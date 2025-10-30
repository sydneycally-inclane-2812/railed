from typing import List, Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class TrainSpawn:
    """Represents a train spawn event"""
    train_id: int
    line_id: str
    direction: int
    depart_time: float
    timetable: List[tuple]
    max_capacity: int

class TrainGenerator:
    """Manages train spawning for a line"""
    
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
        self.next_spawn_times: List[float] = []
        self.train_id_counter = 0
    
    def tick(self, current_time: float) -> List[TrainSpawn]:
        """Determine if new trains should spawn"""
        spawns = []
        
        # Check service hours
        hour = (current_time / 3600) % 24
        service_start, service_end = self.schedule_policy.get('service_hours', (0, 24))
        
        if hour < service_start or hour >= service_end:
            return spawns
        
        # Check headway-based spawning
        headway = self.schedule_policy.get('headway', 600)  # seconds
        
        # Simple spawning: check if we need more trains
        if len(self.active_trains) < self.fleet_size:
            # Check if enough time since last spawn
            if not self.next_spawn_times or current_time >= self.next_spawn_times[0]:
                # Create spawn event
                train_id = self.allocate_train()
                if train_id is not None:
                    spawn = self._create_spawn_event(train_id, current_time)
                    spawns.append(spawn)
                    
                    # Schedule next spawn
                    if self.next_spawn_times:
                        self.next_spawn_times.pop(0)
                    self.next_spawn_times.append(current_time + headway)
        
        return spawns
    
    def allocate_train(self) -> Optional[int]:
        """Get train ID from pool or create new"""
        if self.idle_pool:
            train_id = self.idle_pool.pop()
            self.active_trains.add(train_id)
            return train_id
        
        if len(self.active_trains) < self.fleet_size:
            train_id = self._create_train_id()
            self.active_trains.add(train_id)
            return train_id
        
        return None
    
    def release_train(self, train_id: int):
        """Return train to idle pool"""
        self.active_trains.discard(train_id)
        self.idle_pool.append(train_id)
    
    def handle_direction_change(self, train_id: int):
        """Manage direction reversal at terminal"""
        # Typically handled by Train.reverse_direction()
        pass
    
    def _create_train_id(self) -> int:
        """Generate unique train ID"""
        self.train_id_counter += 1
        return int(f"{hash(self.line_id) % 1000}{self.train_id_counter:04d}")
    
    def _create_spawn_event(self, train_id: int, current_time: float) -> TrainSpawn:
        """Create spawn event with timetable"""
        # Simplified: create basic timetable
        # In real implementation, use Line.timetable
        return TrainSpawn(
            train_id=train_id,
            line_id=self.line_id,
            direction=1,
            depart_time=current_time,
            timetable=[],  # To be filled by Line
            max_capacity=self.schedule_policy.get('capacity', 1000)
        )
