import numpy as np
from functools import wraps

def precalculate(
    *,
    period: int = 86400,
    resolution: int = 60,
    method: str = "interp",
):
    """
    Decorator that pre-computes arrival rate function evaluations for fast lookup.

    Args:
        period: Cycle period in seconds (default: 86400 = 24h)
        resolution: Sampling interval in seconds
        method: "interp" (linear interpolation) or "staircase" (fixed-second bucket)

    Methods:
        - interp (default): pre-sample every ``resolution`` seconds and linearly interpolate.
        - staircase: pre-sample every ``resolution`` seconds and return floor bucket.
    """
    method = method.lower()
    if method not in {"interp", "staircase"}:
        raise ValueError("method must be one of: interp, staircase")

    def decorator(func):
        # Precompute once
        time_points = np.arange(0, period, resolution, dtype=np.int64)
        rate_values = np.array([func(t) for t in time_points])
        n = len(rate_values)

        @wraps(func)
        def wrapper(t):
            # Work in integers for indexing; final result may still be float from rates
            t_mod_int = int(t) % period
            idx = (t_mod_int // resolution) % n

            if method == "staircase":
                return rate_values[idx]

            # Simple linear interpolation without np.interp
            next_idx = (idx + 1) % n
            offset = t_mod_int - idx * resolution  # 0 <= offset < resolution
            frac = offset / resolution
            start = rate_values[idx]
            end = rate_values[next_idx]
            return start + (end - start) * frac

        wrapper._original_func = func
        wrapper._cached = True
        wrapper._period = period
        wrapper._resolution = resolution
        wrapper._cache_size = n
        wrapper._mode = method
        return wrapper

    return decorator

def constant_arrival(rate: float):
    """
    Returns a function that always returns the same arrival rate.
    """
    def profile(t: float) -> float:
        return rate
    return profile

def daily_peak_arrival(base: float, peak: float, peak_hour: float, spread: float):
    """
    Returns a function that models a daily peak using a Gaussian distribution.
    - base: minimum arrival rate
    - peak: maximum additional arrival rate at the peak
    - peak_hour: hour of the day when the peak occurs (e.g., 8 for 8am)
    - spread: standard deviation of the peak in hours
    """
    def profile(t: float) -> float:
        hour = (t / 3600) % 24
        # Gaussian peak
        peak_value = peak * np.exp(-0.5 * ((hour - peak_hour) / spread) ** 2)
        return base + peak_value
    return profile
