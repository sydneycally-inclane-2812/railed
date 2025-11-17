"""
Example: minimal simulation setup
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
    return 0.2  # 1 customer per second = 60 per minute

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
        schedule={'headway': 180, 'service_hours': (6, 22), 'capacity': 1000},
        fleet_size=4,
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
        log_level = logging.ERROR
    )
    
    # Set start time to 6 AM (within service hours)
    sim.current_time = 6 * 3600.0  # 6 AM in seconds
    
    sim.add_customer_generator(gen_central)
    sim.add_customer_generator(gen_redfern)
    
    # 7. Run simulation
    print(f"Starting simulation at time {sim.current_time} (hour {sim.current_time/3600})")
    print(f"Service hours: {line_t1.train_generator.schedule_policy['service_hours']}")
    
    
    print("\n=== Running full simulation ===")
    sim.run(n_ticks=2990)  # Run remaining ticks
    
    print("\nSimulation complete!")
    print(f"Final metrics: {sim.metrics_history[-1]}")

if __name__ == "__main__":
    main()