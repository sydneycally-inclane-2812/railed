from typing import List, Dict, Optional
import networkx as nx
from .line import Line
from .station import Station
from .path_table import PathTable
from .logger import get_logger

logger = get_logger()

class Map:
    """Network graph and routing"""
    
    def __init__(self):
        self.lines: List[Line] = []
        self.stations: Dict[int, Station] = {}
        self.station_lookup: Dict[str, Station] = {}
        self.path_table = PathTable()
        
        # String ID to Integer ID mapping
        self.str_to_int: Dict[str, int] = {}
        self.int_to_str: Dict[int, str] = {}
        self._next_station_id = 1
        
        # Build graph - use MultiGraph to support multiple lines on same edge
        self.graph = nx.MultiGraph()
        logger.info("Map initialized")
    
    def register_station_id(self, str_id: str) -> int:
        """Register a string station ID and return its integer equivalent.
        If already registered, return existing ID."""
        if str_id in self.str_to_int:
            return self.str_to_int[str_id]
        
        int_id = self._next_station_id
        self._next_station_id += 1
        
        self.str_to_int[str_id] = int_id
        self.int_to_str[int_id] = str_id
        
        logger.debug(f"Registered station ID mapping: '{str_id}' -> {int_id}")
        return int_id
    
    def get_int_id(self, str_id: str) -> int:
        """Convert string station ID to integer ID."""
        if str_id not in self.str_to_int:
            raise ValueError(f"Station ID '{str_id}' not registered. Register stations before using them.")
        return self.str_to_int[str_id]
    
    def get_str_id(self, int_id: int) -> str:
        """Convert integer station ID to string ID."""
        if int_id not in self.int_to_str:
            raise ValueError(f"Integer station ID {int_id} not found in mapping.")
        return self.int_to_str[int_id]
    
    def add_line(self, line: Line):
        """Add a line to the map"""
        # Convert station list from strings to integers
        line.station_list = []
        for station_id in line.station_list_original:
            if isinstance(station_id, int):
                # If already an integer, ensure it's registered
                if station_id not in self.int_to_str:
                    # Auto-register with str(int) as the string ID
                    self.str_to_int[str(station_id)] = station_id
                    self.int_to_str[station_id] = str(station_id)
                line.station_list.append(station_id)
            else:
                # Convert string to integer
                int_id = self.get_int_id(str(station_id))
                line.station_list.append(int_id)
        
        self.lines.append(line)
        
        # Auto-populate line_codes in stations
        for station_id in line.station_list:
            if station_id in self.stations:
                station = self.stations[station_id]
                if line.line_code not in station.line_codes:
                    station.line_codes.append(line.line_code)
                    logger.debug(f"Added line {line.line_code} to station {station.name}")
        
        self._rebuild_graph()
        logger.info(f"Added line {line.line_code} to network with stations: {line.station_list}")
    
    def add_station(self, station: Station):
        """Add a station to the map"""
        # Register the string ID and get/set the integer ID
        int_id = self.register_station_id(station.station_id_str)
        station.station_id = int_id
        
        self.stations[int_id] = station
        self.station_lookup[station.name] = station
        self._rebuild_graph()
        logger.info(f"Added station '{station.station_id_str}' (ID: {int_id}, Name: {station.name}) to network")
    
    def _rebuild_graph(self):
        """Rebuild network graph from lines"""
        self.graph.clear()
        
        for line in self.lines:
            for i in range(len(line.station_list) - 1):
                from_id = line.station_list[i]
                to_id = line.station_list[i + 1]
                weight = line.time_between_stations[i]
                
                # MultiGraph allows multiple edges between same nodes
                self.graph.add_edge(
                    from_id, 
                    to_id, 
                    weight=weight,
                    line=line.line_code
                )
    
    def find_path(self, origin_id: int, dest_id: int) -> int:
        """
        Find optimal path and return path_id
        Uses shortest path by travel time
        """
        try:
            #print(f"DEBUG: Finding path from {origin_id} to {dest_id}")
            #print(f"DEBUG: Graph nodes: {list(self.graph.nodes())}")
            #print(f"DEBUG: Graph edges: {list(self.graph.edges(data=True))}")
            # Find shortest path
            node_path = nx.shortest_path(
                self.graph, 
                origin_id, 
                dest_id, 
                weight='weight'
            )
            #print(f"DEBUG: Found node path: {node_path}")
            # Convert to segments
            segments = []
            for i in range(len(node_path) - 1):
                from_id = node_path[i]
                to_id = node_path[i + 1]
                # Get line for this edge - MultiGraph returns dict of edges by key
                edge_data = self.graph.get_edge_data(from_id, to_id)
                # For MultiGraph, edge_data is {key: {attributes}, ...}
                # Pick the first edge (arbitrary choice when multiple lines exist)
                if isinstance(edge_data, dict):
                    first_key = next(iter(edge_data))
                    line_code = edge_data[first_key].get('line', 'Unknown')
                else:
                    line_code = edge_data.get('line', 'Unknown')
                segments.append((line_code, from_id, to_id))
            #print(f"DEBUG: Segments for path: {segments}")
            # Store in path table
            path_id = self.path_table.plan(origin_id, dest_id, segments)
            #print(f"DEBUG: Stored path_id {path_id} for {origin_id}->{dest_id}")
            return path_id
        except nx.NetworkXNoPath:
            #print(f"DEBUG: No path found from station {origin_id} to {dest_id}")
            logger.error(f"No path found from station {origin_id} to {dest_id}")
            return 0  # No path found
    
    def assign_path_to_customer(self, customer_idx: int, memmap):
        """Find and assign path to customer"""
        origin = int(memmap[customer_idx]['origin_station_id'])
        dest = int(memmap[customer_idx]['dest_station_id'])
        #print(f"DEBUG: Assigning path for customer {customer_idx} from {origin} to {dest}")
        path_id = self.find_path(origin, dest)
        #print(f"DEBUG: Assigned path_id {path_id} to customer {customer_idx}")
        memmap[customer_idx]['path_id'] = path_id
    
    def get_transfer_options(self, station_id: int) -> List[str]:
        """Get available lines at a station"""
        station = self.stations.get(station_id)
        if station:
            return station.line_codes
        return []
