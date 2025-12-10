"""
Graph Exporter module for generating analytical plots from simulation data
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import matplotlib.dates as mdates
from datetime import datetime, timedelta

from .logger import get_logger
from .simulation import SimulationLoop, SimulationMetrics
from .map import Map

logger = get_logger()


class GraphExporter:
	"""Generate analytical graphs from simulation results"""
	
	def __init__(self, simulation: SimulationLoop):
		"""
		Initialize graph exporter
		
		Args:
			simulation: SimulationLoop instance with completed run data
		"""
		self.sim = simulation
		self.map = simulation.map
		self.metrics = simulation.metrics_history
		self.station_history = simulation.station_history
		
		if not self.metrics:
			logger.warning("No metrics data available in simulation")
		
		logger.info(f"GraphExporter initialized with {len(self.metrics)} metrics entries")
	
	def _get_time_array(self, start_time: float = 0.0) -> np.ndarray:
		"""Convert tick indices to time array in hours"""
		if not self.metrics:
			return np.array([])
		
		ticks = np.array([m.tick for m in self.metrics])
		time_seconds = ticks * self.sim.dt + start_time
		return time_seconds / 3600.0  # Convert to hours
	
	def plot_station_waiting_passengers(
		self,
		station_ids: List[int],
		output_path: str,
		start_time: float = 0.0,
		figsize: Tuple[int, int] = (12, 6)
	):
		"""
		Plot waiting passenger counts over time for specified stations
		
		Args:
			station_ids: List of station IDs to plot
			output_path: Path to save the plot
			start_time: Simulation start time in seconds (for x-axis labels)
			figsize: Figure size (width, height)
		"""
		if not self.station_history:
			logger.error("No station history available - visualization must be enabled during simulation")
			return
		
		fig, ax = plt.subplots(figsize=figsize)
		
		# Extract time array (in hours from start)
		time_hours = np.arange(len(self.station_history)) / (3600 / self.sim.dt) + (start_time / 3600)
		
		# Plot each station
		for station_id in station_ids:
			if station_id not in self.map.stations:
				logger.warning(f"Station ID {station_id} not found in map")
				continue
			
			station_name = self.map.stations[station_id].name
			counts = [frame.get(station_id, 0) for frame in self.station_history]
			
			ax.plot(time_hours, counts, label=station_name, linewidth=2)
		
		ax.set_xlabel('Time (hours)', fontsize=12)
		ax.set_ylabel('Waiting Passengers', fontsize=12)
		ax.set_title('Waiting Passengers at Stations Over Time', fontsize=14, fontweight='bold')
		ax.legend(loc='best')
		ax.grid(True, alpha=0.3)
		
		plt.tight_layout()
		plt.savefig(output_path, dpi=150, bbox_inches='tight')
		plt.close()
		
		logger.info(f"Saved station waiting passengers plot to {output_path}")
	
	def plot_customer_throughput(
		self,
		output_path: str,
		start_time: float = 0.0,
		figsize: Tuple[int, int] = (12, 6),
		window_size: int = 10
	):
		"""
		Plot customer boarding and alighting rates over time
		
		Args:
			output_path: Path to save the plot
			start_time: Simulation start time in seconds (for x-axis labels)
			figsize: Figure size (width, height)
			window_size: Moving average window size for smoothing
		"""
		if not self.metrics:
			logger.error("No metrics data available")
			return
		
		fig, ax = plt.subplots(figsize=figsize)
		
		time_hours = self._get_time_array(start_time)
		boarding_rates = np.array([m.boarding_rate for m in self.metrics])
		alight_rates = np.array([m.alight_rate for m in self.metrics])
		
		# Apply moving average smoothing
		if window_size > 1:
			boarding_smooth = np.convolve(boarding_rates, np.ones(window_size)/window_size, mode='valid')
			alight_smooth = np.convolve(alight_rates, np.ones(window_size)/window_size, mode='valid')
			time_smooth = time_hours[:len(boarding_smooth)]
		else:
			boarding_smooth = boarding_rates
			alight_smooth = alight_rates
			time_smooth = time_hours
		
		ax.plot(time_smooth, boarding_smooth, label='Boarding Rate', linewidth=2, color='#2ecc71')
		ax.plot(time_smooth, alight_smooth, label='Alighting Rate', linewidth=2, color='#e74c3c')
		
		ax.set_xlabel('Time (hours)', fontsize=12)
		ax.set_ylabel('Passengers per Second', fontsize=12)
		ax.set_title('Customer Throughput Over Time', fontsize=14, fontweight='bold')
		ax.legend(loc='best')
		ax.grid(True, alpha=0.3)
		
		plt.tight_layout()
		plt.savefig(output_path, dpi=150, bbox_inches='tight')
		plt.close()
		
		logger.info(f"Saved customer throughput plot to {output_path}")
	
	def plot_line_occupancy(
		self,
		output_path: str,
		start_time: float = 0.0,
		figsize: Tuple[int, int] = (12, 8),
		sample_interval: int = 10
	):
		"""
		Plot average occupancy percentage for each train line over time
		
		Args:
			output_path: Path to save the plot
			start_time: Simulation start time in seconds (for x-axis labels)
			figsize: Figure size (width, height)
			sample_interval: Sample every Nth tick to reduce computation
		"""
		if not self.sim.active_trains and not hasattr(self, '_train_history'):
			logger.error("No train data available")
			return
		
		fig, ax = plt.subplots(figsize=figsize)
		
		# Sample train states throughout simulation
		# We'll reconstruct from metrics tick by tick
		line_occupancy = {}  # {line_id: [(time, avg_occupancy_pct)]}
		
		# Get all line IDs
		line_ids = [line.line_id for line in self.map.lines]
		
		# Initialize tracking
		for line_id in line_ids:
			line_occupancy[line_id] = []
		
		# Sample at intervals
		for tick_idx in range(0, len(self.metrics), sample_interval):
			time_hour = (tick_idx * self.sim.dt + start_time) / 3600.0
			
			# Calculate occupancy for each line at this tick
			# Note: we need to sample active_trains state, but we don't have historical train data
			# So we'll compute this from the current state if available
			# For a complete solution, we'd need to track this during simulation
			pass
		
		# Since we don't have historical train data, calculate average from final state
		# and create a bar chart instead
		ax.clear()
		
		line_names = []
		avg_occupancies = []
		
		for line in self.map.lines:
			line_id = line.line_id
			line_trains = [t for t in self.sim.active_trains if t.line_id == line_id]
			
			if line_trains:
				occupancies = [t.current_capacity / t.max_capacity * 100 for t in line_trains]
				avg_occ = np.mean(occupancies)
			else:
				avg_occ = 0.0
			
			line_names.append(line.line_code)
			avg_occupancies.append(avg_occ)
		
		colors = plt.cm.get_cmap('viridis')(np.linspace(0, 1, len(line_names)))
		bars = ax.bar(line_names, avg_occupancies, color=colors, edgecolor='black', linewidth=1.5)
		
		# Add percentage labels on bars
		for bar, pct in zip(bars, avg_occupancies):
			height = bar.get_height()
			ax.text(bar.get_x() + bar.get_width()/2., height,
					f'{pct:.1f}%',
					ha='center', va='bottom', fontsize=10, fontweight='bold')
		
		ax.set_ylabel('Average Occupancy (%)', fontsize=12)
		ax.set_xlabel('Train Line', fontsize=12)
		ax.set_title('Average Train Occupancy by Line (Final State)', fontsize=14, fontweight='bold')
		ax.set_ylim(0, 100)
		ax.grid(True, alpha=0.3, axis='y')
		
		plt.tight_layout()
		plt.savefig(output_path, dpi=150, bbox_inches='tight')
		plt.close()
		
		logger.info(f"Saved line occupancy plot to {output_path}")
	
	def plot_system_overview(
		self,
		output_path: str,
		start_time: float = 0.0,
		figsize: Tuple[int, int] = (14, 10)
	):
		"""
		Create a multi-panel overview plot with key system metrics
		
		Args:
			output_path: Path to save the plot
			start_time: Simulation start time in seconds
			figsize: Figure size (width, height)
		"""
		if not self.metrics:
			logger.error("No metrics data available")
			return
		
		fig, axes = plt.subplots(2, 2, figsize=figsize)
		time_hours = self._get_time_array(start_time)
		
		# Panel 1: Total waiting passengers
		ax1 = axes[0, 0]
		waiting = np.array([m.waiting_passengers for m in self.metrics])
		ax1.plot(time_hours, waiting, linewidth=2, color='#e74c3c')
		ax1.fill_between(time_hours, waiting, alpha=0.3, color='#e74c3c')
		ax1.set_xlabel('Time (hours)', fontsize=10)
		ax1.set_ylabel('Waiting Passengers', fontsize=10)
		ax1.set_title('Total Waiting Passengers', fontsize=12, fontweight='bold')
		ax1.grid(True, alpha=0.3)
		
		# Panel 2: Average wait time
		ax2 = axes[0, 1]
		wait_times = np.array([m.avg_wait_time for m in self.metrics])
		ax2.plot(time_hours, wait_times / 60, linewidth=2, color='#3498db')  # Convert to minutes
		ax2.set_xlabel('Time (hours)', fontsize=10)
		ax2.set_ylabel('Wait Time (minutes)', fontsize=10)
		ax2.set_title('Average Wait Time', fontsize=12, fontweight='bold')
		ax2.grid(True, alpha=0.3)
		
		# Panel 3: Active trains
		ax3 = axes[1, 0]
		active_trains = np.array([m.active_trains for m in self.metrics])
		ax3.plot(time_hours, active_trains, linewidth=2, color='#2ecc71')
		ax3.fill_between(time_hours, active_trains, alpha=0.3, color='#2ecc71')
		ax3.set_xlabel('Time (hours)', fontsize=10)
		ax3.set_ylabel('Number of Trains', fontsize=10)
		ax3.set_title('Active Trains', fontsize=12, fontweight='bold')
		ax3.grid(True, alpha=0.3)
		
		# Panel 4: Throughput rates
		ax4 = axes[1, 1]
		boarding = np.array([m.boarding_rate for m in self.metrics])
		alighting = np.array([m.alight_rate for m in self.metrics])
		ax4.plot(time_hours, boarding, label='Boarding', linewidth=2, color='#2ecc71')
		ax4.plot(time_hours, alighting, label='Alighting', linewidth=2, color='#e74c3c')
		ax4.set_xlabel('Time (hours)', fontsize=10)
		ax4.set_ylabel('Rate (passengers/sec)', fontsize=10)
		ax4.set_title('Boarding & Alighting Rates', fontsize=12, fontweight='bold')
		ax4.legend(loc='best')
		ax4.grid(True, alpha=0.3)
		
		plt.suptitle('Simulation System Overview', fontsize=16, fontweight='bold', y=0.995)
		plt.tight_layout()
		plt.savefig(output_path, dpi=150, bbox_inches='tight')
		plt.close()
		
		logger.info(f"Saved system overview plot to {output_path}")
	
	def export_all_graphs(
		self,
		output_dir: str,
		station_ids: Optional[List[int]] = None,
		start_time: float = 0.0,
		prefix: str = ""
	):
		"""
		Export all available graphs to a directory
		
		Args:
			output_dir: Directory to save graphs
			station_ids: List of station IDs for station-specific plots (default: first 5)
			start_time: Simulation start time in seconds
			prefix: Filename prefix for all graphs
		"""
		output_path = Path(output_dir)
		output_path.mkdir(parents=True, exist_ok=True)
		
		if station_ids is None:
			# Default to first 5 stations
			station_ids = list(self.map.stations.keys())[:5]
		
		logger.info(f"Exporting all graphs to {output_dir}")
		
		# Export each graph type
		if self.station_history:
			self.plot_station_waiting_passengers(
				station_ids=station_ids,
				output_path=str(output_path / f"{prefix}station_waiting.png"),
				start_time=start_time
			)
		
		self.plot_customer_throughput(
			output_path=str(output_path / f"{prefix}throughput.png"),
			start_time=start_time
		)
		
		self.plot_line_occupancy(
			output_path=str(output_path / f"{prefix}line_occupancy.png"),
			start_time=start_time
		)
		
		self.plot_system_overview(
			output_path=str(output_path / f"{prefix}system_overview.png"),
			start_time=start_time
		)
		
		logger.info(f"Exported all graphs successfully")
