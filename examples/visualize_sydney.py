"""
Example: Sydney network simulation with MP4 visualization export
"""

import sys
import numpy as np
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rail_sim import (
    MemmapAllocator,
    MemoryAllocator,
    CustomerGenerator,
    Map,
    SimulationLoop,
    Visualizer,
    GraphExporter,
    precalculate
)

def constant_arrival_rate(t):
    """Constant arrival rate function"""
    return 2.0  # 2 customers per second

@precalculate(method="staircase", resolution=2000)
def peaky_high_demand_arrival_rate(t):
    scale = 5
    morn_aft_scale = 4
    min = 2
    
    power = -1/morn_aft_scale
    f = lambda x: scale * x ** power * np.abs(np.sin(x)) + min
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 

@precalculate(method="staircase", resolution=2000)
def peaky_low_demand_arrival_rate(t):
    scale = 2
    morn_aft_scale = 4
    min = 1
    
    power = -1/morn_aft_scale
    f = lambda x: scale * x ** power * np.abs(np.sin(x)) + min
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 

def main():
    print("=== Sydney Network Simulation with Visualization ===\n")
    
    # 1. Create allocator and network
    allocator = MemoryAllocator()
    network = Map()
    
    # 2. Import Sydney network structure
    from sydney_train import SydneyNetwork
    sydney = SydneyNetwork()

    # Add all stations and lines
    for station in sydney.stations:
        network.add_station(station)
    for line in sydney.lines:
        network.add_line(line)
    
    print(f"Network loaded: {len(network.stations)} stations, {len(network.lines)} lines\n")
    
    # 3. Create customer generators for multiple stations
    generators = []
    
    # High demand stations (first 5)
    high_demand_station_ids = [1, 2, 3, 4, 5]
    for idx, station_id in enumerate(high_demand_station_ids):
        gen = CustomerGenerator(
            allocator=allocator,
            station_id=station_id,
            arrival_rate_profile=peaky_high_demand_arrival_rate,
            seed=42 + idx
        )
        generators.append(gen)
    
    # Low demand stations (remaining stations)
    low_demand_station_ids = list(range(6, len(network.stations) + 1))
    for idx, station_id in enumerate(low_demand_station_ids):
        gen = CustomerGenerator(
            allocator=allocator,
            station_id=station_id,
            arrival_rate_profile=peaky_low_demand_arrival_rate,
            seed=100 + idx
        )
        generators.append(gen)
    
    print(f"Created {len(high_demand_station_ids)} high-demand and {len(low_demand_station_ids)} low-demand generators\n")
    
    # 4. Create simulation
    sim = SimulationLoop(
        memmap_allocator=allocator,
        map_network=network,
        dt=1.0,  # 1 second per tick
        snapshot_interval=7200,  # snapshot every 2 hours
        log_level=logging.ERROR
    )
    
    # Set start time to 6 AM
    sim.current_time = 6 * 3600.0
    # Add generators
    for gen in generators:
        sim.add_customer_generator(gen)
    
    # 5. Enable visualization BEFORE running simulation
    capture_rate = 30  # Capture 30 snapshots per second
    print(f"Enabling visualization with capture rate: {capture_rate} snapshots/sec...")
    sim.enable_visualization(capture_rate=capture_rate)
    print(f"Visualization enabled - capturing {capture_rate} snapshots per second\n")
    
    # 6. Run simulation
    n_ticks = 3600*12  # Run for 1 hour (3600 seconds)
    print(f"Running simulation for {n_ticks} ticks ({n_ticks/3600:.1f} hours)...")
    sim.run(n_ticks=n_ticks)
    
    print(f"\nSimulation complete!")
    print(f"Final metrics: {sim.metrics_history[-1]}")
    print(f"Captured {len(sim.station_history)} station state snapshots\n")
    
    # 7. Create visualization
    if len(sim.station_history) == 0:
        print("ERROR: No station history captured. Cannot generate visualization.")
        return
    
    print("Creating visualizer...")
    video_fps = 60  # 60 fps video output
    visualizer = Visualizer(
        map_network=network,
        fps=video_fps,
        resolution=(1920, 1080)  # Full HD
    )
    
    # 8. Render video
    output_path = Path(__file__).parent / "video.mp4"
    print(f"Rendering video to {output_path} at {video_fps} fps...")
    print("This may take a few minutes depending on the number of frames...\n")
    
    visualizer.render_video(
        station_history=sim.station_history,
        output_path=str(output_path),
        dt=sim.dt,  # Simulation timestep
        sim_start_time=6 * 3600.0  # Start at 6 AM
    )
    
    print(f"\n✅ Video saved to: {output_path}")
    print(f"   Duration: {len(sim.station_history) / capture_rate:.2f} seconds")
    print(f"   Frame rate: {video_fps} fps")
    print(f"   Resolution: 1920x1080")
    
    # 9. Export analytical graphs
    print("\n=== Exporting Analytical Graphs ===")
    graph_exporter = GraphExporter(sim)
    graphs_dir = Path(__file__).parent / "graphs"
    
    # Export all graphs with high-demand stations highlighted
    graph_exporter.export_all_graphs(
        output_dir=str(graphs_dir),
        station_ids=high_demand_station_ids,  # Show the 5 high-demand stations
        start_time=6 * 3600.0,
        prefix="sydney_"
    )
    

if __name__ == "__main__":
    main()
