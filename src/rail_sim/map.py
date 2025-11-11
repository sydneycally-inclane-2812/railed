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
        
        # Build graph
        self.graph = nx.Graph()
        logger.info("Map initialized")
    
    def add_line(self, line: Line):
        """Add a line to the map"""
        self.lines.append(line)
        self._rebuild_graph()
        logger.info(f"Added line {line.line_code} to network")
    
    def add_station(self, station: Station):
        """Add a station to the map"""
        self.stations[station.station_id] = station
        self.station_lookup[station.name] = station
        self._rebuild_graph()
        logger.info(f"Added station {station.station_id} ({station.name}) to network")
    
    def _rebuild_graph(self):
        """Rebuild network graph from lines"""
        self.graph.clear()
        
        for line in self.lines:
            for i in range(len(line.station_list) - 1):
                from_id = line.station_list[i]
                to_id = line.station_list[i + 1]
                weight = line.time_between_stations[i]
                
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
            # Find shortest path
            node_path = nx.shortest_path(
                self.graph, 
                origin_id, 
                dest_id, 
                weight='weight'
            )
            
            logger.debug(f"Found path from {origin_id} to {dest_id}: {node_path}")
            
            # Convert to segments
            segments = []
            for i in range(len(node_path) - 1):
                from_id = node_path[i]
                to_id = node_path[i + 1]
                
                # Get line for this edge
                edge_data = self.graph.get_edge_data(from_id, to_id)
                line_code = edge_data['line']
                
                segments.append((line_code, from_id, to_id))
            
            # Store in path table
            path_id = self.path_table.plan(origin_id, dest_id, segments)
            return path_id
            
        except nx.NetworkXNoPath:
            logger.error(f"No path found from station {origin_id} to {dest_id}")
            return 0  # No path found
    
    def assign_path_to_customer(self, customer_idx: int, memmap):
        """Find and assign path to customer"""
        origin = int(memmap[customer_idx]['origin_station_id'])
        dest = int(memmap[customer_idx]['dest_station_id'])
        
        # Debug: print first assignment
        if not hasattr(self, '_debug_printed'):
            print(f"DEBUG: Assigning path from {origin} to {dest}")
            print(f"DEBUG: Stations in network: {list(self.stations.keys())}")
            print(f"DEBUG: Graph nodes: {list(self.graph.nodes())}")
            self._debug_printed = True
        
        path_id = self.find_path(origin, dest)
        memmap[customer_idx]['path_id'] = path_id
    
    def get_transfer_options(self, station_id: int) -> List[str]:
        """Get available lines at a station"""
        station = self.stations.get(station_id)
        if station:
            return station.line_codes
        return []
