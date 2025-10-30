from typing import List, Tuple, Dict, Optional
import hashlib

class PathTable:
    """Stores and manages precomputed routing paths"""
    
    def __init__(self):
        # path_id -> [(line_code, from_station_id, to_station_id), ...]
        self.paths: Dict[int, List[Tuple[str, int, int]]] = {}
        self.path_hash_to_id: Dict[str, int] = {}
        self.next_path_id = 1
    
    def plan(self, origin_id: int, dest_id: int, segments: List[Tuple[str, int, int]]) -> int:
        """
        Store a new path or return existing path_id
        segments: list of (line_code, from_station_id, to_station_id)
        """
        # Create hash of path for deduplication
        path_hash = self._hash_path(segments)
        
        if path_hash in self.path_hash_to_id:
            return self.path_hash_to_id[path_hash]
        
        # New path
        path_id = self.next_path_id
        self.next_path_id += 1
        self.paths[path_id] = segments
        self.path_hash_to_id[path_hash] = path_id
        
        return path_id
    
    def expand(self, path_id: int) -> Optional[List[Tuple[str, int, int]]]:
        """Get segments for a path_id"""
        return self.paths.get(path_id)
    
    def _hash_path(self, segments: List[Tuple[str, int, int]]) -> str:
        """Create unique hash for path"""
        path_str = str(segments)
        return hashlib.md5(path_str.encode()).hexdigest()
