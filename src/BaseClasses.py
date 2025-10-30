from dataclasses import dataclass, field
from typing import Optional, List, Set, Callable, Dict, Deque
from collections import deque
from enum import Enum


# ============================================================================
# Passenger Classes
# ============================================================================

@dataclass
class Passenger:
    """Individual passenger with journey tracking."""
    id: int
    origin_id: str
    dest_id: str
    speed_mps: float = 1.4  # meters per second, reflects mobility
    created_at: float = 0.0  # when generated (minutes)
    queued_at: Optional[float] = None  # when joined station queue
    boarded_at: Optional[float] = None  # when entered train
    alighted_at: Optional[float] = None  # when exited train
    tags: Set[str] = field(default_factory=set)  # e.g., {"wheelchair"}
    notes: Optional[str] = None
    current_line: Optional[str] = None  # which line queue they're in
    route: List[str] = field(default_factory=list)  # planned station path

    @property
    def wait_time(self) -> Optional[float]:
        """Time spent waiting at platform (minutes)."""
        if self.boarded_at is None or self.queued_at is None:
            return None
        return self.boarded_at - self.queued_at

    @property
    def in_vehicle_time(self) -> Optional[float]:
        """Time spent on train (minutes)."""
        if self.alighted_at is None or self.boarded_at is None:
            return None
        return self.alighted_at - self.boarded_at

    @property
    def total_journey_time(self) -> Optional[float]:
        """Total time from creation to arrival (minutes)."""
        if self.alighted_at is None:
            return None
        return self.alighted_at - self.created_at
    
           


@dataclass
class PassengerProfile:
    """Defines characteristics for a passenger type."""
    name: str = "default"
    speed_mps: float = 1.4  # walking speed
    boarding_time: float = 2.0  # seconds to board
    proportion: float = 1.0  # proportion of total passengers


# ============================================================================
# Infrastructure Classes
# ============================================================================

class Station:
    """Station with passenger queues."""
    def __init__(self, station_id: str, transfer_time: float = 2.0):
        self.id = station_id
        self.transfer_time = transfer_time  # minutes to transfer between lines
        # Queue per line at this station
        self.queues: Dict[str, Deque[int]] = {}  # line_id -> deque of passenger_ids
        self.lines: Set[str] = set()  # which lines stop here

    def add_line(self, line_id: str):
        """Register a line that stops at this station."""
        self.lines.add(line_id)
        if line_id not in self.queues:
            self.queues[line_id] = deque()

    def add_passenger_to_queue(self, passenger_id: int, line_id: str):
        """Add passenger to queue for specific line."""
        if line_id not in self.queues:
            self.queues[line_id] = deque()
        self.queues[line_id].append(passenger_id)

    def pop_for_boarding(self, line_id: str, max_n: int) -> List[int]:
        """Pop up to max_n passengers FIFO from the queue for a line."""
        q = self.queues.get(line_id)
        if not q:
            return []
        out = []
        for _ in range(min(max_n, len(q))):
            out.append(q.popleft())
        return out

    def get_queue_length(self, line_id: str) -> int:
        """Get number of passengers waiting for a line."""
        q = self.queues.get(line_id)
        return len(q) if q is not None else 0

    def is_transfer_station(self) -> bool:
        """Check if this is a transfer point between lines."""
        return len(self.lines) > 1


class Line:
    """Train line with stops and travel times."""
    def __init__(self, name: str, stops: List[str], travel_times: List[float], fleet_size: int = 0):
        self.name = name
        self.stops = stops  # ordered list of station IDs
        self.fleet_size = fleet_size  # optional: number of trains assigned to this line
        if len(travel_times) != len(stops) - 1:
            raise ValueError(
                f"Line {name}: need {len(stops)-1} travel times for {len(stops)} stops"
            )
        self.travel_times = travel_times  # minutes between consecutive stops

    def get_travel_time(self, from_station: str, to_station: str) -> Optional[float]:
        """Get travel time between two stations on this line (forward direction)."""
        try:
            from_idx = self.stops.index(from_station)
            to_idx = self.stops.index(to_station)
            if from_idx >= to_idx:
                return None  # wrong direction or same station
            return sum(self.travel_times[from_idx:to_idx])
        except (ValueError, IndexError):
            return None

    def get_next_stop(self, current_station: str) -> Optional[str]:
        """Get the next station after current one."""
        try:
            idx = self.stops.index(current_station)
            if idx < len(self.stops) - 1:
                return self.stops[idx + 1]
        except ValueError:
            pass
        return None

    def get_stop_index(self, station: str) -> Optional[int]:
        """Get index of station in stops list."""
        try:
            return self.stops.index(station)
        except ValueError:
            return None

