from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class PassengerDemand:
    """Defines passenger demand between two stations."""
    origin: str
    destination: str
    rate: Callable[[float], float]  # function: time -> passengers per hour
    pattern: Optional[str] = None  # optional preset pattern name

    def get_demand(self, time: float) -> float:
        """Get passenger arrival rate at given time (passengers/hour)."""
        if self.pattern:
            return self._get_pattern_demand(time)
        return self.rate(time)

    def _get_pattern_demand(self, time: float) -> float:
        """Get demand from preset pattern."""
        patterns = {
            "rush_hour": lambda t: 100 if (7 <= t < 9 or 17 <= t < 19) else 20,
            "constant": lambda t: 50,
            "evening_peak": lambda t: 80 if 17 <= t < 20 else 30,
        }
        if self.pattern in patterns:
            return patterns[self.pattern](time)
        return self.rate(time)