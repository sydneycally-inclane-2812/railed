from typing import List, Dict, Optional, Union
from .train_gen import TrainGenerator
from .logger import get_logger

logger = get_logger()

class Line:
    def __init__(
        self,
        line_id: str,
        line_code: str,
        station_list: List[Union[str, int]],
        time_between_stations: List[float],
        schedule: Dict,
        fleet_size: int,
        bidirectional: bool = True
    ):
        self.line_id = line_id
        self.line_code = line_code
        # Store original station list (may be strings or ints)
        self.station_list_original = station_list
        # This will be converted to integers by Map.add_line
        self.station_list: List[int] = []
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
    
    def build_timetable(self, start_time: float, direction: int = 1, min_interval: float = 10.0) -> List[tuple]:
        """Build timetable for a train run, ensuring minimum interval between stops."""
        timetable = []
        current_time = start_time

        stations = self.station_list if direction == 1 else list(reversed(self.station_list))
        times = self.time_between_stations if direction == 1 else list(reversed(self.time_between_stations))

        # First station
        timetable.append((current_time, stations[0]))

        # Subsequent stations
        for i, travel_time in enumerate(times):
            # Use the greater of travel_time and min_interval to ensure movement
            interval = max(travel_time, min_interval)
            current_time += interval
            timetable.append((current_time, stations[i + 1]))

        logger.debug(f"Line {self.line_code}: Built timetable with {len(timetable)} stops, "
                    f"direction={direction}, total_time={current_time - start_time:.1f}s")

        return timetable

    def get_terminals_and_directions(self):
        """
        Return a list of (terminal_station_id, direction) pairs for both ends of the line.
        direction=1 means forward (start to end), direction=-1 means reverse (end to start).
        """
        if not self.station_list or len(self.station_list) < 2:
            return []
        return [
            (self.station_list[0], 1),    # Departures from first terminal, forward
            (self.station_list[-1], -1)   # Departures from last terminal, reverse
        ]
    """Represents a railway line"""