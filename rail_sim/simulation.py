from typing import List, Dict, Optional
import numpy as np
import logging
from dataclasses import dataclass

from .logger import get_logger
from .memory import MemmapAllocator, MemoryAllocator
from .map import Map
from .train import Train
from .customer_gen import CustomerGenerator

@dataclass
class SimulationMetrics:
    """Metrics collected per tick"""
    tick: int
    boarding_rate: float
    alight_rate: float
    avg_wait_time: float
    active_trains: int
    waiting_passengers: int

class SimulationLoop:
    """Main simulation coordinator"""
    
    def __init__(
        self,
        memmap_allocator: MemmapAllocator | MemoryAllocator,
        map_network: Map,
        dt: float = 1.0,  # seconds per tick
        snapshot_interval: int = 3600,  # snapshots every hour
        log_level = logging.INFO
    ):
        self.allocator = memmap_allocator
        self.map = map_network
        self.dt = dt
        self.snapshot_interval = snapshot_interval
        
        self.current_tick = 0
        self.current_time = 0.0
        
        self.active_trains: List[Train] = []
        self.customer_generators: List[CustomerGenerator] = []
        self.event_queue: List = []
        
        self.metrics_history: List[SimulationMetrics] = []
        
        logger = get_logger()
        logger.setLevel(log_level)
        logger.info(f"SimulationLoop initialized: dt={dt}s, snapshot_interval={snapshot_interval} ticks")
        
    
    def add_customer_generator(self, gen: CustomerGenerator):
        """Register a customer generator"""
        self.customer_generators.append(gen)
        logger = get_logger()
        logger.info(f"Added customer generator for station {gen.station_id}")
    
    def step(self):
        """Execute one simulation tick"""
        logger = get_logger()
        self.current_tick += 1
        self.current_time += self.dt
        
        if self.current_tick % 100 == 0:
            logger.info(f"=== Tick {self.current_tick} | Time: {self.current_time:.1f}s ({self.current_time/3600:.2f}h) ===")
        
        # 1. Generate new customers
        new_passenger_indices = []
        for gen in self.customer_generators:
            # Exclude the origin station to avoid zero-length trips
            destinations = [sid for sid in self.map.stations.keys() if sid != gen.station_id]
            if not destinations:
                logger.warning(f"No valid destinations for station {gen.station_id}; skipping generation")
                continue
            indices = gen.generate_customers(
                self.current_time, 
                self.dt,
                destinations
            )
            new_passenger_indices.extend(indices)
        
        if len(new_passenger_indices) > 0:
            logger.debug(f"Generated {len(new_passenger_indices)} new passengers")
        
        # 2. Assign paths to new customers
        for idx in new_passenger_indices:
            self.map.assign_path_to_customer(idx, self.allocator.memmap)
            
            # Add to station queue
            origin = int(self.allocator.memmap[idx]['origin_station_id'])
            station = self.map.stations.get(origin)
            if station:
                station.enqueue_passenger(idx)
        
        # 3. Make new trains (literature terminology)
        for line in self.map.lines:
            makes = line.train_generator.tick(self.current_time)
            for make in makes:
                # Build timetable
                timetable = line.build_timetable(self.current_time, make.direction)
                print(f"[DEBUG] Creating Train {make.train_id} on line {line.line_id} at sim time {self.current_time}")
                print(f"[DEBUG] Timetable for Train {make.train_id}: {timetable}")
                train = Train(
                    train_id=make.train_id,
                    line_id=line.line_id,
                    timetable=timetable,
                    max_capacity=make.max_capacity,
                    direction=make.direction
                )
                self.active_trains.append(train)
        
        # 4. Update all trains
        boarding_count = 0
        alighting_count = 0

        # Debug: print queue at each station and train occupancy every 100 ticks
        if self.current_tick % 100 == 1:
            print(f"Tick {self.current_tick} (Time: {self.current_time:.1f}s): Station queues:")
            for station_id, station in self.map.stations.items():
                print(f"  Station {station.name} (ID {station_id}): {len(station.waiting_passengers)} waiting")

        for train in self.active_trains:
            arrived = train.step(self.dt, self.current_time)

            # Debug: print train occupancy every 100 ticks
            if self.current_tick % 100 == 1:
                print(f"    Train {train.id} on line {train.line_id} at station {train.current_station_id}: {train.current_capacity}/{train.max_capacity} passengers onboard, status: {train.status}")

            # Handle boarding/alighting if train is at a station (either just arrived or dwelling)
            if (arrived or train.dwell_remaining > 0) and train.current_station_id:
                # Handle alighting (only on arrival)
                if arrived:
                    alighted = train.alight(self.allocator.memmap)
                    alighting_count += len(alighted)

                    # Update tap-off times and release indices
                    if len(alighted) > 0:
                        self.allocator.memmap[alighted]['tap_off_ts'] = self.current_time
                        for idx in alighted:
                            self.allocator.release_index(idx)
                        logger.debug(f"Released {len(alighted)} passenger indices back to free pool")

                    # If at terminal, reverse and reschedule
                    if train.timetable_idx >= len(train.timetable) - 1:
                        # Reverse direction
                        train.reverse_direction()
                        # Rebuild timetable for return trip
                        for line in self.map.lines:
                            if line.line_id == train.line_id:
                                train.timetable = line.build_timetable(self.current_time, train.direction)
                                break
                        train.timetable_idx = 0
                        train.status = 'in_service'
                        train.dwell_remaining = 30.0  # dwell at terminal before departing
                        continue
                # Handle boarding (during any dwell period)
                station = self.map.stations.get(train.current_station_id)
                if station and train.dwell_remaining > 0:
                    eligible = station.dequeue_for_boarding(
                        train, 
                        self.allocator.memmap,
                        self.map.path_table
                    )
                    boarded = train.board(eligible, self.allocator.memmap)
                    boarding_count += len(boarded)
                    if len(boarded) > 0:
                        self.allocator.memmap[boarded]['tap_on_ts'] = self.current_time
        
        # 5. Update waiting times for waiting passengers
        waiting_mask = (self.allocator.memmap['state'] == 0) & (self.allocator.memmap['id'] > 0)
        waiting_indices = np.where(waiting_mask)[0]
        if len(waiting_indices) > 0:
            self.allocator.memmap[waiting_indices]['total_wait_time'] += self.dt
        
        # 6. Collect metrics
        metrics = self.collect_metrics(boarding_count, alighting_count)
        self.metrics_history.append(metrics)
        
        if self.current_tick % 100 == 0:
            logger.info(f"Metrics: {metrics.active_trains} trains, {metrics.waiting_passengers} waiting, "
                       f"boarding_rate={metrics.boarding_rate:.2f}, alight_rate={metrics.alight_rate:.2f}")
        
        # 7. Snapshot if needed
        if self.current_tick % self.snapshot_interval == 0:
            logger.info(f"Taking snapshot at tick {self.current_tick}")
            self.snapshot()
        
        # 8. Process events (disruptions, etc.)
        self.process_events()
    
    def process_events(self):
        """Handle scheduled events"""
        # Process any events in queue
        pass
    
    def collect_metrics(self, boarding_count: int, alighting_count: int) -> SimulationMetrics:
        """Gather statistics"""
        # Only count valid passengers (id > 0)
        waiting_mask = (self.allocator.memmap['state'] == 0) & (self.allocator.memmap['id'] > 0)
        waiting_count = np.sum(waiting_mask)
        
        wait_times = self.allocator.memmap[waiting_mask]['total_wait_time']
        avg_wait = float(np.mean(wait_times)) if len(wait_times) > 0 else 0.0
        
        return SimulationMetrics(
            tick=self.current_tick,
            boarding_rate=boarding_count / self.dt if self.dt > 0 else 0,
            alight_rate=alighting_count / self.dt if self.dt > 0 else 0,
            avg_wait_time=avg_wait,
            active_trains=len(self.active_trains),
            waiting_passengers=int(waiting_count)
        )
    
    def snapshot(self):
        """Create PyArrow snapshot"""
        logger = get_logger()
        # Import here to avoid dependency if not needed
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            from pathlib import Path
            
            # Convert active customers to Arrow table
            active_mask = self.allocator.memmap['id'] > 0
            active_data = self.allocator.memmap[active_mask]
            
            logger.info(f"Creating snapshot with {len(active_data)} active customers")
            
            table = pa.table({
                'id': pa.array(active_data['id']),
                'origin_station_id': pa.array(active_data['origin_station_id']),
                'dest_station_id': pa.array(active_data['dest_station_id']),
                'current_station_id': pa.array(active_data['current_station_id']),
                'on_train_id': pa.array(active_data['on_train_id']),
                'state': pa.array(active_data['state']),
                'total_wait_time': pa.array(active_data['total_wait_time']),
                'total_travel_time': pa.array(active_data['total_travel_time']),
            })
            
            # Write snapshot
            snapshot_dir = Path('e:/railed/snapshots')
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            filename = snapshot_dir / f'snapshot_tick_{self.current_tick}.parquet'
            pq.write_table(table, filename, compression='snappy')
            
            logger.info(f"Snapshot saved: {filename}")
            print(f"Snapshot saved: {filename}")
            
        except ImportError:
            logger.warning("PyArrow not installed, skipping snapshot")
            print("PyArrow not installed, skipping snapshot")
    
    def run(self, n_ticks: int):
        """Run simulation for n ticks"""
        print(f"Starting simulation for {n_ticks} ticks...")

        for _ in range(n_ticks):
            self.step()
            if self.current_tick % 100 == 0:
                print(f"Tick {self.current_tick}: "
                      f"{len(self.active_trains)} trains, "
                      f"{self.metrics_history[-1].waiting_passengers} waiting")

        # Final flush
        self.allocator.flush()
        print("Simulation complete")

        # Print aggregate summary table
        print("\nSimulation Summary Table (Aggregates):")
        metrics = self.metrics_history
        if not metrics:
            print("No metrics collected.")
            return
        import numpy as np
        def col(arr, attr):
            return np.array([getattr(m, attr) for m in arr])
        summary = [
            [
                "Average",
                np.mean(col(metrics, "boarding_rate")),
                np.mean(col(metrics, "alight_rate")),
                np.mean(col(metrics, "avg_wait_time")),
                np.mean(col(metrics, "active_trains")),
                np.mean(col(metrics, "waiting_passengers")),
            ],
            [
                "Max",
                np.max(col(metrics, "boarding_rate")),
                np.max(col(metrics, "alight_rate")),
                np.max(col(metrics, "avg_wait_time")),
                np.max(col(metrics, "active_trains")),
                np.max(col(metrics, "waiting_passengers")),
            ],
            [
                "Min",
                np.min(col(metrics, "boarding_rate")),
                np.min(col(metrics, "alight_rate")),
                np.min(col(metrics, "avg_wait_time")),
                np.min(col(metrics, "active_trains")),
                np.min(col(metrics, "waiting_passengers")),
            ],
        ]
        headers = ["Stat", "Boarding/s", "Alight/s", "Avg Wait (s)", "Active Trains", "Waiting"]
        try:
            from tabulate import tabulate
            print(tabulate(summary, headers=headers, tablefmt="github", floatfmt=".2f"))
        except ImportError:
            print("(Install 'tabulate' for prettier tables)")
            print(" | ".join(headers))
            for row in summary:
                print(" | ".join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in row))