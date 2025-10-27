from dataclasses import dataclass, field
from typing import Optional, List, Set

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