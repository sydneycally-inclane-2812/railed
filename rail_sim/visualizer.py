"""
Visualizer module for generating MP4 videos of simulation playback
Shows real-time passenger counts at each station
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from typing import Dict, List, Tuple, Optional
import subprocess
import shutil
from pathlib import Path

from .logger import get_logger
from .map import Map

logger = get_logger()


class Visualizer:
	"""Generate MP4 videos from simulation station history"""
	
	def __init__(
		self,
		map_network: Map,
		resolution: Tuple[int, int] = (1920, 1080),
		fps: int = 60,
		dpi: int = 100
	):
		"""
		Initialize visualizer
		
		Args:
			map_network: Map object containing stations and network graph
			resolution: Video resolution (width, height) in pixels
			fps: Video output framerate - must match simulation capture_rate or be lower (will interpolate/duplicate frames)
			dpi: Dots per inch for matplotlib rendering
		"""
		self.map = map_network
		self.resolution = resolution
		self.fps = fps
		self.dpi = dpi
		
		# Validate inputs
		if resolution[0] < 640 or resolution[1] < 480:
			raise ValueError("Resolution must be at least 640x480")
		if resolution[0] > 3840 or resolution[1] > 2160:
			raise ValueError("Resolution cannot exceed 4K (3840x2160)")
		if fps < 1:
			raise ValueError("FPS must be at least 1")
		
		# Check ffmpeg availability
		self._check_ffmpeg()
		
		# Pre-compute station positions using network layout
		self._compute_station_positions()
		
		logger.info(f"Visualizer initialized: {resolution[0]}x{resolution[1]} @ {fps}fps")
	
	def _check_ffmpeg(self):
		"""Check if ffmpeg is available"""
		if not shutil.which('ffmpeg'):
			logger.warning(
				"ffmpeg not found in PATH. Video export may fail. "
				"Install ffmpeg: https://ffmpeg.org/download.html"
			)
	
	def _compute_station_positions(self):
		"""Compute 2D positions for all stations using graph layout"""
		import networkx as nx
		
		G = self.map.graph
		
		if len(G.nodes()) == 0:
			logger.warning("No stations in network graph")
			self.station_positions = {}
			return
		
		try:
			# Use spring layout with multiple iterations for good spacing
			self.station_positions = nx.spring_layout(
				G, 
				k=0.5, 
				iterations=200, 
				seed=42
			)
			logger.info(f"Computed positions for {len(self.station_positions)} stations")
		except Exception as e:
			logger.error(f"Failed to compute station positions: {e}")
			self.station_positions = {}
	
	def _get_passenger_color(self, count: int, max_count: int) -> str:
		"""
		Get color for station based on passenger count
		Green (few) -> Yellow (moderate) -> Red (crowded)
		"""
		if max_count == 0:
			return '#00ff00'
		
		ratio = min(count / max_count, 1.0)
		
		if ratio < 0.3:
			# Green to yellow
			r = int(255 * (ratio / 0.3))
			g = 255
			b = 0
		elif ratio < 0.7:
			# Yellow to orange
			r = 255
			g = int(255 * (1 - (ratio - 0.3) / 0.4))
			b = 0
		else:
			# Orange to red
			r = 255
			g = int(128 * (1 - (ratio - 0.7) / 0.3))
			b = 0
		
		return f'#{r:02x}{g:02x}{b:02x}'
	
	def _get_station_size(self, count: int, max_count: int) -> float:
		"""Get circle size for station based on passenger count"""
		min_size = 100
		max_size = 2000
		
		if max_count == 0:
			return min_size
		
		ratio = min(count / max_count, 1.0)
		# Use sqrt for better visual scaling
		return min_size + (max_size - min_size) * np.sqrt(ratio)
	
	def render_video(
		self,
		station_history: List[Dict[int, int]],
		output_path: str,
		capture_rate: float = 30.0,
		title: str = "Rail Network Simulation"
	):
		"""
		Render video from station history
		
		Args:
			station_history: List of dicts mapping station_id -> passenger_count (already captured at desired rate)
			output_path: Path to save MP4 file
			capture_rate: Rate at which snapshots were captured (snapshots per second)
			title: Video title displayed on screen
		"""
		if not station_history:
			raise ValueError("No station history data to render")
		
		if not self.station_positions:
			raise ValueError("No station positions computed - cannot render")
		
		logger.info(f"Rendering video with {len(station_history)} frames at {self.fps} fps")
		logger.info(f"Capture rate: {capture_rate} snapshots/sec, Video duration: {len(station_history)/capture_rate:.2f}s")
		
		# Find max passenger count for scaling
		max_passengers = 0
		for tick_data in station_history:
			max_passengers = max(max_passengers, max(tick_data.values(), default=0))
		
		if max_passengers == 0:
			logger.warning("No passengers in simulation history")
			max_passengers = 1
		
		# Set up figure
		figsize = (self.resolution[0] / self.dpi, self.resolution[1] / self.dpi)
		fig, ax = plt.subplots(figsize=figsize, dpi=self.dpi)
		
		# Initial setup
		ax.set_aspect('equal')
		ax.axis('off')
		ax.set_xlim(-1.2, 1.2)
		ax.set_ylim(-1.2, 1.2)
		
		# Draw network edges (lines) - static
		for u, v, data in self.map.graph.edges(data=True):
			if u in self.station_positions and v in self.station_positions:
				pos_u = self.station_positions[u]
				pos_v = self.station_positions[v]
				ax.plot(
					[pos_u[0], pos_v[0]], 
					[pos_u[1], pos_v[1]], 
					color='#cccccc', 
					linewidth=1, 
					alpha=0.5,
					zorder=1
				)
		
		# Store capture rate for time calculations
		self.current_capture_rate = capture_rate
		
		# Store capture rate for time calculations
		self.current_capture_rate = capture_rate
		
		# Title and info text
		title_text = ax.text(
			0.5, 0.98, title,
			transform=ax.transAxes,
			ha='center', va='top',
			fontsize=20, fontweight='bold'
		)
		
		time_text = ax.text(
			0.02, 0.98, '',
			transform=ax.transAxes,
			ha='left', va='top',
			fontsize=14,
			family='monospace'
		)
		
		stats_text = ax.text(
			0.02, 0.02, '',
			transform=ax.transAxes,
			ha='left', va='bottom',
			fontsize=12,
			family='monospace'
		)
		
		# Legend
		legend_y = 0.92
		ax.text(
			0.98, legend_y, 'Passenger Count:',
			transform=ax.transAxes,
			ha='right', va='top',
			fontsize=10, fontweight='bold'
		)
		
		# Legend color samples
		for i, (label, ratio) in enumerate([
			('Low', 0.1),
			('Medium', 0.5),
			('High', 0.9)
		]):
			color = self._get_passenger_color(int(ratio * max_passengers), max_passengers)
			y_pos = legend_y - 0.03 * (i + 1)
			
			# Color box
			ax.add_patch(plt.Rectangle(
				(0.96, y_pos - 0.008),
				0.015, 0.015,
				transform=ax.transAxes,
				facecolor=color,
				edgecolor='black',
				linewidth=0.5
			))
			
			ax.text(
				0.95, y_pos,
				label,
				transform=ax.transAxes,
				ha='right', va='center',
				fontsize=9
			)
		
		# Prepare station circles (will be updated each frame)
		station_circles = {}
		station_labels = {}
		
		for station_id, pos in self.station_positions.items():
			if station_id not in self.map.stations:
				continue
			
			# Create circle
			circle = Circle(
				pos, 0.02,
				facecolor='#00ff00',
				edgecolor='black',
				linewidth=1,
				zorder=3
			)
			ax.add_patch(circle)
			station_circles[station_id] = circle
			
			# Create label
			station_name = self.map.stations[station_id].name
			label = ax.text(
				pos[0], pos[1] - 0.05,
				f'{station_name}\n0',
				ha='center', va='top',
				fontsize=8,
				zorder=4
			)
			station_labels[station_id] = label
		
		def update_frame(frame_idx):
			"""Update function for animation"""
			if frame_idx >= len(station_history):
				return []
			
			tick_data = station_history[frame_idx]
			sim_time = frame_idx / self.current_capture_rate
			
			# Update time display
			hours = int(sim_time // 3600)
			minutes = int((sim_time % 3600) // 60)
			seconds = int(sim_time % 60)
			time_text.set_text(f'Time: {hours:02d}:{minutes:02d}:{seconds:02d}')
			
			# Calculate total passengers
			total_passengers = sum(tick_data.values())
			stats_text.set_text(
				f'Frame: {frame_idx}\n'
				f'Total Waiting: {total_passengers:,}\n'
				f'Max at Station: {max(tick_data.values(), default=0):,}'
			)
			
			# Update each station
			for station_id in station_circles:
				count = tick_data.get(station_id, 0)
				
				# Update circle size and color
				circle = station_circles[station_id]
				size = self._get_station_size(count, max_passengers)
				# Convert size to radius in data coordinates
				radius = 0.01 + 0.08 * (size / 2000)
				circle.set_radius(radius)
				
				color = self._get_passenger_color(count, max_passengers)
				circle.set_facecolor(color)
				
				# Update label
				station_name = self.map.stations[station_id].name
				station_labels[station_id].set_text(f'{station_name}\n{count:,}')
			
			return list(station_circles.values()) + list(station_labels.values()) + [time_text, stats_text]
		
		# Create animation
		logger.info("Creating animation...")
		anim = animation.FuncAnimation(
			fig,
			update_frame,
			frames=len(station_history),
			interval=1000/self.fps,
			blit=False,  # Set to False for better compatibility
			repeat=False
		)
		
		# Save to file
		output_path = Path(output_path)
		output_path.parent.mkdir(parents=True, exist_ok=True)
		
		logger.info(f"Saving video to {output_path}...")
		try:
			Writer = animation.writers['ffmpeg']
			writer = Writer(
				fps=self.fps,
				metadata=dict(artist='RailSim'),
				bitrate=5000,
				codec='libx264'
			)
			anim.save(str(output_path), writer=writer, dpi=self.dpi)
			logger.info(f"Video saved successfully: {output_path}")
		except Exception as e:
			logger.error(f"Failed to save video: {e}")
			raise
		finally:
			plt.close(fig)
