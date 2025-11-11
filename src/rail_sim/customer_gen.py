import numpy as np
from typing import Callable, Optional, List
from .memmap_schema import MemmapAllocator, CUSTOMER_DTYPE
from .logger import get_logger

logger = get_logger()

class CustomerGenerator:
    """Generates customers and writes to memmap"""
    
    def __init__(
        self, 
        allocator: MemmapAllocator,
        station_id: int,
        arrival_rate_profile: Callable[[float], float],
        seed: Optional[int] = None
    ):
        self.allocator = allocator
        self.station_id = station_id
        self.arrival_rate_profile = arrival_rate_profile
        self.rng = np.random.default_rng(seed)
        logger.info(f"CustomerGenerator initialized for station {station_id} with seed={seed}")
    
    def generate_customers(
        self, 
        t: float, 
        dt: float,
        possible_destinations: List[int]
    ) -> np.ndarray:
        """
        Generate new customers for this tick
        Returns array of customer indices
        """
        rate = self.arrival_rate_profile(t)
        # Poisson arrivals
        n_arrivals = self.rng.poisson(rate * dt)
        
        if n_arrivals == 0:
            logger.debug(f"Station {self.station_id}: No arrivals this tick (rate={rate:.2f})")
            return np.array([], dtype=np.int64)
        
        logger.debug(f"Station {self.station_id}: Generating {n_arrivals} customers (rate={rate:.2f}, dt={dt})")
        
        # Allocate indices
        indices = self.allocator.allocate_indices(n_arrivals)
        
        # Generate destinations
        dest_ids = self.rng.choice(possible_destinations, size=n_arrivals)
        
        # Write to memmap
        for i, idx in enumerate(indices):
            self.allocator.memmap[idx]['id'] = self.allocator.get_next_id()
            self.allocator.memmap[idx]['origin_station_id'] = self.station_id
            self.allocator.memmap[idx]['dest_station_id'] = dest_ids[i]
            self.allocator.memmap[idx]['current_station_id'] = self.station_id
            self.allocator.memmap[idx]['on_train_id'] = 0
            self.allocator.memmap[idx]['state'] = 0  # waiting
            self.allocator.memmap[idx]['spawn_ts'] = t
            self.allocator.memmap[idx]['tap_on_ts'] = 0
            self.allocator.memmap[idx]['tap_off_ts'] = 0
            self.allocator.memmap[idx]['path_id'] = 0  # To be assigned by Map
            self.allocator.memmap[idx]['total_wait_time'] = 0
            self.allocator.memmap[idx]['total_travel_time'] = 0
            self.allocator.memmap[idx]['movement_speed'] = self.rng.uniform(1.0, 1.5)
        
        logger.info(f"Station {self.station_id}: Created {n_arrivals} customers with indices {indices[:5]}{'...' if len(indices) > 5 else ''}")
        return indices
    
    def assign_path(self, customer_idx: int, path_id: int):
        """Assign a path to a customer"""
        self.allocator.memmap[customer_idx]['path_id'] = path_id
