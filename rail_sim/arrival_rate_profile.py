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

def random_peak_hour(
    peak_hour: float,
    spread: float = 1.0,
    period: int = 24,
    random_seed: int = None
):
    """
    Returns a function that samples a random hour of the day,
    with higher probability near the specified peak_hour using a Gaussian distribution.

    Args:
        peak_hour: hour of the day with highest probability (e.g., 8 for 8am)
        spread: standard deviation of the peak in hours
        period: number of hours in a cycle (default 24)
        random_seed: for reproducibility

    Returns:
        sample_hour(): function that returns a random hour (float, 0 <= hour < period)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    def sample_hour():
        hour = np.random.normal(loc=peak_hour, scale=spread)
        hour = hour % period
        return hour

    return sample_hour


def random_multi_peak_hour(
    peak_hours: list,
    spreads: list = None,
    weights: list = None,
    period: int = 24,
    random_seed: int = None
):
    """
    Returns a function that samples a random hour of the day using np.random.normal,
    with higher probability near multiple specified peak_hours (mixture of Gaussians).

    Args:
        peak_hours: list of hours (e.g., [8, 17]) for peaks
        spreads: list of std deviations for each peak (default 1.0 for all)
        weights: list of weights for each peak (default equal for all)
        period: number of hours in a cycle (default 24)
        random_seed: for reproducibility

    Returns:
        sample_hour(): function that returns a random hour (float, 0 <= hour < period)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n_peaks = len(peak_hours)
    if spreads is None:
        spreads = [1.0] * n_peaks
    if weights is None:
        weights = [1.0] * n_peaks
    weights = np.array(weights) / np.sum(weights)  # Normalize weights

    def sample_hour():
        # Choose which peak to sample from
        peak_idx = np.random.choice(n_peaks, p=weights)
        hour = np.random.normal(loc=peak_hours[peak_idx], scale=spreads[peak_idx])
        # Wrap around the period (e.g., 24 hours)
        hour = hour % period
        return hour

    return sample_hour

# Example usage:
if __name__ == "__main__":
    sampler = random_multi_peak_hour(peak_hours=[8, 17], spreads=[1.5, 2.0], weights=[1, 0.8])
    samples = [sampler() for _ in range(10000)]
    import matplotlib.pyplot as plt
    plt.hist(samples, bins=24, range=(0,24), density=True, alpha=0.7)
    plt.xlabel("Hour of Day")
    plt.ylabel("Probability Density")
    plt.title("Random Sampling  with Peaks at 8am & 5pm")
    plt.show()
