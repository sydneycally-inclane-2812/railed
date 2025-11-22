"""
Test case: Simple simulation
- 3 stops
- variable user rate - custom function
- in-memory allocator
- customer coming from only 2 stations
- running for full 10 hour ticks. taking too long

"""

import sys
import numpy as np
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


from rail_sim import (
    MemoryAllocator,
    CustomerGenerator,
    Station,
    Line,
    Map,
    SimulationLoop
)

def peaky_arrival_rate(t):
    scale = 10
    morn_aft_scale = 4
    min = 4
    
    power = -1/morn_aft_scale
    f = lambda x: scale * x ** power * np.abs(np.sin(x)) + min
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 

def main():
    # 1. Create memmap allocator
    allocator = MemoryAllocator()
    
    # 2. Create map
    network = Map()
    
    # 3. Create stations
    station_central = Station(
        station_id="central",
        name="Central",
        line_codes=["T1"],
        theoretical_capacity=5000
    )
    
    station_redfern = Station(
        station_id="redfern",
        name="Redfern",
        line_codes=["T1"],
        theoretical_capacity=2000
    )
    
    station_erskineville = Station(
        station_id="ersk",
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
        station_list=["central", "redfern", "ersk"],
        time_between_stations=[60.0, 120.0],  # seconds
        schedule={'headway': 200, 'service_hours': (6, 22), 'capacity': 1000},
        fleet_size=4,
        bidirectional=True
    )
    
    network.add_line(line_t1)
    
    # 5. Create customer generators
    gen_central = CustomerGenerator(
        allocator=allocator,
        station_id=1,
        arrival_rate_profile=peaky_arrival_rate,
        seed=42
    )
    
    gen_redfern = CustomerGenerator(
        allocator=allocator,
        station_id=2,
        arrival_rate_profile=peaky_arrival_rate,
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
    sim.run(n_ticks=3600*10)  # Run remaining ticks
    
    print("\nSimulation complete!")
    print(f"Final metrics: {sim.metrics_history[-1]}")

if __name__ == "__main__":
    main()
    
#test