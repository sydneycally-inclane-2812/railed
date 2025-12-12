"""
Test case: Simple simulation
- 3 stops
- Constant user rate
- in-memory allocator
- customer coming to only 2 stations.
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
        schedule={'headway': 200, 'service_hours': (6, 22), 'capacity': 1000},
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
    
    # 7. Run simulation for 30 days, collect daily average waiting times
    print(f"Starting simulation at time {sim.current_time} (hour {sim.current_time/3600})")
    print(f"Service hours: {line_t1.train_generator.schedule_policy['service_hours']}")

    n_days = 30
    seconds_per_day = 24 * 3600
    daily_waiting_times = []

    for day in range(n_days):
        print(f"\n=== Running simulation for day {day+1} ===")
        sim.run(n_ticks=seconds_per_day)
        # Assume sim.metrics_history[-1] contains 'avg_waiting_time' (adjust if needed)
        metrics = sim.metrics_history[-1]
        avg_wait = metrics.get('avg_waiting_time', None)
        if avg_wait is not None:
            daily_waiting_times.append(avg_wait)
        else:
            print("Warning: 'avg_waiting_time' not found in metrics.")

    print("\nSimulation complete!")
    print(f"Daily average waiting times: {daily_waiting_times}")

    # Bootstrap sampling on daily average waiting times
    if daily_waiting_times:
        # Custom bootstrap implementation
        n_samples = 30
        stats_arr = []
        n = len(daily_waiting_times)
        orig_stat = np.mean(daily_waiting_times)
        for _ in range(n_samples):
            sample = np.random.choice(daily_waiting_times, size=n, replace=True)
            stats_arr.append(np.mean(sample))
        stats_arr = np.array(stats_arr)
        boot_mean = np.mean(stats_arr)
        bias = boot_mean - orig_stat
        std_err = np.std(stats_arr)
        ci = 95
        lower = np.percentile(stats_arr, (100 - ci) / 2)
        upper = np.percentile(stats_arr, 100 - (100 - ci) / 2)
        print(f"\nBootstrap mean: {boot_mean:.3f}")
        print(f"Bootstrap bias: {bias:.3f}")
        print(f"Bootstrap std error: {std_err:.3f}")
        print(f"Bootstrap 95% CI: {lower:.3f} - {upper:.3f}")

if __name__ == "__main__":
    main()
    
#test