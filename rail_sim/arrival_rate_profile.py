import numpy as np

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
