class Line:
    """Train line with stops and travel times."""
    def __init__(self, name: str, stops: List[str], travel_times: List[float], fleet_size: int = 3):
        self.name = name
        self.stops = stops  # ordered list of station IDs
        self.fleet_size = fleet_size  # number of trains assigned to this line
        if len(travel_times) != len(stops) - 1:
            raise ValueError(
                f"Line {name}: need {len(stops)-1} travel times for {len(stops)} stops"
            )
        self.travel_times = travel_times  # minutes between consecutive stops

    def get_travel_time(self, from_station: str, to_station: str) -> Optional[float]:
        """Get travel time between two stations on this line (forward direction)."""
        try:
            from_idx = self.stops.index(from_station)
            to_idx = self.stops.index(to_station)
            if from_idx >= to_idx:
                return None  # wrong direction or same station
            return sum(self.travel_times[from_idx:to_idx])
        except (ValueError, IndexError):
            return None

    def get_next_stop(self, current_station: str) -> Optional[str]:
        """Get the next station after current one."""
        try:
            idx = self.stops.index(current_station)
            if idx < len(self.stops) - 1:
                return self.stops[idx + 1]
        except ValueError:
            pass
        return None

    def get_previous_stop(self, current_station: str) -> Optional[str]:
        """Get the previous station before the current one."""
        try:
            idx = self.stops.index(current_station)
            if idx > 0:
                return self.stops[idx - 1]
        except ValueError:
            pass
        return None

    def get_stop_index(self, station: str) -> Optional[int]:
        """Get index of station in stops list."""
        try:
            return self.stops.index(station)
        except ValueError:
            return None