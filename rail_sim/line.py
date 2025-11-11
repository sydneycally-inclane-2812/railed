from typing import List, Dict, Optional
from .train_gen import TrainGenerator
from .logger import get_logger

logger = get_logger()

class Line:
    """Represents a railway line"""
    
    def __init__(
        self,
        line_id: str,
        line_code: str,
        station_list: List[int],
        time_between_stations: List[float],
        schedule: Dict,
        fleet_size: int,
        bidirectional: bool = True
    ):
        self.line_id = line_id
        self.line_code = line_code
        self.station_list = station_list
        self.time_between_stations = time_between_stations
        self.schedule = schedule
        self.fleet_size = fleet_size
        self.bidirectional = bidirectional
        
        # Create train generator
        self.train_generator = TrainGenerator(line_id, fleet_size, schedule)
    
    def get_next_station(self, current_station_id: int, direction: int) -> Optional[int]:
        """Get next station along route"""
        try:
            idx = self.station_list.index(current_station_id)
            next_idx = idx + direction
            
            if 0 <= next_idx < len(self.station_list):
                return self.station_list[next_idx]
        except ValueError:
            pass
        
        return None
    
    def get_travel_time(self, from_id: int, to_id: int) -> Optional[float]:
        """Get travel time between stations"""
        try:
            from_idx = self.station_list.index(from_id)
            to_idx = self.station_list.index(to_id)
            
            if abs(to_idx - from_idx) == 1:
                idx = min(from_idx, to_idx)
                return self.time_between_stations[idx]
        except (ValueError, IndexError):
            pass
        
        return None
    
    def update_fleet(self, new_size: int):
        """Adjust fleet size"""
        self.fleet_size = new_size
        self.train_generator.fleet_size = new_size
    
    def notify_disruption(self, event: Dict):
        """Handle disruption events"""
        # Propagate to train generator
        pass
    
    def build_timetable(self, start_time: float, direction: int = 1) -> List[tuple]:
        """Build timetable for a train run"""
        timetable = []
        current_time = start_time
        
        stations = self.station_list if direction == 1 else list(reversed(self.station_list))
        times = self.time_between_stations if direction == 1 else list(reversed(self.time_between_stations))
        
        # First station
        timetable.append((current_time, stations[0]))
        
        # Subsequent stations
        for i, travel_time in enumerate(times):
            current_time += travel_time
            timetable.append((current_time, stations[i + 1]))
        
        logger.debug(f"Line {self.line_code}: Built timetable with {len(timetable)} stops, "
                    f"direction={direction}, total_time={current_time - start_time:.1f}s")
        
        return timetable
