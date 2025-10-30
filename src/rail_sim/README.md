# Rail Sim Module Documentation

## File Map

### Core Data Layer
- **`memmap_schema.py`** - Customer data storage and allocation
  - `CUSTOMER_DTYPE`: NumPy structured dtype with 13 fields (id, origin, dest, state, timestamps, etc.)
  - `MemmapAllocator`: Manages file-backed columnar storage for customer records
    - Methods: `allocate_index()`, `allocate_indices()`, `release_index()`, `flush()`
    - Handles capacity management and free index pooling
[TODO]: Add in-memory mode to improve performance

### Routing & Path Management
- **`path_table.py`** - Path caching and deduplication
  - `PathTable`: Stores routing paths between origin-destination pairs
    - `plan(origin, dest, segments)`: Store path or return existing path_id
    - `expand(path_id)`: Retrieve path segments as list of (line_code, from_station, to_station)
    - Uses MD5 hashing for path deduplication

### Customer Generation
- **`customer_gen.py`** - Passenger arrival simulation
  - `CustomerGenerator`: Generates new customers with Poisson arrivals
    - `generate_customers(t, dt, destinations)`: Creates new passengers and writes to memmap
    - Configurable arrival rate profile function
    - Assigns origin, destination, spawn time, and initial state

### Simulation Entities

#### Train Operations
- **`train.py`** - Train movement and passenger management
  - `Train`: In-memory representation of a train
    - Attributes: id, line_id, timetable, capacity, onboard passengers, direction, position
    - `step(dt, current_time)`: Advance along timetable, detect station arrivals
    - `board(passenger_indices, memmap)`: Board passengers if capacity allows
    - `alight(memmap)`: Return passengers whose destination matches current station
    - `reverse_direction()`: Flip direction at terminals for bidirectional lines

#### Station Management
- **`station.py`** - Station queues and boarding logic
  - `Station`: Represents a railway station
    - Attributes: station_id, name, line_codes, capacity, waiting_passengers queue
    - `enqueue_passenger(customer_idx)`: Add passenger to waiting queue
    - `dequeue_for_boarding(train, memmap, path_table)`: Filter eligible passengers by path/line compatibility
    - `transfer_passenger(customer_idx, next_line, memmap)`: Handle transfers between lines

#### Fleet Management
- **`train_gen.py`** - Train spawning and scheduling
  - `TrainSpawn`: Dataclass for spawn events (train_id, line_id, direction, depart_time, capacity)
  - `TrainGenerator`: Manages train fleet for a line
    - Attributes: fleet_size, schedule_policy, active_trains set, idle_pool
    - `tick(current_time)`: Determine if new trains should spawn based on headway and service hours
    - `allocate_train()`: Get train from pool or create new if under fleet limit
    - `release_train(train_id)`: Return train to idle pool for reuse

#### Line Configuration
- **`line.py`** - Railway line topology and schedules
  - `Line`: Represents a transit line
    - Attributes: line_id, line_code, station_list, travel_times, schedule, fleet_size, train_generator
    - `build_timetable(start_time, direction)`: Generate arrival times for each station
    - `get_next_station(current_id, direction)`: Navigate along line topology
    - `get_travel_time(from_id, to_id)`: Lookup segment travel time
    - Owns its TrainGenerator instance

### Network & Routing
- **`map.py`** - Network graph and pathfinding
  - `Map`: Network-wide routing and station management
    - Attributes: stations dict, lines list, NetworkX graph, path_table
    - `add_station(station)`, `add_line(line)`: Build network topology
    - `find_path(origin, dest)`: Shortest path routing using Dijkstra's algorithm
    - `assign_path_to_customer(customer_idx, memmap)`: Compute and assign route to passenger
    - `get_transfer_options(station_id)`: Available lines at a station

### Main Simulation Loop
- **`simulation.py`** - Orchestrates the entire simulation
  - `SimulationMetrics`: Dataclass for per-tick statistics
  - `SimulationLoop`: Main coordinator
    - Attributes: current_time, current_tick, active_trains, customer_generators, event queue
    - `step()`: Single simulation tick
      1. Generate new customers
      2. Assign paths and enqueue at stations
      3. Spawn trains based on schedules
      4. Update all trains (movement, boarding, alighting)
      5. Update waiting times
      6. Collect metrics
      7. Periodic snapshots
    - `run(n_ticks)`: Execute simulation for N ticks
    - `snapshot()`: Export to PyArrow/Parquet for analytics
    - `collect_metrics()`: Calculate boarding rates, wait times, occupancy

## Object Ownership

