from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass

from .memmap_schema import MemmapAllocator
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
        memmap_allocator: MemmapAllocator,
        map_network: Map,
        dt: float = 1.0,  # seconds per tick
        snapshot_interval: int = 3600  # snapshots every hour
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
    
    def add_customer_generator(self, gen: CustomerGenerator):
        """Register a customer generator"""
        self.customer_generators.append(gen)
    
    def step(self):
        """Execute one simulation tick"""
        self.current_tick += 1
        self.current_time += self.dt
        
        # 1. Generate new customers
        new_passenger_indices = []
        for gen in self.customer_generators:
            # Get all stations as possible destinations (simplified)
            destinations = list(self.map.stations.keys())
            indices = gen.generate_customers(
                self.current_time, 
                self.dt,
                destinations
            )
            new_passenger_indices.extend(indices)
        
        # 2. Assign paths to new customers
        for idx in new_passenger_indices:
            self.map.assign_path_to_customer(idx, self.allocator.memmap)
            
            # Add to station queue
            origin = self.allocator.memmap[idx]['origin_station_id']
            station = self.map.stations.get(origin)
            if station:
                station.enqueue_passenger(idx)
        
        # 3. Spawn new trains
        for line in self.map.lines:
            spawns = line.train_generator.tick(self.current_time)
            for spawn in spawns:
                # Build timetable
                timetable = line.build_timetable(self.current_time, spawn.direction)
                
                train = Train(
                    train_id=spawn.train_id,
                    line_id=line.line_id,
                    timetable=timetable,
                    max_capacity=spawn.max_capacity,
                    direction=spawn.direction
                )
                self.active_trains.append(train)
        
        # 4. Update all trains
        boarding_count = 0
        alighting_count = 0
        
        for train in self.active_trains:
            arrived = train.step(self.dt, self.current_time)
            
            if arrived and train.current_station_id:
                # Handle alighting
                alighted = train.alight(self.allocator.memmap)
                alighting_count += len(alighted)
                
                # Update tap-off times
                if len(alighted) > 0:
                    self.allocator.memmap[alighted]['tap_off_ts'] = self.current_time
                
                # Handle boarding
                station = self.map.stations.get(train.current_station_id)
                if station:
                    eligible = station.dequeue_for_boarding(
                        train, 
                        self.allocator.memmap,
                        self.map.path_table
                    )
                    
                    boarded = train.board(eligible, self.allocator.memmap)
                    boarding_count += len(boarded)
                    
                    # Update tap-on times
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
        
        # 7. Snapshot if needed
        if self.current_tick % self.snapshot_interval == 0:
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
        # Import here to avoid dependency if not needed
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            from pathlib import Path
            
            # Convert active customers to Arrow table
            active_mask = self.allocator.memmap['id'] > 0
            active_data = self.allocator.memmap[active_mask]
            
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
            
            print(f"Snapshot saved: {filename}")
            
        except ImportError:
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
