# Railed - Rail Transport Simulation Framework

A high-performance railway simulation framework for modeling urban transit networks with realistic passenger flows, train operations, and network visualization.

## Features

- 🚄 **Realistic Train Operations**: Dynamic fleet management with bidirectional lines, capacity constraints, and automatic turnarounds
- 👥 **Customer Simulation**: Poisson arrival processes with time-varying demand profiles and multi-leg journey planning
- 🗺️ **Network Routing**: Dijkstra-based pathfinding with automatic transfer handling and path deduplication
- 📊 **Analytics**: Real-time metrics collection with Parquet export for post-simulation analysis
- 🎬 **Visualization**: Export MP4 videos showing network state evolution over time
- ⚡ **High Performance**: Columnar storage using NumPy arrays for efficient large-scale simulations

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start: Sydney Network Simulation

Here's a complete example simulating the Sydney train network with realistic demand patterns and video visualization:

```python
import sys
import numpy as np
import logging
from pathlib import Path

from rail_sim import (
    MemoryAllocator,
    CustomerGenerator,
    Map,
    SimulationLoop,
    Visualizer,
    GraphExporter,
    precalculate
)

# Define time-varying arrival rate with morning/evening peaks
@precalculate(method="staircase", resolution=2000)
def peaky_high_demand_arrival_rate(t):
    """Rush hour demand pattern for busy stations"""
    scale = 5
    morn_aft_scale = 4
    min_rate = 2
    
    power = -1/morn_aft_scale
    f = lambda x: scale * x ** power * np.abs(np.sin(x)) + min_rate
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2)  # 2 peaks per day

def main():
    # 1. Create memory allocator for customer data
    allocator = MemoryAllocator()
    
    # 2. Build network topology
    network = Map()
    
    # Import Sydney network structure (stations and lines)
    from sydney_train import SydneyNetwork
    sydney = SydneyNetwork()
    
    for station in sydney.stations:
        network.add_station(station)
    for line in sydney.lines:
        network.add_line(line)
    
    print(f"Network loaded: {len(network.stations)} stations, {len(network.lines)} lines")
    
    # 3. Create customer generators for high-demand stations
    generators = []
    high_demand_stations = [1, 2, 3, 4, 5]  # Central, Town Hall, Wynyard, etc.
    
    for idx, station_id in enumerate(high_demand_stations):
        gen = CustomerGenerator(
            allocator=allocator,
            station_id=station_id,
            arrival_rate_profile=peaky_high_demand_arrival_rate,
            seed=42 + idx
        )
        generators.append(gen)
    
    # 4. Create simulation starting at 6 AM
    sim = SimulationLoop(
        memmap_allocator=allocator,
        map_network=network,
        dt=1.0,  # 1 second per tick
        snapshot_interval=7200,  # snapshot every 2 hours
        log_level=logging.ERROR
    )
    
    sim.current_time = 6 * 3600.0  # Start at 6 AM
    
    for gen in generators:
        sim.add_customer_generator(gen)
    
    # 5. Enable visualization (captures 30 snapshots per second)
    sim.enable_visualization(capture_rate=30)
    
    # 6. Run simulation for 12 hours
    n_ticks = 3600 * 12
    print(f"Running simulation for {n_ticks/3600:.1f} hours...")
    sim.run(n_ticks=n_ticks)
    
    print(f"Simulation complete! Captured {len(sim.station_history)} snapshots")
    
    # 7. Render MP4 video
    visualizer = Visualizer(
        map_network=network,
        fps=60,
        resolution=(1920, 1080)
    )
    
    visualizer.render_video(
        station_history=sim.station_history,
        output_path="video.mp4",
        dt=sim.dt,
        sim_start_time=6 * 3600.0
    )
    
    print("✅ Video saved to: video.mp4")
    
    # 8. Export analytical graphs
    graph_exporter = GraphExporter(sim)
    graph_exporter.export_all_graphs(
        output_dir="graphs/",
        station_ids=high_demand_stations,
        start_time=6 * 3600.0,
        prefix="sydney_"
    )

if __name__ == "__main__":
    main()
```

**Run the example:**

```bash
cd examples
python visualize_sydney.py
```

