"""
Example: minimal simulation setup
"""

import sys
import numpy as np
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
    return 5.0  # 5 customers per second = 300 per minute

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
        time_between_stations=[120.0, 180.0],  # seconds
        schedule={'headway': 300, 'service_hours': (6, 22), 'capacity': 800},
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
        snapshot_interval=3600  # snapshot every hour (3600 ticks)
    )
    
    # Set start time to 6 AM (within service hours)
    sim.current_time = 6 * 3600.0  # 6 AM in seconds
    
    sim.add_customer_generator(gen_central)
    sim.add_customer_generator(gen_redfern)
    
    # 7. Run simulation
    print(f"Starting simulation at time {sim.current_time} (hour {sim.current_time/3600})")
    print(f"Service hours: {line_t1.train_generator.schedule_policy['service_hours']}")
    
    # Debug: Run a few ticks manually to see what's happening
    for i in range(10):
        print(f"\n=== Tick {i+1} ===")
        print(f"Time: {sim.current_time}, Hour: {sim.current_time/3600}")
        
        # Check if trains spawn
        spawns = line_t1.train_generator.tick(sim.current_time)
        print(f"Trains to spawn: {len(spawns)}")
        
        # Check active trains
        print(f"Active trains: {len(sim.active_trains)}")
        for train in sim.active_trains[:3]:  # Show first 3 trains
            print(f"  Train {train.id}: at station {train.current_station_id}, next {train.next_station_id}, "
                  f"passengers {train.current_capacity}/{train.max_capacity}, dwell {train.dwell_remaining:.1f}s")
            if train.timetable:
                print(f"    Timetable preview: {train.timetable[:3]}")
        
        # Check passengers
        waiting_mask = (sim.allocator.memmap['state'] == 0) & (sim.allocator.memmap['id'] > 0)
        n_waiting = np.sum(waiting_mask)
        print(f"Waiting passengers: {n_waiting}")
        
        if n_waiting > 0:
            # Check first passenger
            waiting_idx = np.where(waiting_mask)[0][0]
            passenger = sim.allocator.memmap[waiting_idx]
            print(f"Sample passenger: origin={passenger['origin_station_id']}, dest={passenger['dest_station_id']}, path_id={passenger['path_id']}")
            if passenger['path_id'] > 0:
                segments = network.path_table.expand(int(passenger['path_id']))
                print(f"  Path segments: {segments}")
        
        # Check station queues
        for station_id, station in network.stations.items():
            if len(station.waiting_passengers) > 0:
                print(f"Station {station.name}: {len(station.waiting_passengers)} in queue")
        
        # Step simulation
        sim.step()
    
    print("\n=== Running full simulation ===")
    sim.run(n_ticks=990)  # Run remaining ticks
    
    print("\nSimulation complete!")
    print(f"Final metrics: {sim.metrics_history[-1]}")

if __name__ == "__main__":
    main()
