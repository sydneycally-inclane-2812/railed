from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from .logger import get_logger

logger = get_logger()

@dataclass
class TrainMake:
    """Represents a train make event"""
    train_id: int
    line_id: str
    direction: int
    depart_time: float
    timetable: List[tuple]
    max_capacity: int

class TrainGenerator:
    """Manages train making for a line"""
    
    def __init__(
        self,
        line_id: str,
        fleet_size: int,
        schedule_policy: Dict,  # {'headway': 300, 'service_hours': (5, 23)}
    ):
        self.line_id = line_id
        self.fleet_size = fleet_size
        self.schedule_policy = schedule_policy

        self.active_trains: Set[int] = set()
        self.idle_pool: List[int] = []
        self.train_id_counter = 0

        # Track last departure time for each direction
        self.last_departure_time = {1: -float('inf'), -1: -float('inf')}

        logger.info(f"TrainGenerator for line {line_id}: fleet_size={fleet_size}, "
                   f"headway={schedule_policy.get('headway', 600)}s, "
                   f"service_hours={schedule_policy.get('service_hours', (0, 24))}")
    
    def tick(self, current_time: float) -> List[TrainMake]:
        """Determine if new trains should be made, enforcing headway for both directions."""
        makes = []

        # Check service hours
        hour = (current_time / 3600) % 24
        service_start, service_end = self.schedule_policy.get('service_hours', (0, 24))

        if hour < service_start or hour >= service_end:
            logger.debug(f"Line {self.line_id}: Outside service hours (hour={hour:.1f}, service={service_start}-{service_end})")
            return makes

        headway = self.schedule_policy.get('headway', 600)  # seconds

        # Try to make a train in each direction, if enough time has passed since last departure
        for direction in [1, -1]:
            if len(self.active_trains) < self.fleet_size:
                if current_time - self.last_departure_time[direction] >= headway:
                    train_id = self.allocate_train()
                    if train_id is not None:
                        make = self._create_make_event(train_id, current_time, direction)
                        makes.append(make)
                        self.last_departure_time[direction] = current_time
                        logger.info(f"Line {self.line_id}: Making train {train_id} at time {current_time:.1f} direction {direction} "
                                    f"(active: {len(self.active_trains)}/{self.fleet_size})")
        return makes
    
    def allocate_train(self) -> Optional[int]:
        """Get train ID from pool or create new"""
        if self.idle_pool:
            train_id = self.idle_pool.pop()
            self.active_trains.add(train_id)
            logger.debug(f"Line {self.line_id}: Allocated train {train_id} from idle pool")
            return train_id
        
        if len(self.active_trains) < self.fleet_size:
            train_id = self._create_train_id()
            self.active_trains.add(train_id)
            logger.debug(f"Line {self.line_id}: Created new train {train_id}")
            return train_id
        
        logger.warning(f"Line {self.line_id}: Cannot allocate train, fleet at capacity ({self.fleet_size})")
        return None
    
    def release_train(self, train_id: int):
        """Return train to idle pool"""
        self.active_trains.discard(train_id)
        self.idle_pool.append(train_id)
        logger.info(f"Line {self.line_id}: Train {train_id} released to idle pool "
                   f"(active: {len(self.active_trains)}, idle: {len(self.idle_pool)})")
    
    def handle_direction_change(self, train_id: int):
        """Manage direction reversal at terminal"""
        # Typically handled by Train.reverse_direction()
        pass
    
    def _create_train_id(self) -> int:
        """Generate unique train ID"""
        self.train_id_counter += 1
        return int(f"{hash(self.line_id) % 1000}{self.train_id_counter:04d}")
    
    def _create_make_event(self, train_id: int, current_time: float, direction: int = 1) -> TrainMake:
        """Create make event with timetable and direction"""
        return TrainMake(
            train_id=train_id,
            line_id=self.line_id,
            direction=direction,
            depart_time=current_time,
            timetable=[],  # To be filled by Line
            max_capacity=self.schedule_policy.get('capacity', 1000)
        )
