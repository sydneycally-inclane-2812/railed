from typing import Dict, List, Optional

class Network:
    """Rail network graph with stations and lines."""
    
    def __init__(self, transfer_time: float = 2.0):
        self.stations: Dict[str, Station] = {}
        self.lines: Dict[str, Line] = {}
        self.default_transfer_time = transfer_time

    def add_station(self, station_id: str, transfer_time: Optional[float] = None):
        """Add a station to the network."""
        if station_id not in self.stations:
            tt = transfer_time if transfer_time is not None else self.default_transfer_time
            self.stations[station_id] = Station(station_id, transfer_time=tt)

    def add_line(self, line: Line):
        """Add a line and auto-create stations."""
        self.lines[line.name] = line
        # Auto-create stations from line definition
        for station_id in line.stops:
            self.add_station(station_id)
            self.stations[station_id].add_line(line.name)

    def get_station(self, station_id: str) -> Optional[Station]:
        """Get station by ID."""
        return self.stations.get(station_id)

    def get_line(self, line_id: str) -> Optional[Line]:
        """Get line by ID."""
        return self.lines.get(line_id)

    def find_route(self, origin: str, destination: str) -> Optional[List[tuple]]:
        """
        Find route between stations.
        Returns list of (line_id, from_station, to_station) tuples.
        Simple implementation: direct line or one transfer.
        """
        # Direct line
        for line in self.lines.values():
            if origin in line.stops and destination in line.stops:
                orig_idx = line.stops.index(origin)
                dest_idx = line.stops.index(destination)
                if orig_idx < dest_idx:
                    return [(line.name, origin, destination)]
        
        # One-transfer
        for line1 in self.lines.values():
            if origin not in line1.stops:
                continue
            for transfer_station in line1.stops:
                if transfer_station == origin:
                    continue
                for line2 in self.lines.values():
                    if line2.name == line1.name:
                        continue
                    if transfer_station in line2.stops and destination in line2.stops:
                        orig_idx = line1.stops.index(origin)
                        transfer_idx = line1.stops.index(transfer_station)
                        transfer_idx2 = line2.stops.index(transfer_station)
                        dest_idx = line2.stops.index(destination)
                        if orig_idx < transfer_idx and transfer_idx2 < dest_idx:
                            return [
                                (line1.name, origin, transfer_station),
                                (line2.name, transfer_station, destination),
                            ]
        return None  # No route found