"""
Profile script to identify bottlenecks in simulation
"""

import sys
import numpy as np
import logging
import cProfile
import pstats
from pathlib import Path
from io import StringIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rail_sim import (
    MemoryAllocator,
    CustomerGenerator,
    Station,
    Line,
    Map,
    SimulationLoop,
    precalculate
)

@precalculate(method='staircase', resolution=2000)
def peaky_arrival_rate(t):
    scale = 10
    morn_aft_scale = 4
    min = 4
    
    power = -1/morn_aft_scale
    f = lambda x: scale * x ** power * np.abs(np.sin(x)) + min
    time_of_day = (t % 86400) / 86400
    return f(time_of_day * np.pi * 2)

def setup_sim():
    """Setup simulation for profiling"""
    allocator = MemoryAllocator()
    network = Map()
    
    station_central = Station(station_id="central", name="Central", theoretical_capacity=5000)
    station_redfern = Station(station_id="redfern", name="Redfern", theoretical_capacity=2000)
    station_erskineville = Station(station_id="ersk", name="Erskineville", theoretical_capacity=1500)
    
    network.add_station(station_central)
    network.add_station(station_redfern)
    network.add_station(station_erskineville)
    
    line_t1 = Line(
        line_id="T1",
        line_code="T1",
        station_list=["central", "redfern", "ersk"],
        time_between_stations=[60.0, 120.0],
        schedule={'headway': 200, 'service_hours': (6, 22), 'capacity': 1000},
        fleet_size=4,
        bidirectional=True
    )
    
    network.add_line(line_t1)
    
    gen_central = CustomerGenerator(
        allocator=allocator,
        station_id="central",
        arrival_rate_profile=peaky_arrival_rate,
        seed=42
    )
    
    gen_redfern = CustomerGenerator(
        allocator=allocator,
        station_id="redfern",
        arrival_rate_profile=peaky_arrival_rate,
        seed=43
    )
    
    sim = SimulationLoop(
        memmap_allocator=allocator,
        map_network=network,
        dt=1.0,
        snapshot_interval=3600,
        log_level=logging.ERROR
    )
    
    sim.current_time = 6 * 3600.0
    sim.add_customer_generator(gen_central)
    sim.add_customer_generator(gen_redfern)
    
    return sim

def run_profile(n_ticks=360):
    """Profile simulation for n_ticks"""
    sim = setup_sim()
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    sim.run(n_ticks=n_ticks)
    
    profiler.disable()
    
    # Print sorted by cumulative time
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    print(s.getvalue())
    
    # Also sort by time in function (not cumulative)
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('time')
    ps.print_stats(30)
    print("\n=== By Total Time (not cumulative) ===")
    print(s.getvalue())

if __name__ == "__main__":
    print("Profiling simulation for 360 ticks...")
    run_profile(n_ticks=360)
