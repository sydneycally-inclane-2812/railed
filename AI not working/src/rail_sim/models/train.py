from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class TrainState(Enum):
    """Train operational state."""
    AT_STATION = "at_station"
    IN_TRANSIT = "in_transit"

@dataclass
class Train:
    """Train operating on a line."""
    train_id: str
    line: str  # line ID this train operates on
    capacity: int
    schedule: Optional[List[float]] = None  # departure times from first station (minutes)
    onboard: List[int] = None  # passenger IDs currently on train
    state: TrainState = TrainState.AT_STATION
    current_station: Optional[str] = None
    next_station: Optional[str] = None
    arrival_time: Optional[float] = None  # when arriving at next station

    def __post_init__(self):
        if self.onboard is None:
            self.onboard = []

    @property
    def occupancy(self) -> int:
        """Current number of passengers."""
        return len(self.onboard)

    @property
    def occupancy_rate(self) -> float:
        """Occupancy as percentage of capacity."""
        return (self.occupancy / self.capacity * 100) if self.capacity > 0 else 0.0

    @property
    def available_capacity(self) -> int:
        """Remaining space on train."""
        return max(0, self.capacity - self.occupancy)

    def board_passengers(self, passenger_ids: List[int]) -> List[int]:
        """Board passengers up to capacity. Returns list of boarded passenger IDs."""
        space = self.available_capacity
        to_board = passenger_ids[:space]
        if to_board:
            self.onboard.extend(to_board)
        return to_board

    def alight_passengers(self, station_id: str, passengers: dict) -> List[int]:
        """Remove passengers whose destination is this station; return list of alighting IDs."""
        alighting = []
        remaining = []
        for pid in self.onboard:
            if passengers[pid].dest_id == station_id:
                alighting.append(pid)
            else:
                remaining.append(pid)
        self.onboard = remaining
        return alighting

    def move_to_next_station(self, next_station: str):
        """Move the train to the next station."""
        self.current_station = next_station
        self.state = TrainState.IN_TRANSIT

    def reverse_direction(self):
        """Reverse the direction of the train."""
        # Logic to reverse direction can be implemented here
        pass