- `Line` owns `TrainGenerator`
- `Map` owns `PathTable`, `Station` dict, `Line` list
- `SimulationLoop` owns `MemmapAllocator`, `Map`, `CustomerGenerator` list
- `Train` references customers via indices into memmap
- `Station` references customers via indices into memmap


# Rail Simulation - Class Diagram & Interactions

## Core Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          SimulationLoop                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ - current_tick: int                                              │  │
│  │ - current_time: float                                            │  │
│  │ - dt: float                                                      │  │
│  │ - active_trains: List[Train]                                     │  │
│  │ - customer_generators: List[CustomerGenerator]                   │  │
│  │ - event_queue: List                                              │  │
│  │ - metrics_history: List[SimulationMetrics]                       │  │ 
│  │                                                                  │  │
│  │ + step()                                                         │  │
│  │ + process_events()                                               │  │
│  │ + collect_metrics() -> SimulationMetrics                         │  │
│  │ + snapshot()                                                     │  │
│  │ + run(n_ticks)                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
         │                    │                     │
         │ owns               │ owns                │ owns
         ▼                    ▼                     ▼
    ┌─────────┐         ┌──────────┐         ┌──────────────────┐
    │   Map   │         │  Train   │         │ CustomerGenerator│
    └─────────┘         └──────────┘         └──────────────────┘
```

## Data Layer

```
┌────────────────────────────────────────────────────────────────────┐
│                      MemmapAllocator                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ - filepath: Path                                             │  │
│  │ - capacity: int                                              │  │
│  │ - memmap: np.memmap[CUSTOMER_DTYPE]                          │  │
│  │ - free_indices: List[int]                                    │  │
│  │ - next_id: int                                               │  │
│  │                                                              │  │
│  │ + allocate_index() -> int                                    │  │
│  │ + allocate_indices(n) -> np.ndarray                          │  │
│  │ + release_index(idx)                                         │  │
│  │ + get_next_id() -> int                                       │  │
│  │ + flush()                                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              │
                              │ manages
                              ▼
                    ┌─────────────────────┐
                    │   Customer Records  │
                    │   (numpy memmap)    │
                    │                     │
                    │ Columns:            │
                    │ - id (u64)          │
                    │ - origin_station_id │
                    │ - dest_station_id   │
                    │ - current_station_id│
                    │ - on_train_id       │
                    │ - state (u8)        │
                    │ - tap_on_ts         │
                    │ - tap_off_ts        │
                    │ - spawn_ts          │
                    │ - path_id           │
                    │ - total_wait_time   │
                    │ - total_travel_time │
                    │ - movement_speed    │
                    └─────────────────────┘
```

## Network Layer

```
┌──────────────────────────────────────────────────────────────────┐
│                            Map                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - lines: List[Line]                                         │ │
│  │ - stations: Dict[int, Station]                              │ │
│  │ - station_lookup: Dict[str, Station]                        │ │
│  │ - path_table: PathTable                                     │ │
│  │ - graph: nx.Graph                                           │ │
│  │                                                             │ │
│  │ + add_line(line)                                            │ │
│  │ + add_station(station)                                      │ │
│  │ + find_path(origin, dest) -> path_id                       │ │
│  │ + assign_path_to_customer(idx, memmap)                     │ │
│  │ + get_transfer_options(station_id) -> List[str]            │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
         │                    │                      │
         │ owns               │ owns                 │ owns
         ▼                    ▼                      ▼
    ┌────────┐          ┌──────────┐          ┌────────────┐
    │  Line  │          │ Station  │          │ PathTable  │
    └────────┘          └──────────┘          └────────────┘
         │
         │ owns
         ▼
┌──────────────────┐
│ TrainGenerator   │
└──────────────────┘
```

## Line & Train Management

```
┌────────────────────────────────────────────────────────────┐
│                         Line                                │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - line_id: str                                        │ │
│  │ - line_code: str                                      │ │
│  │ - station_list: List[int]                             │ │
│  │ - time_between_stations: List[float]                  │ │
│  │ - schedule: Dict                                      │ │
│  │ - fleet_size: int                                     │ │
│  │ - bidirectional: bool                                 │ │
│  │ - train_generator: TrainGenerator                     │ │
│  │                                                        │ │
│  │ + get_next_station(current, direction) -> int        │ │
│  │ + get_travel_time(from, to) -> float                 │ │
│  │ + update_fleet(new_size)                              │ │
│  │ + build_timetable(start_time, direction) -> List     │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                              │
                              │ delegates to
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    TrainGenerator                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - line_id: str                                        │ │
│  │ - fleet_size: int                                     │ │
│  │ - schedule_policy: Dict                               │ │
│  │ - active_trains: Set[int]                             │ │
│  │ - idle_pool: List[int]                                │ │
│  │ - next_spawn_times: List[float]                       │ │
│  │                                                        │ │
│  │ + tick(current_time) -> List[TrainSpawn]             │ │
│  │ + allocate_train() -> int                             │ │
│  │ + release_train(train_id)                             │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                              │
                              │ creates
                              ▼
                      ┌──────────────┐
                      │  TrainSpawn  │
                      │  (dataclass) │
                      └──────────────┘
                              │
                              │ instantiates
                              ▼
