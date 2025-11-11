import numpy as np
from pathlib import Path
from typing import Optional
from .logger import get_logger

logger = get_logger()

# Customer memmap dtype definition
CUSTOMER_DTYPE = np.dtype([
    ('id', 'u8'),
    ('origin_station_id', 'u4'),
    ('dest_station_id', 'u4'),
    ('current_station_id', 'u4'),
    ('on_train_id', 'u4'),  # 0 = not on train
    ('state', 'u1'),  # 0=waiting, 1=onboard, 2=arrived, 3=transferring
    ('tap_on_ts', 'f8'),
    ('tap_off_ts', 'f8'),
    ('spawn_ts', 'f8'),
    ('path_id', 'u4'),
    ('total_wait_time', 'f8'),
    ('total_travel_time', 'f8'),
    ('movement_speed', 'f4')
])

class MemmapAllocator:
    """Manages allocation of customer records in memmap"""
    
    def __init__(self, filepath: str, initial_capacity: int = 1_000_000):
        self.filepath = Path(filepath)
        self.capacity = initial_capacity
        self.free_indices = []
        self.next_id = 1
        
        logger.info(f"Initializing MemmapAllocator with capacity={initial_capacity} at {filepath}")
        
        # Create or load memmap
        if self.filepath.exists():
            logger.info(f"Loading existing memmap from {filepath}")
            self.memmap = np.memmap(self.filepath, dtype=CUSTOMER_DTYPE, mode='r+')
            self.capacity = len(self.memmap)
            # Rebuild free list (simplified: assumes ids are sequential)
            used = np.count_nonzero(self.memmap['id'])
            self.next_id = used + 1
            logger.info(f"Loaded memmap: capacity={self.capacity}, used={used}, next_id={self.next_id}")
        else:
            logger.info(f"Creating new memmap at {filepath}")
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.memmap = np.memmap(
                self.filepath, 
                dtype=CUSTOMER_DTYPE, 
                mode='w+', 
                shape=(self.capacity,)
            )
            logger.info(f"Created new memmap with capacity={self.capacity}")
    
    def allocate_index(self) -> int:
        """Get next available index"""
        if self.free_indices:
            idx = self.free_indices.pop()
            logger.debug(f"Allocated index {idx} from free pool (pool size: {len(self.free_indices)})")
            return idx
        
        # Find next free slot
        for idx in range(self.capacity):
            if self.memmap['id'][idx] == 0:
                # Mark this slot as allocated by setting a non-zero id
                self.memmap['id'][idx] = self.get_next_id()
                logger.debug(f"Allocated new index {idx}")
                return idx
        
        # Need to grow memmap
        logger.error(f"Memmap capacity exceeded! Capacity: {self.capacity}")
        raise RuntimeError("Memmap capacity exceeded")
    
    def allocate_indices(self, n: int) -> np.ndarray:
        """Allocate multiple indices"""
        logger.debug(f"Allocating {n} indices")
        indices = []
        for _ in range(n):
            indices.append(self.allocate_index())
        logger.debug(f"Successfully allocated {n} indices")
        return np.array(indices, dtype=np.int64)
    
    def release_index(self, idx: int):
        """Mark index as free for reuse"""
        logger.debug(f"Releasing index {idx} to free pool")
        self.memmap[idx] = 0  # Zero out the record
        self.free_indices.append(idx)
    
    def flush(self):
        """Flush memmap to disk"""
        logger.debug("Flushing memmap to disk")
        self.memmap.flush()
        logger.debug("Memmap flushed successfully")
    
    def get_next_id(self) -> int:
        """Get next customer ID"""
        cid = self.next_id
        self.next_id += 1
        return cid
