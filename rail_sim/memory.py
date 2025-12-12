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
        self.free_stack = []  # Stack-based free list (O(1) pop/push)
        self.next_id = 1
        self._next_scan_idx = 0  # Track where to scan for initial free indices
        
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
        """Get next available index (O(1) from pre-allocated stack)"""
        # Fast path: use pre-allocated free stack
        if self.free_stack:
            idx = self.free_stack.pop()
            return idx
        
        # Slow path: scan for free slots (only happens if stack depleted)
        for idx in range(self._next_scan_idx, self.capacity):
            if self.memmap['id'][idx] == 0:
                self._next_scan_idx = idx + 1
                return idx
        
        # Need to grow memmap
        logger.error(f"Memmap capacity exceeded! Capacity: {self.capacity}")
        raise RuntimeError("Memmap capacity exceeded")
    
    def allocate_indices(self, n: int) -> np.ndarray:
        """Allocate multiple indices (fast batch using pre-allocated stack)"""
        if len(self.free_stack) >= n:
            indices = [self.free_stack.pop() for _ in range(n)]
            return np.array(indices, dtype=np.int64)
        
        logger.debug(f"Allocating {n} indices (stack had {len(self.free_stack)})")
        indices = []
        for _ in range(n):
            indices.append(self.allocate_index())
        logger.debug(f"Successfully allocated {n} indices")
        return np.array(indices, dtype=np.int64)
    
    def preallocate(self, n: int) -> None:
        """Pre-allocate n free indices for fast allocation during simulation."""
        logger.info(f"Pre-allocating {n} free indices...")
        initial_stack_size = len(self.free_stack)
        
        for idx in range(self._next_scan_idx, min(self._next_scan_idx + n, self.capacity)):
            if self.memmap['id'][idx] == 0:
                self.free_stack.append(idx)
        
        self._next_scan_idx = min(self._next_scan_idx + n, self.capacity)
        allocated_count = len(self.free_stack) - initial_stack_size
        logger.info(f"Pre-allocated {allocated_count} indices (free stack now has {len(self.free_stack)})")
    
    def release_index(self, idx: int):
        """Mark index as free for reuse"""
        self.memmap[idx] = 0  # Zero out the record
        self.free_stack.append(idx)
    
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
    
    def defragment(self, threshold: float = 0.5) -> int:
        """
        Compact memory when fragmentation exceeds threshold
        
        Args:
            threshold: Defragment if fragmentation ratio exceeds this (0.0 to 1.0)
            
        Returns:
            Number of records compacted
        """
        active_count = np.sum(self.memmap['id'] > 0)
        fragmentation = 1 - (active_count / self.capacity)
        
        if fragmentation < threshold:
            logger.debug(f"Fragmentation {fragmentation:.2%} below threshold {threshold:.2%}, skipping defrag")
            return 0
        
        logger.info(f"Defragmenting memmap: {active_count} active / {self.capacity} capacity ({fragmentation:.2%} fragmented)")
        
        # Find all active records
        active_mask = self.memmap['id'] > 0
        active_data = self.memmap[active_mask].copy()
        
        # Clear entire memmap
        self.memmap[:] = 0
        
        # Write active records to start
        self.memmap[:len(active_data)] = active_data
        
        # Rebuild free stack with all indices after active data
        self.free_stack = list(range(len(active_data), self.capacity))
        self._next_scan_idx = len(active_data)
        
        logger.info(f"Defragmentation complete: compacted {len(active_data)} records, {len(self.free_stack)} free slots")
        
        return len(active_data)
    
    def trim_capacity(self, target_capacity: Optional[int] = None) -> int:
        """
        Reduce memmap capacity to save memory (cannot be used with file-backed memmap)
        
        Args:
            target_capacity: New capacity (default: current active + 20% headroom)
            
        Returns:
            New capacity
        """
        logger.error("trim_capacity not supported for file-backed memmap - use MemoryAllocator instead")
        raise NotImplementedError("Cannot trim file-backed memmap")