┌────────────────────────────────────────────────────────────┐
│                         Train                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - id: int                                             │ │
│  │ - line_id: str                                        │ │
│  │ - timetable: List[Tuple[float, int]]                 │ │
│  │ - current_station_id: int                             │ │
│  │ - next_station_id: int                                │ │
│  │ - dwell_remaining: float                              │ │
│  │ - max_capacity: int                                   │ │
│  │ - current_capacity: int                               │ │
│  │ - onboard_passengers: List[int]                       │ │
│  │ - direction: int (1 or -1)                            │ │
│  │ - status: str                                         │ │
│  │ - position_ratio: float                               │ │
│  │                                                        │ │
│  │ + step(dt, current_time) -> bool                      │ │
│  │ + board(passenger_indices, memmap) -> np.ndarray     │ │
│  │ + alight(memmap) -> np.ndarray                       │ │
│  │ + reverse_direction()                                 │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Station & Customer Generation

```
┌────────────────────────────────────────────────────────────┐
│                       Station                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - station_id: int                                     │ │
│  │ - name: str                                           │ │
│  │ - line_codes: List[str]                               │ │
│  │ - avg_change_time: float                              │ │
│  │ - theoretical_capacity: int                           │ │
│  │ - maximum_capacity: int                               │ │
│  │ - waiting_passengers: List[int]                       │ │
│  │ - platforms: Dict[int, List[int]]                     │ │
│  │                                                        │ │
│  │ + enqueue_passenger(idx)                              │ │
│  │ + dequeue_for_boarding(train, memmap, path_table)    │ │
│  │ + update_capacity() -> int                            │ │
│  │ + transfer_passenger(idx, next_line, memmap)         │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                  CustomerGenerator                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - allocator: MemmapAllocator                          │ │
│  │ - station_id: int                                     │ │
│  │ - arrival_rate_profile: Callable[[float], float]     │ │
│  │ - rng: np.random.Generator                            │ │
│  │                                                        │ │
│  │ + generate_customers(t, dt, destinations)            │ │
│  │     -> np.ndarray (customer indices)                 │ │
│  │ + assign_path(customer_idx, path_id)                 │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Routing & Path Management

```
┌────────────────────────────────────────────────────────────┐
│                      PathTable                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - paths: Dict[int, List[Tuple[str, int, int]]]       │ │
│  │ - path_hash_to_id: Dict[str, int]                    │ │
│  │ - next_path_id: int                                   │ │
│  │                                                        │ │
│  │ + plan(origin, dest, segments) -> path_id            │ │
│  │ + expand(path_id) -> List[Tuple[str, int, int]]      │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