This will generate:
- `video.mp4` - Animated visualization of the network over 12 simulated hours
- `graphs/` - Statistical plots (wait times, occupancy, boarding rates, etc.)
- Parquet snapshots for detailed analysis

## Core Concepts

### Customer Data Storage

Customers are stored in efficient columnar format (NumPy array or memmap) with 13 fields per record:

```python
CUSTOMER_DTYPE = np.dtype([
    ('id', 'u8'),                    # Unique customer ID
    ('origin_station_id', 'i4'),     # Starting station
    ('dest_station_id', 'i4'),       # Destination station
    ('current_station_id', 'i4'),    # Current location
    ('on_train_id', 'i4'),           # Train ID (if onboard)
    ('state', 'u1'),                 # 0=waiting, 1=onboard, 2=arrived, 3=transfer
    ('tap_on_ts', 'f8'),             # Board time
    ('tap_off_ts', 'f8'),            # Alight time
    ('spawn_ts', 'f8'),              # Arrival at origin time
    ('path_id', 'i4'),               # Route identifier
    ('total_wait_time', 'f8'),       # Cumulative wait time
    ('total_travel_time', 'f8'),     # Cumulative travel time
    ('movement_speed', 'f4')         # Movement speed
])
```

### Network Architecture

- **Map**: Network graph with stations and lines, handles pathfinding
- **Station**: Waiting queues, passenger boarding/alighting logic, transfer management
- **Line**: Route topology, travel times, owns TrainGenerator
- **Train**: Movement, capacity, passenger management
- **PathTable**: Caches computed routes to avoid redundant pathfinding

### Simulation Flow

Each simulation tick:

1. **Customer Generation**: Spawn new passengers based on arrival rate profiles
2. **Path Assignment**: Compute shortest paths and assign to customers
3. **Train Spawning**: Generate trains based on schedule and headway
4. **Train Movement**: Update train positions, handle arrivals at stations
5. **Boarding/Alighting**: Transfer passengers between stations and trains
6. **Metrics Collection**: Track wait times, occupancy, throughput
7. **Snapshot**: Periodic export to Parquet for analysis

## Architecture

### Data Layer
- **MemoryAllocator / MemmapAllocator**: Manages customer record storage with index pooling
- **PathTable**: Deduplicates and caches routing paths using MD5 hashing

### Entity Layer
- **CustomerGenerator**: Poisson arrival process with configurable rate profiles
- **Train**: In-memory object with timetable, capacity, onboard passenger list
- **TrainGenerator**: Fleet manager handling train lifecycle (spawn, turnaround, pooling)
- **Station**: Queue management, boarding eligibility filtering

### Orchestration
- **SimulationLoop**: Main coordinator executing the simulation tick by tick
- **Visualizer**: Renders MP4 videos from captured station state history
- **GraphExporter**: Exports matplotlib charts for post-simulation analysis

## Project Structure

```
rail_sim/
├── memory.py           # Customer data storage (memmap/in-memory)
├── path_table.py       # Path caching and deduplication
├── customer_gen.py     # Passenger arrival simulation
├── arrival_rate_profile.py  # Demand profile functions
├── train.py            # Train movement and operations
├── station.py          # Station queues and boarding logic
├── train_gen.py        # Train spawning and fleet management
├── line.py             # Line topology and schedules
├── map.py              # Network graph and routing
├── simulation.py       # Main simulation loop
├── visualizer.py       # MP4 video rendering
├── graph_exporter.py   # Statistical plot generation
└── stats_utils.py      # Analytics utilities

examples/
├── visualize_sydney.py    # Full Sydney network example
├── sydney_train.py        # Sydney network definition
├── simple_simulation_v2.py # Basic examples
└── graphs/                # Output directory for plots

research/
└── research.md            # Design documentation
```

## Advanced Features

### Time-Varying Demand Profiles

Use the `@precalculate` decorator to optimize complex arrival rate functions:

