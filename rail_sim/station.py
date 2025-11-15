import numpy as np
from typing import List, Dict, Optional, Set
from .logger import get_logger

logger = get_logger()

class Station:
    """Represents a railway station"""
    
    def __init__(
        self,
        station_id: int,
        name: str,
        line_codes: List[str],
        avg_change_time: float = 60.0,
        theoretical_capacity: int = 5000,
        maximum_capacity: int = 10000
    ):
        self.station_id = station_id
        self.name = name
        self.line_codes = line_codes
        self.avg_change_time = avg_change_time
        self.theoretical_capacity = theoretical_capacity
        self.maximum_capacity = maximum_capacity
        
        # Track waiting passengers
        self.waiting_passengers: List[int] = []  # customer indices
        
        # Optional: platform tracking
        self.platforms: Dict[int, List[int]] = {}  # platform_id -> [train_ids]
        
        logger.info(f"Station {station_id} ({name}) initialized: lines={line_codes}, capacity={theoretical_capacity}")
    
    def enqueue_passenger(self, customer_idx: int):
        """Add passenger to waiting queue"""
        self.waiting_passengers.append(customer_idx)
        logger.debug(f"Station {self.name}: Passenger {customer_idx} added to queue (total waiting: {len(self.waiting_passengers)})")
        
        if len(self.waiting_passengers) > self.theoretical_capacity:
            logger.warning(f"Station {self.name}: Queue size {len(self.waiting_passengers)} exceeds theoretical capacity {self.theoretical_capacity}")
    
    def dequeue_for_boarding(
        self, 
        train, 
        memmap,
        path_table
    ) -> np.ndarray:
        """
        Select passengers to board a train
        Filter by path/line compatibility
        """
        if not self.waiting_passengers:
            logger.debug(f"Station {self.name}: No waiting passengers for train {train.id}")
            return np.array([], dtype=np.int64)
        
        waiting_arr = np.array(self.waiting_passengers, dtype=np.int64)
        
        logger.debug(f"Station {self.name}: Checking {len(waiting_arr)} passengers for train {train.id} (line {train.line_id})")
   
        # Filter passengers whose path includes this train's line
        eligible = []
        for idx in waiting_arr:
            path_id = memmap[idx]['path_id']
            if path_id == 0:
                logger.debug(f"Station {self.name}: Passenger {idx} has no path assigned")
                continue
            
            segments = path_table.expand(path_id)
            if segments:
                # Check if any segment uses this train's line
                for line_code, from_id, to_id in segments:
                    if line_code == train.line_id and from_id == self.station_id:
                        eligible.append(idx)
                        break
        
        eligible_arr = np.array(eligible, dtype=np.int64)
        
        logger.info(f"Station {self.name}: {len(eligible_arr)} passengers eligible for train {train.id} out of {len(waiting_arr)} waiting")
        
        # Remove from waiting list
        remaining = set(self.waiting_passengers) - set(eligible)
        self.waiting_passengers = list(remaining)
        
        logger.debug(f"Station {self.name}: {len(self.waiting_passengers)} passengers remain in queue")
        
        return eligible_arr
    
    def update_capacity(self) -> int:
        """Return current occupancy"""
        return len(self.waiting_passengers)
    
    def transfer_passenger(self, customer_idx: int, next_line: str, memmap):
        """Handle passenger transfer"""
        memmap[customer_idx]['state'] = 3  # transferring
        memmap[customer_idx]['current_station_id'] = self.station_id
        # Add to waiting queue
        self.enqueue_passenger(customer_idx)
        logger.info(f"Station {self.name}: Passenger {customer_idx} transferring to line {next_line}")