Path segment format: (line_code, from_station_id, to_station_id)
Example: [("T1", 1, 2), ("T1", 2, 3)]
```

## Complete Interaction Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Simulation Tick Flow                                 │
└──────────────────────────────────────────────────────────────────────────┘

1. Customer Generation
   SimulationLoop.step()
        │
        ├─► CustomerGenerator.generate_customers(t, dt, destinations)
        │        │
        │        ├─► MemmapAllocator.allocate_indices(n)
        │        ├─► Write customer data to memmap
        │        └─► Return customer indices
        │
        ├─► Map.assign_path_to_customer(idx, memmap)
        │        │
        │        ├─► Map.find_path(origin, dest)
        │        │        │
        │        │        ├─► nx.shortest_path(graph, origin, dest)
        │        │        └─► PathTable.plan(origin, dest, segments)
        │        │
        │        └─► Write path_id to memmap
        │
        └─► Station.enqueue_passenger(idx)

2. Train Spawning
   SimulationLoop.step()
        │
        └─► Line.train_generator.tick(current_time)
                 │
                 ├─► Check service hours
                 ├─► Check headway
                 ├─► TrainGenerator.allocate_train()
                 └─► Return List[TrainSpawn]
                      │
                      └─► Line.build_timetable(start_time, direction)
                           │
                           └─► Create Train instance

3. Train Movement
   SimulationLoop.step()
        │
        └─► For each Train:
                 │
                 ├─► Train.step(dt, current_time)
                 │        │
                 │        ├─► Update position_ratio
                 │        ├─► Check if arrived at station
                 │        └─► Return True if arrived
                 │
                 ├─► If arrived:
                 │    │
                 │    ├─► Train.alight(memmap)
                 │    │        │
                 │    │        ├─► Filter onboard by destination
                 │    │        ├─► Update memmap (state=arrived)
                 │    │        └─► Return alighted indices
                 │    │
                 │    └─► Station.dequeue_for_boarding(train, memmap, path_table)
                 │             │
                 │             ├─► Filter waiting by path compatibility
                 │             ├─► PathTable.expand(path_id)
                 │             └─► Return eligible indices
                 │                  │
                 │                  └─► Train.board(indices, memmap)
                 │                           │
                 │                           ├─► Check capacity
                 │                           ├─► Add to onboard_passengers
                 │                           ├─► Update memmap (state=onboard)
                 │                           └─► Return boarded indices
                 │
                 └─► Update metrics

4. Metrics & Snapshots
   SimulationLoop.step()
        │
        ├─► collect_metrics(boarding_count, alighting_count)
        │        │
        │        └─► Count active customers (id > 0)
        │
        └─► If snapshot_interval reached:
                 │
                 └─► snapshot()
                      │
                      ├─► Filter active customers (id > 0)
                      ├─► Convert to PyArrow.Table
                      └─► Write Parquet file
```

## Object Ownership & References

```
SimulationLoop
├── owns: MemmapAllocator (1)
├── owns: Map (1)
│   ├── owns: List[Line]
│   │   └── owns: TrainGenerator (1 per Line)
│   ├── owns: Dict[Station]
│   └── owns: PathTable (1)
├── owns: List[Train] (ephemeral, created/destroyed)
└── owns: List[CustomerGenerator]

References (by index/id):
├── Train.onboard_passengers -> Customer indices in memmap
├── Station.waiting_passengers -> Customer indices in memmap
├── Customer.on_train_id -> Train.id
├── Customer.current_station_id -> Station.station_id
├── Customer.path_id -> PathTable entry
└── PathTable segments reference Station.station_id and Line.line_code
```

## State Transitions

```
Customer States (memmap column 'state'):
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  ┌──────────┐  enqueue   ┌──────────┐  board   ┌──────────┐
│  │ 0: wait  │ ────────►  │ 0: wait  │ ───────► │1: onboard│
│  │ (spawn)  │            │(at stn)  │          │ (on train)│
│  └──────────┘            └──────────┘          └──────────┘
│       │                       ▲                      │
│       │                       │ transfer             │ alight
│       │                       │                      │
│       │                  ┌──────────┐                │
│       └─────────────────►│3: transf │◄───────────────┘
│                          │ (change) │
│                          └──────────┘
│                               │
│                               │ complete
│                               ▼
│                          ┌──────────┐
│                          │2: arrived│
│                          │  (done)  │
│                          └──────────┘
│                                                          │
└─────────────────────────────────────────────────────────┘

Train Status:
┌─────────────┐  spawn  ┌──────────────┐  complete  ┌────────┐
│    idle     │ ──────► │ in_service   │ ─────────► │  idle  │
│  (in pool)  │         │  (running)   │            │ (pool) │
└─────────────┘         └──────────────┘            └────────┘
                             │      ▲
                             │      │
                             ▼      │
                        ┌─────────────────┐
                        │ out_of_service  │
                        │  (maintenance)  │
                        └─────────────────┘
```

## Data Types Summary

| Class              | Type      | Storage          | Lifecycle           |
|--------------------|-----------|------------------|---------------------|
| Customer           | Data      | NumPy memmap     | Persistent (disk)   |
| Train              | Object    | Python list      | Ephemeral (runtime) |
| Station            | Object    | Dict in Map      | Persistent (config) |
| Line               | Object    | List in Map      | Persistent (config) |
| PathTable          | Data      | Dict in Map      | Runtime (cached)    |
| TrainGenerator     | Object    | Owned by Line    | Persistent (config) |
| CustomerGenerator  | Object    | List in Sim      | Persistent (config) |
| SimulationLoop     | Object    | Entry point      | Runtime (main)      |
| Map                | Object    | Owned by Sim     | Persistent (config) |
| MemmapAllocator    | Manager   | Owned by Sim     | Runtime (main)      |