```python
from rail_sim import precalculate
import numpy as np

@precalculate(method="staircase", resolution=2000)
def rush_hour_profile(t):
    """Morning and evening peaks"""
    time_of_day = (t % 86400) / 86400  # Normalize to [0, 1]
    hour = time_of_day * 24
    
    if 7 <= hour < 9 or 17 <= hour < 19:
        return 5.0  # Peak rate
    elif 9 <= hour < 17:
        return 2.0  # Mid-day
    else:
        return 0.5  # Off-peak
```

### Custom Network Definitions

Build networks programmatically:

```python
from rail_sim import Station, Line

# Define stations
stations = [
    Station(station_id=1, name="Central", line_codes=["T1", "T2"]),
    Station(station_id=2, name="Town Hall", line_codes=["T1"]),
    Station(station_id=3, name="Wynyard", line_codes=["T1", "T2"])
]

# Define line with bidirectional service
line = Line(
    line_id="T1",
    line_code="T1",
    station_list=[1, 2, 3],
    time_between_stations=[120.0, 180.0],  # seconds
    schedule={
        'headway': 300,  # 5 minutes between trains
        'service_start': 5 * 3600,  # 5 AM
        'service_end': 23 * 3600,  # 11 PM
        'capacity': 800
    },
    fleet_size=10,
    bidirectional=True
)
```

### Metrics and Analysis

Access real-time metrics during simulation:

```python
sim.run(n_ticks=3600)

# Get latest metrics
metrics = sim.metrics_history[-1]
print(f"Active passengers: {metrics.active_customers}")
print(f"Boarding rate: {metrics.boarding_count / sim.dt:.2f}/sec")
print(f"Avg wait time: {metrics.avg_waiting_time:.1f}s")
print(f"Train utilization: {metrics.avg_train_occupancy:.1%}")

# Export all snapshots to Parquet
import pyarrow.parquet as pq
for i, snapshot in enumerate(sim.snapshots):
    pq.write_table(snapshot, f"snapshot_{i}.parquet")
```

### Visualization Options

Customize video output:

```python
from rail_sim import Visualizer

visualizer = Visualizer(
    map_network=network,
    fps=60,  # Video frame rate
    resolution=(1920, 1080),  # Full HD
    show_station_names=True,
    show_line_colors=True,
    show_train_ids=False
)

visualizer.render_video(
    station_history=sim.station_history,
    output_path="simulation.mp4",
    dt=sim.dt,
    sim_start_time=6 * 3600.0,
    playback_speed=60  # 60x real-time
)
```

### Statistical Graphs

Export comprehensive analytics:

```python
from rail_sim import GraphExporter

exporter = GraphExporter(sim)

# Export all standard graphs
exporter.export_all_graphs(
    output_dir="analysis/",
    station_ids=[1, 2, 3],  # Highlight specific stations
    start_time=6 * 3600.0,
    prefix="morning_rush_"
)

# Or export individual graphs
exporter.export_wait_time_graph("wait_times.png", station_ids=[1, 2])
exporter.export_occupancy_graph("occupancy.png")
exporter.export_customer_state_graph("states.png")
```

## Performance Considerations

- **MemoryAllocator vs MemmapAllocator**: Use `MemoryAllocator` for faster in-memory simulations (up to 2x faster), `MemmapAllocator` for large simulations requiring disk persistence
- **Visualization capture rate**: Lower capture rates (10-30 fps) reduce memory usage during simulation
- **Snapshot interval**: Adjust based on analytics needs vs storage constraints
- **Path table**: Automatically caches routes to avoid redundant pathfinding

## Output Files

**During Simulation:**
- `snapshots/snapshot_*.parquet` - Periodic customer state exports
- `pipeline_log.txt` - Simulation log (if logging enabled)

**After Visualization:**
- `video.mp4` - Animated network visualization
- `graphs/*.png` - Statistical plots (wait times, occupancy, boarding rates, etc.)

## API Reference

See [rail_sim/README.md](rail_sim/README.md) for detailed class diagrams and API documentation.

## Examples

Browse the `examples/` directory for more use cases:
- `simple_simulation_v2.py` - Minimal example with 3 stations
- `sydney_simulation_v3.py` - Large-scale network simulation
- `profile_sim.py` - Performance profiling
- `validating_precalc.py` - Arrival rate function testing

## Development

See `research/research.md` for architectural decisions and design rationale.

## License

MIT

