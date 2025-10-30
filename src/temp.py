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


# ============================================================================
# Rolling Stock Classes
# ============================================================================

class TrainState(Enum):
    """Train operational state."""
    AT_STATION = "at_station"
    IN_TRANSIT = "in_transit"


class Train:
    """Train operating on a line."""
    def __init__(self, train_id: str, line: str, capacity: int, schedule: Optional[List[float]] = None):
        self.id = train_id
        self.line = line  # line ID this train operates on
        self.capacity = capacity
        self.schedule = schedule or []  # departure times from first station (minutes)
        self.onboard: List[int] = []  # passenger IDs currently on train
        self.state = TrainState.AT_STATION
        self.current_station: Optional[str] = None
        self.next_station: Optional[str] = None
        self.arrival_time: Optional[float] = None  # when arriving at next station

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

    def alight_passengers(self, station_id: str, passengers: Dict[int, Passenger]) -> List[int]:
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


# ============================================================================
# Demand & Schedule Classes
# ============================================================================

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


# ============================================================================
# Network Classes
# ============================================================================

class Network:
    """Rail network graph with stations and lines."""
    def __init__(self, transfer_time: float = 2.0):
        self.stations: Dict[str, Station] = {}
        self.lines: Dict[str, Line] = {}
        self.default_transfer_time = transfer_time

    def add_station(self, station_id: str, transfer_time: Optional[float] = None):
        """Add a station to the network."""
        if station_id not in self.stations:
            tt = transfer_time if transfer_time is not None else self.default_transfer_time
            self.stations[station_id] = Station(station_id, transfer_time=tt)

    def add_line(self, line: Line):
        """Add a line and auto-create stations."""
        self.lines[line.name] = line
        # Auto-create stations from line definition
        for station_id in line.stops:
            self.add_station(station_id)
            self.stations[station_id].add_line(line.name)

    def get_station(self, station_id: str) -> Optional[Station]:
        """Get station by ID."""
        return self.stations.get(station_id)

    def get_line(self, line_id: str) -> Optional[Line]:
        """Get line by ID."""
        return self.lines.get(line_id)

    def find_route(self, origin: str, destination: str) -> Optional[List[tuple]]:
        """
        Find route between stations.
        Returns list of (line_id, from_station, to_station) tuples.
        Simple implementation: direct line or one transfer.
        """
        # Direct line
        for line in self.lines.values():
            if origin in line.stops and destination in line.stops:
                orig_idx = line.stops.index(origin)
                dest_idx = line.stops.index(destination)
                if orig_idx < dest_idx:
                    return [(line.name, origin, destination)]
        # One-transfer
        for line1 in self.lines.values():
            if origin not in line1.stops:
                continue
            for transfer_station in line1.stops:
                if transfer_station == origin:
                    continue
                for line2 in self.lines.values():
                    if line2.name == line1.name:
                        continue
                    if transfer_station in line2.stops and destination in line2.stops:
                        orig_idx = line1.stops.index(origin)
                        transfer_idx = line1.stops.index(transfer_station)
                        transfer_idx2 = line2.stops.index(transfer_station)
                        dest_idx = line2.stops.index(destination)
                        if orig_idx < transfer_idx and transfer_idx2 < dest_idx:
                            return [
                                (line1.name, origin, transfer_station),
                                (line2.name, transfer_station, destination),
                            ]
        return None  # No route found