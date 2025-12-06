import sys
import numpy as np
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from time import time
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


from rail_sim import (
    MemmapAllocator,
    MemoryAllocator,
    CustomerGenerator,
    Station,
    Line,
    Map,
    SimulationLoop,
	precalculate,
)

def timeit(func):
    # This function shows the execution time of 
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func

def peaky_arrival_rate_1(t):
    scale = 10
    morn_aft_scale = 4
    min = 4
    
    power = -1/morn_aft_scale
    f = lambda x: scale * np.clip(x, 1e-6, None) ** power * np.abs(np.sin(x)) + min  # avoid 0**negative
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 

@precalculate(method="interp", resolution=5000)
def peaky_arrival_rate_2(t):
    scale = 10
    morn_aft_scale = 4
    min = 4
    
    power = -1/morn_aft_scale
    f = lambda x: scale * np.clip(x, 1e-6, None) ** power * np.abs(np.sin(x)) + min  # avoid 0**negative
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 

@precalculate(method="staircase", resolution=5000)
def peaky_arrival_rate_3(t):
    scale = 10
    morn_aft_scale = 4
    min = 4
    
    power = -1/morn_aft_scale
    f = lambda x: scale * np.clip(x, 1e-6, None) ** power * np.abs(np.sin(x)) + min  # avoid 0**negative
    time_of_day = (t % 86400) / 86400  # seconds in a day
    return f(time_of_day * np.pi * 2) # scale it to 2pi for 2 peaks a day 



def plot_profiles():
    """Plot original vs precalculated arrival rates over 24h."""
    # Sample one full day
    t = np.linspace(0, 86400, 2000)
    f_orig = np.vectorize(peaky_arrival_rate_1)(t)
    f_cached = np.vectorize(peaky_arrival_rate_2)(t)
    f_cached_2 = np.vectorize(peaky_arrival_rate_3)(t)

    plt.figure(figsize=(10, 6))
    plt.plot(t / 3600, f_orig, label="original", linewidth=2)
    plt.plot(t / 3600, f_cached, label="precalculate", linewidth=1.6, linestyle="--")
    plt.plot(t / 3600, f_cached_2, label="precalculate_staircase", linewidth=1.6, linestyle="-.")
    plt.xlabel("Hour of day")
    plt.ylabel("Arrival rate")
    plt.title("Arrival rate profile: original vs precalculated")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_profiles()