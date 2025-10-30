# Railed - Rail Transport Simulation Framework

A high-performance railway simulation framework using columnar customer data storage and object-oriented simulation entities.

## Architecture

- **Customer Data**: Stored in NumPy memmap for high-throughput vectorized operations
- **Simulation Objects**: In-memory OOP entities (Trains, Stations, Lines) for behavior and logic
- **Snapshots**: PyArrow/Parquet for analytics and persistence

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from rail_sim import (
    MemmapAllocator,
    CustomerGenerator,
    Station,
    Line,
    Map,
    SimulationLoop
)

# Create memmap for customer data
allocator = MemmapAllocator('data/passengers.dat', initial_capacity=100_000)

# Build network
network = Map()
station = Station(station_id=1, name="Central", line_codes=["T1"])
network.add_station(station)

# Create line with schedule
line = Line(
    line_id="T1",
    line_code="T1",
    station_list=[1, 2, 3],
    time_between_stations=[120.0, 180.0],
    schedule={'headway': 600, 'capacity': 800},
    fleet_size=5
)
network.add_line(line)

# Run simulation
sim = SimulationLoop(allocator, network)
sim.run(n_ticks=1000)
```

## Project Structure

```
src/rail_sim/
├── memmap_schema.py    # Customer data structure and allocator
├── path_table.py       # Path storage and routing
├── customer_gen.py     # Customer generation
├── train.py            # Train movement and operations
├── station.py          # Station queues and boarding
├── train_gen.py        # Train spawning and fleet management
├── line.py             # Line topology and schedules
├── map.py              # Network graph and routing
└── simulation.py       # Main simulation loop

examples/
└── simple_simulation.py  # Basic example

research/
└── research.md          # Design documentation
```

## Data Model

### Customer (memmap columns)
- id, origin_station_id, dest_station_id, current_station_id
- on_train_id, state (waiting/onboard/arrived/transferring)
- tap_on_ts, tap_off_ts, spawn_ts
- path_id (reference to PathTable)
- total_wait_time, total_travel_time, movement_speed

### Simulation Objects
- **Train**: Movement, boarding, alighting, capacity
- **Station**: Queues, platforms, transfers
- **Line**: Topology, schedules, fleet management
- **Map**: Network graph, routing

## Features

- ✅ Columnar customer storage with vectorized operations
- ✅ Capacity-constrained boarding
- ✅ Path-based routing with NetworkX
- ✅ Fleet size management and train pooling
- ✅ Direction reversal at terminals
- ✅ PyArrow snapshot export for analytics
- ✅ Per-tick metrics collection
- ✅ Event-driven architecture ready

## Performance

- Handles 100k+ customers with minimal overhead
- Vectorized state updates for waiting/boarding/alighting
- Zero-copy memmap for cross-process access
- Efficient path caching

## Development

See `research/research.md` for detailed architecture and design decisions.

## License

MIT - Rail System Simulator for Python

A Python package for simulating passenger rail systems. Define lines, schedules, and demand—the simulator handles the rest.

## Philosophy

**You define:** Train lines, train schedules, passenger demand  
**Simulator handles:** Stations, network graph, passenger objects, metrics, visualization

## Features

- Node-based rail network built automatically from line definitions
- Time-stepped passenger movement simulation
- Identify bottlenecks, crowding, and service gaps
- Export metrics and generate visualizations

## User-Defined Inputs

### 1. Train Lines

Define routes with stations and travel times:

```python
Line(
    name="T1",
    stops=["Central", "Redfern", "Town Hall", "Wynyard"],
    travel_times=[3, 2, 4]  # minutes between consecutive stops
)
```

### 2. Train Schedules

Define when trains run on each line:

```python
TrainSchedule(
    line="T1",
    frequency=10,  # train every 10 minutes
    capacity=200,  # passengers per train
    start_time=0,  # simulation start
    end_time=120   # stop generating trains after 120 min
)

# OR specify exact departure times
TrainSchedule(
    line="T1",
    departures=[0, 8, 18, 30, 45, 60],  # specific times in minutes
    capacity=200
)
```

### 3. Passenger Demand

Define origin-destination flows with time-varying rates:

```python
PassengerDemand(
    origin="Central",
    destination="Wynyard",
    rate=lambda t: 100 if 7 <= t < 9 else 30  # passengers/hour by time
)

# OR use preset patterns
PassengerDemand(
    origin="Redfern",
    destination="Town Hall",
    pattern="rush_hour",  # built-in patterns
    peak_rate=150
)
```

### 4. Passenger Characteristics (Optional)

Customize passenger movement if needed:

```python
PassengerProfile(
    name="default",
    speed_mps=1.4,  # average walking speed
    boarding_time=2  # seconds per passenger
)

