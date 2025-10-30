import numpy as np
from pathlib import Path
from typing import Optional

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
        
        # Create or load memmap
        if self.filepath.exists():
            self.memmap = np.memmap(self.filepath, dtype=CUSTOMER_DTYPE, mode='r+')
            self.capacity = len(self.memmap)
            # Rebuild free list (simplified: assumes ids are sequential)
            used = np.count_nonzero(self.memmap['id'])
            self.next_id = used + 1
        else:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.memmap = np.memmap(
                self.filepath, 
                dtype=CUSTOMER_DTYPE, 
                mode='w+', 
                shape=(self.capacity,)
            )
    
    def allocate_index(self) -> int:
        """Get next available index"""
        if self.free_indices:
            return self.free_indices.pop()
        
        # Find next free slot
        for idx in range(self.capacity):
            if self.memmap['id'][idx] == 0:
                return idx
        
        # Need to grow memmap
        raise RuntimeError("Memmap capacity exceeded")
    
    def allocate_indices(self, n: int) -> np.ndarray:
        """Allocate multiple indices"""
        indices = []
        for _ in range(n):
            indices.append(self.allocate_index())
        return np.array(indices, dtype=np.int64)
    
    def release_index(self, idx: int):
        """Mark index as free for reuse"""
        self.memmap[idx] = 0  # Zero out the record
        self.free_indices.append(idx)
    
    def flush(self):
        """Flush memmap to disk"""
        self.memmap.flush()
    
    def get_next_id(self) -> int:
        """Get next customer ID"""
        cid = self.next_id
        self.next_id += 1
        return cid
