"""
Test case: Show detailed customer path information
- Displays 10 random customers at each epoch to debug why waiting count keeps climbing
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
    Station,
    Line,
    Map,
    SimulationLoop
)

def constant_arrival_rate(t):
    """Constant arrival rate function"""
    return 1  # 1 customer per second = 60 per minute

def print_customer_details(sim, epoch, n_samples=10):
    """Print detailed info about random customers"""
    print(f"\n{'='*80}")
    print(f"EPOCH {epoch} | Time: {sim.current_time:.1f}s ({sim.current_time/3600:.2f}h)")
    print(f"{'='*80}")
    
    # Get all active customers
    active_mask = sim.allocator.memmap['id'] > 0
    active_indices = np.where(active_mask)[0]
    
    if len(active_indices) == 0:
        print("No active customers")
        return
    
    # Sample random customers (or all if fewer than n_samples)
    sample_size = min(n_samples, len(active_indices))
    sample_indices = np.random.choice(active_indices, size=sample_size, replace=False)
    
    print(f"\nActive customers: {len(active_indices)}")
    print(f"Sampling {sample_size} random customers:\n")
    
    for i, idx in enumerate(sample_indices, 1):
        customer = sim.allocator.memmap[idx]
        
        # State mapping
        state_names = {0: 'WAITING', 1: 'ONBOARD', 2: 'ALIGHTED'}
        state = state_names.get(int(customer['state']), 'UNKNOWN')
        
        print(f"Customer #{i} (idx={idx}):")
        print(f"  ID: {customer['id']}")
        print(f"  State: {state}")
        print(f"  Origin: Station {customer['origin_station_id']}")
        print(f"  Destination: Station {customer['dest_station_id']}")
        print(f"  Current Station: {customer['current_station_id']}")
        print(f"  On Train: {customer['on_train_id']}")
        print(f"  Wait Time: {customer['total_wait_time']:.1f}s")
        print(f"  Travel Time: {customer['total_travel_time']:.1f}s")
        print(f"  Tap-on: {customer['tap_on_ts']:.1f}s")
        print(f"  Tap-off: {customer['tap_off_ts']:.1f}s")
        
        # Path information
        path_id = int(customer['path_id'])
        if path_id > 0:
            segments = sim.map.path_table.expand(path_id)
            print(f"  Path ID: {path_id}")
            print(f"  Path segments: {segments}")
            
            # Check if path is valid
            if len(segments) == 0:
                print(f"  ⚠️  WARNING: Empty path!")
            else:
                # Check if first segment matches current situation
                first_seg = segments[0]
                print(f"  First segment: from_station={first_seg['from_station_id']}, "
                      f"to_station={first_seg['to_station_id']}, line={first_seg['line_id']}")
        else:
            print(f"  ⚠️  WARNING: No path assigned (path_id=0)")
        
        print()
    
    # Summary by state
    waiting_mask = (sim.allocator.memmap['state'] == 0) & (sim.allocator.memmap['id'] > 0)
    onboard_mask = (sim.allocator.memmap['state'] == 1) & (sim.allocator.memmap['id'] > 0)
    alighted_mask = (sim.allocator.memmap['state'] == 2) & (sim.allocator.memmap['id'] > 0)
    
    print(f"State Summary:")
    print(f"  Waiting: {np.sum(waiting_mask)}")
    print(f"  Onboard: {np.sum(onboard_mask)}")
    print(f"  Alighted: {np.sum(alighted_mask)}")
    
    # Station queue summary
    print(f"\nStation Queue Summary:")
    for station_id, station in sim.map.stations.items():
        queue_size = len(station.waiting_passengers)
        if queue_size > 0:
            print(f"  Station {station.name} (ID {station_id}): {queue_size} waiting")
    
    # Train summary
    print(f"\nTrain Summary:")
    print(f"  Active trains: {len(sim.active_trains)}")
    for train in sim.active_trains[:5]:  # Show first 5 trains
        print(f"  Train {train.id} (Line {train.line_id}): "
              f"at station {train.current_station_id}, "
              f"next {train.next_station_id}, "
              f"capacity {train.current_capacity}/{train.max_capacity}, "
              f"status={train.status}, "
              f"dwell={train.dwell_remaining:.1f}s")

def main():
    # 1. Create memmap allocator
    allocator = MemoryAllocator()
    
    # 2. Create map
    network = Map()
    
    # 3. Create stations
    station_central = Station(
        station_id=1,
        name="Central",
        line_codes=["T1"],
        theoretical_capacity=5000
    )
    
    station_redfern = Station(
        station_id=2,
        name="Redfern",
        line_codes=["T1"],
        theoretical_capacity=2000
    )
    
    station_erskineville = Station(
        station_id=3,
        name="Erskineville",
        line_codes=["T1"],
        theoretical_capacity=1500
    )
    
    network.add_station(station_central)
    network.add_station(station_redfern)
    network.add_station(station_erskineville)
    
    # 4. Create line
    line_t1 = Line(
        line_id="T1",
        line_code="T1",
        station_list=[1, 2, 3],
        time_between_stations=[60.0, 120.0],  # seconds
        schedule={'headway': 20, 'service_hours': (6, 22), 'capacity': 1000},
        fleet_size=10,
        bidirectional=True
    )
    
    network.add_line(line_t1)
    
    # 5. Create customer generators
    gen_central = CustomerGenerator(
        allocator=allocator,
        station_id=1,
        arrival_rate_profile=constant_arrival_rate,
        seed=42
    )
    
    gen_redfern = CustomerGenerator(
        allocator=allocator,
        station_id=2,
        arrival_rate_profile=constant_arrival_rate,
        seed=43
    )
    
    # 6. Create simulation
    sim = SimulationLoop(
        memmap_allocator=allocator,
        map_network=network,
        dt=1.0,  # 1 second per tick
        snapshot_interval=3600,  # snapshot every hour (3600 ticks)
        log_level=logging.ERROR
    )
    
    # Set start time to 6 AM (within service hours)
    sim.current_time = 6 * 3600.0  # 6 AM in seconds
    
    sim.add_customer_generator(gen_central)
    sim.add_customer_generator(gen_redfern)
    
    # 7. Run simulation with periodic detailed output
    print(f"Starting simulation at time {sim.current_time} (hour {sim.current_time/3600})")
    print(f"Service hours: {line_t1.train_generator.schedule_policy['service_hours']}")
    
    n_ticks = 1000
    epoch_interval = 100  # Show details every 100 ticks
    
    for tick in range(n_ticks):
        sim.step()
        
        # Show detailed info every epoch_interval ticks
        if (tick + 1) % epoch_interval == 0:
            print_customer_details(sim, tick + 1, n_samples=10)
    
    # Final summary
    print(f"\n{'='*80}")
    print("SIMULATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total ticks: {sim.current_tick}")
    print(f"Final time: {sim.current_time:.1f}s ({sim.current_time/3600:.2f}h)")
    if sim.metrics_history:
        final_metrics = sim.metrics_history[-1]
        print(f"\nFinal Metrics:")
        print(f"  Active trains: {final_metrics.active_trains}")
        print(f"  Waiting passengers: {final_metrics.waiting_passengers}")
        print(f"  Avg wait time: {final_metrics.avg_wait_time:.1f}s")
        print(f"  Boarding rate: {final_metrics.boarding_rate:.2f}/s")
        print(f"  Alighting rate: {final_metrics.alight_rate:.2f}/s")

if __name__ == "__main__":
    main()