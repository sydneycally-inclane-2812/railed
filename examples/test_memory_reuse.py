"""
Test script to verify memory allocation reuse
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from rail_sim import (
    MemmapAllocator,
    MemoryAllocator,
    CustomerGenerator,
    Station,
    Line,
    Map,
    SimulationLoop
)


def test_memory_reuse():
    print("Testing MemoryAllocator reuse...")
    
    allocator = MemoryAllocator(initial_capacity=100)
    
    # Allocate some indices
    print("\n1. Allocating 10 indices:")
    indices = []
    for i in range(10):
        idx = allocator.allocate_index()
        indices.append(idx)
        allocator.memmap[idx]['id'] = allocator.next_id
    
    print(f"   Allocated: {indices}")
    print(f"   Free pool size: {len(allocator.free_indices)}")
    
    # Release some indices
    print("\n2. Releasing first 5 indices:")
    for idx in indices[:5]:
        allocator.release_index(idx)
    
    print(f"   Free pool size: {len(allocator.free_indices)}")
    print(f"   Free pool: {allocator.free_indices}")
    
    # Allocate again - should reuse
    print("\n3. Allocating 5 new indices (should reuse):")
    new_indices = []
    for i in range(5):
        idx = allocator.allocate_index()
        new_indices.append(idx)
        allocator.memmap[idx]['id'] = allocator.next_id
    
    print(f"   New indices: {new_indices}")
    print(f"   Free pool size: {len(allocator.free_indices)}")
    
    # Check if reused
    reused = set(new_indices) & set(indices[:5])
    print(f"\n4. Reused indices: {reused}")
    print(f"   SUCCESS: {len(reused)} indices were reused!" if reused else "   FAILED: No reuse occurred")

if __name__ == "__main__":
    test_memory_reuse()