PassengerProfile(
    name="mobility_impaired",
    speed_mps=0.8,
    boarding_time=5,
    proportion=0.1  # 10% of passengers
)
```

## Simulator Auto-Generates

- **Stations**: Created automatically from line definitions
- **Network**: Graph built from all lines, including transfer points
- **Passengers**: Spawned based on demand, assigned IDs, origin/dest
- **Trains**: Created per schedule with capacity and position tracking
- **Queues**: Managed at each station per line/direction
- **Metrics**: Journey time, wait time, crowding, left-behind counts

## Complete Example

```python
from raily import Line, TrainSchedule, PassengerDemand, Simulator

# Define lines
t1 = Line(
    name="T1",
    stops=["Central", "Redfern", "Town Hall", "Wynyard"],
    travel_times=[3, 2, 4]
)

t2 = Line(
    name="T2", 
    stops=["Central", "Museum", "St James", "Circular Quay"],
    travel_times=[2, 3, 3]
)

# Define train schedules
schedule_t1 = TrainSchedule(
    line="T1",
    frequency=10,  # every 10 min
    capacity=200,
    start_time=0,
    end_time=120
)

schedule_t2 = TrainSchedule(
    line="T2",
    frequency=15,  # every 15 min
    capacity=180,
    start_time=0,
    end_time=120
)

# Define passenger demand
demand1 = PassengerDemand(
    origin="Central",
    destination="Wynyard",
    rate=lambda t: 100 if 7 <= t < 9 else 30
)

demand2 = PassengerDemand(
    origin="Redfern", 
    destination="Circular Quay",
    rate=lambda t: 50 if 7 <= t < 9 else 15
)

# Create and run simulator
sim = Simulator(
    lines=[t1, t2],
    schedules=[schedule_t1, schedule_t2],
    demands=[demand1, demand2],
    duration=120,  # simulate 2 hours
    time_step=1    # 1 minute resolution
)

results = sim.run()

# Access results
print(f"Avg journey time: {results.avg_journey_time:.1f} min")
print(f"Avg wait time: {results.avg_wait_time:.1f} min")
print(f"Max crowding: {results.max_occupancy:.0f}%")
print(f"Passengers left behind: {results.left_behind}")
print(f"Total passengers served: {results.passengers_served}")

# Export results
results.to_csv("simulation_results.csv")
results.plot_crowding()  # matplotlib chart
results.plot_wait_times_by_station()
```

## What Happens During Simulation

The simulator runs a time-stepped loop:

**Each time step (e.g., 1 minute):**
1. **Generate passengers** based on demand functions
2. **Move trains** along their lines according to schedules
3. **Alight passengers** who reached their destination
4. **Board passengers** from station queues (up to train capacity)
5. **Handle transfers** at interchange stations
6. **Record metrics** (wait times, occupancy, etc.)

**After simulation:**
- Aggregate statistics (averages, percentiles, totals)
- Export detailed logs (per-passenger, per-train)
- Generate visualizations (crowding heat maps, time series)

## Advanced Options

```python
sim = Simulator(
    lines=[t1, t2],
    schedules=[schedule_t1, schedule_t2],
    demands=[demand1, demand2],
    duration=120,
    time_step=0.5,  # 30-second resolution for more detail
    transfer_time=3,  # minutes to transfer between lines (default: 2)
    passenger_profiles=[default_profile, impaired_profile],  # optional
    random_seed=42  # reproducible results
)
```

## Output Metrics

**Journey Metrics:**
- Average/median/max journey time
- Average/median/max wait time at platform
- Average/median/max in-vehicle time
- Journey time by origin-destination pair

**Service Metrics:**
- Passengers served vs. left behind
- Train occupancy (avg/max per line, per time period)
- Station crowding (queue length over time)
- Service reliability (% who boarded first train)

**Transfer Metrics:**
- Transfer time statistics
- Most common transfer points
- Missed connection counts

## Visualization

```python
results.plot_crowding()  # Train occupancy over time
results.plot_wait_times_by_station()  # Box plots per station
results.plot_journey_times()  # Histogram
results.plot_network()  # Network graph with flow indicators
results.heatmap_od_matrix()  # Origin-destination demand
```

## Export Formats

- **CSV**: Detailed per-passenger logs, per-train logs, aggregated metrics
- **JSON**: Full simulation state and results
- **PNG/PDF**: Matplotlib charts

## Deliverables

- Python package installable via `pip install raily`
- Clean API requiring only lines, schedules, and demand
- Time-stepped simulation engine
- Comprehensive metrics and statistics
- Built-in visualizations
- Export to CSV/JSON
- Documentation and example notebooks

## Installation

```bash
pip install raily
```

## Quick Start

```python
from raily import Line, TrainSchedule, PassengerDemand, Simulator

# Define your network
lines = [Line("T1", ["A", "B", "C"], [5, 5])]
schedules = [TrainSchedule("T1", frequency=10, capacity=100)]
demands = [PassengerDemand("A", "C", rate=lambda t: 50)]

# Run simulation
sim = Simulator(lines, schedules, demands, duration=60)
results = sim.run()

# View results
print(results.summary())
results.plot_crowding()
```