class MemoryAllocator:
    """In-memory allocator for customer records (faster than memmap)"""
    
    def __init__(self, initial_capacity: int = 1_000_000):
        self.capacity = initial_capacity
        self.free_stack = []  # Stack-based free list (O(1) pop/push)
        self.next_id = 1
        self._next_scan_idx = 0
        
        logger.info(f"Initializing MemoryAllocator with capacity={initial_capacity} (in-memory)")
        
        # Create numpy array in memory
        self.memmap = np.zeros(self.capacity, dtype=CUSTOMER_DTYPE)
        logger.info(f"Created in-memory array with capacity={self.capacity}")
    
    def allocate_index(self) -> int:
        """Get next available index (O(1) from pre-allocated stack)"""
        if self.free_stack:
            idx = self.free_stack.pop()
            return idx
        
        # Scan for free slots
        for idx in range(self._next_scan_idx, self.capacity):
            if self.memmap['id'][idx] == 0:
                self._next_scan_idx = idx + 1
                return idx
        
        # Need to grow array
        logger.warning(f"Memory capacity exceeded! Growing from {self.capacity} to {self.capacity * 2}")
        self._grow()
        return self.allocate_index()
    
    def allocate_indices(self, n: int) -> np.ndarray:
        """Allocate multiple indices (fast batch using pre-allocated stack)"""
        if len(self.free_stack) >= n:
            indices = [self.free_stack.pop() for _ in range(n)]
            return np.array(indices, dtype=np.int64)
        
        logger.debug(f"Allocating {n} indices (stack had {len(self.free_stack)})")
        indices = []
        for _ in range(n):
            indices.append(self.allocate_index())
        logger.debug(f"Successfully allocated {n} indices")
        return np.array(indices, dtype=np.int64)
    
    def preallocate(self, n: int) -> None:
        """Pre-allocate n free indices for fast allocation during simulation."""
        logger.info(f"Pre-allocating {n} free indices...")
        initial_stack_size = len(self.free_stack)
        
        for idx in range(self._next_scan_idx, min(self._next_scan_idx + n, self.capacity)):
            if self.memmap['id'][idx] == 0:
                self.free_stack.append(idx)
        
        self._next_scan_idx = min(self._next_scan_idx + n, self.capacity)
        allocated_count = len(self.free_stack) - initial_stack_size
        logger.info(f"Pre-allocated {allocated_count} indices (free stack now has {len(self.free_stack)})")
    
    def release_index(self, idx: int):
        """Mark index as free for reuse"""
        self.memmap[idx] = 0  # Zero out the record
        self.free_stack.append(idx)
    
    def flush(self):
        """No-op for in-memory allocator (for API compatibility)"""
        logger.debug("Flush called on in-memory allocator (no-op)")
        pass
    
    def get_next_id(self) -> int:
        """Get next customer ID"""
        cid = self.next_id
        self.next_id += 1
        return cid
    
    def _grow(self):
        """Double the capacity of the array"""
        old_capacity = self.capacity
        self.capacity *= 2
        
        logger.info(f"Growing array from {old_capacity} to {self.capacity}")
        
        # Create new larger array
        new_array = np.zeros(self.capacity, dtype=CUSTOMER_DTYPE)
        
        # Copy old data
        new_array[:old_capacity] = self.memmap
        
        # Replace old array
        self.memmap = new_array
        
        logger.info(f"Successfully grew array to {self.capacity}")
    
    def defragment(self, threshold: float = 0.5) -> int:
        """
        Compact memory when fragmentation exceeds threshold
        
        Args:
            threshold: Defragment if fragmentation ratio exceeds this (0.0 to 1.0)
            
        Returns:
            Number of records compacted
        """
        active_count = np.sum(self.memmap['id'] > 0)
        fragmentation = 1 - (active_count / self.capacity)
        
        if fragmentation < threshold:
            logger.debug(f"Fragmentation {fragmentation:.2%} below threshold {threshold:.2%}, skipping defrag")
            return 0
        
        logger.info(f"Defragmenting array: {active_count} active / {self.capacity} capacity ({fragmentation:.2%} fragmented)")
        
        # Find all active records
        active_mask = self.memmap['id'] > 0
        active_data = self.memmap[active_mask].copy()
        
        # Clear entire array
        self.memmap[:] = 0
        
        # Write active records to start
        self.memmap[:len(active_data)] = active_data
        
        # Rebuild free stack with all indices after active data
        self.free_stack = list(range(len(active_data), self.capacity))
        self._next_scan_idx = len(active_data)
        
        logger.info(f"Defragmentation complete: compacted {len(active_data)} records, {len(self.free_stack)} free slots")
        
        return len(active_data)
    
    def trim_capacity(self, target_capacity: Optional[int] = None) -> int:
        """
        Reduce array capacity to save memory
        
        Args:
            target_capacity: New capacity (default: current active + 20% headroom)
            
        Returns:
            New capacity
        """
        active_count = np.sum(self.memmap['id'] > 0)
        
        if target_capacity is None:
            # Default: active + 20% headroom, minimum 10000
            target_capacity = max(int(active_count * 1.2), 10_000)
        
        if target_capacity < active_count:
            logger.error(f"Cannot trim to {target_capacity}: would lose {active_count - target_capacity} active records")
            raise ValueError(f"Target capacity {target_capacity} < active count {active_count}")
        
        if target_capacity >= self.capacity:
            logger.debug(f"Target capacity {target_capacity} >= current {self.capacity}, skipping trim")
            return self.capacity
        
        logger.info(f"Trimming array from {self.capacity} to {target_capacity} ({active_count} active records)")
        
        # Create new smaller array
        new_array = np.zeros(target_capacity, dtype=CUSTOMER_DTYPE)
        
        # Copy active data (should be compacted at start after defrag)
        active_mask = self.memmap['id'] > 0
        active_indices = np.where(active_mask)[0]
        
        if len(active_indices) > 0:
            # Copy all active records
            new_array[:active_count] = self.memmap[active_mask]
        
        # Replace old array
        self.memmap = new_array
        self.capacity = target_capacity
        
        # Rebuild free stack
        self.free_stack = list(range(active_count, target_capacity))
        self._next_scan_idx = active_count
        
        logger.info(f"Trim complete: new capacity {self.capacity}, {len(self.free_stack)} free slots")
        
        return self.capacity
    
