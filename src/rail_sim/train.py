import numpy as np
from typing import List, Tuple, Optional

class Train:
    """Represents a train moving along a line"""
    
    def __init__(
        self,
        train_id: int,
        line_id: str,
        timetable: List[Tuple[float, int]],  # [(arrival_time, station_id), ...]
        max_capacity: int,
        direction: int = 1,
        status: str = 'in_service'
    ):
        self.id = train_id
        self.line_id = line_id
        self.timetable = timetable
        self.max_capacity = max_capacity
        self.current_capacity = 0
        self.onboard_passengers: List[int] = []  # customer indices
        self.direction = direction  # 1 or -1
        self.status = status  # in_service, idle, out_of_service
        
        # Position tracking
        self.timetable_idx = 0
        self.current_station_id: Optional[int] = None
        self.next_station_id: Optional[int] = None
        self.dwell_remaining = 0.0
        self.position_ratio = 0.0  # 0-1 between stations
        
        if timetable:
            self.current_station_id = timetable[0][1]
            if len(timetable) > 1:
                self.next_station_id = timetable[1][1]
    
    def step(self, dt: float, current_time: float) -> bool:
        """
        Advance train along timetable
        Returns True if train arrived at a station
        """
        if self.status != 'in_service' or not self.timetable:
            return False
        
        # Check if dwelling at station
        if self.dwell_remaining > 0:
            self.dwell_remaining -= dt
            if self.dwell_remaining <= 0:
                self.dwell_remaining = 0
            return False
        
        # Check if at terminal
        if self.timetable_idx >= len(self.timetable) - 1:
            return False
        
        # Get current and next station times
        current_arrival, current_station = self.timetable[self.timetable_idx]
        next_arrival, next_station = self.timetable[self.timetable_idx + 1]
        
        # Check if we've arrived at next station
        if current_time >= next_arrival:
            self.current_station_id = next_station
            self.timetable_idx += 1
            
            # Set next station if not at end
            if self.timetable_idx < len(self.timetable) - 1:
                self.next_station_id = self.timetable[self.timetable_idx + 1][1]
            else:
                self.next_station_id = None
            
            # Start dwelling
            self.dwell_remaining = 30.0  # 30 second dwell time
            self.position_ratio = 0.0
            
            return True  # Arrived at station
        
        # Update position between stations
        if next_arrival > current_arrival:
            self.position_ratio = (current_time - current_arrival) / (next_arrival - current_arrival)
        
        return False
    
    def board(self, passenger_indices: np.ndarray, memmap) -> np.ndarray:
        """
        Board passengers if capacity allows
        Returns array of boarded passenger indices
        """
        available_capacity = self.max_capacity - self.current_capacity
        can_board = min(len(passenger_indices), available_capacity)
        
        if can_board <= 0:
            return np.array([], dtype=np.int64)
        
        boarded = passenger_indices[:can_board]
        
        # Add to onboard list
        self.onboard_passengers.extend(boarded.tolist())
        self.current_capacity += can_board
        
        # Update memmap
        memmap[boarded]['on_train_id'] = self.id
        memmap[boarded]['state'] = 1  # onboard
        
        return boarded
    
    def alight(self, memmap) -> np.ndarray:
        """
        Remove passengers whose destination is current station
        Returns array of alighted passenger indices
        """
        if not self.onboard_passengers or self.current_station_id is None:
            return np.array([], dtype=np.int64)
        
        onboard_arr = np.array(self.onboard_passengers, dtype=np.int64)
        
        # Find passengers whose destination matches current station
        destinations = memmap[onboard_arr]['dest_station_id']
        alight_mask = destinations == self.current_station_id
        alighting = onboard_arr[alight_mask]
        staying = onboard_arr[~alight_mask]
        
        # Update onboard list
        self.onboard_passengers = staying.tolist()
        self.current_capacity = len(self.onboard_passengers)
        
        # Update memmap
        if len(alighting) > 0:
            memmap[alighting]['on_train_id'] = 0
            memmap[alighting]['state'] = 2  # arrived
            memmap[alighting]['current_station_id'] = self.current_station_id
        
        return alighting
    
    def reverse_direction(self):
        """Flip direction and reset timetable pointer"""
        self.direction *= -1
        self.timetable_idx = 0
        # Reverse timetable
        self.timetable = list(reversed(self.timetable))
        if self.timetable:
            self.current_station_id = self.timetable[0][1]
            if len(self.timetable) > 1:
                self.next_station_id = self.timetable[1][1]
