from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class TrainSchedule:
    """Defines when trains run on a line."""
    line: str
    capacity: int
    frequency: Optional[float] = None  # minutes between trains
    departures: Optional[List[float]] = None  # explicit departure times
    start_time: float = 0.0
    end_time: float = 120.0

    def get_departure_times(self) -> List[float]:
        """Generate list of departure times."""
        if self.departures:
            return sorted(self.departures)
        if self.frequency:
            times = []
            current = self.start_time
            while current <= self.end_time:
                times.append(current)
                current += self.frequency
            return times
        raise ValueError("Must specify either frequency or departures")

    def __post_init__(self):
        """Validate schedule parameters."""
        if self.frequency is None and self.departures is None:
            raise ValueError("Must specify either frequency or departures")
        if self.frequency is not None and self.departures is not None:
            raise ValueError("Cannot specify both frequency and departures")