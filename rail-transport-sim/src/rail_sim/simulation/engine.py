from typing import List, Dict, Optional
from .models.train import Train
from .models.line import Line
from .models.station import Station
from .models.passenger import Passenger

class SimulationEngine:
    """Core simulation engine for the rail transport simulation."""

    def __init__(self, lines: List[Line], stations: Dict[str, Station], fleet_size: int):
        self.lines = lines
        self.stations = stations
        self.trains: List[Train] = []
        self.current_time = 0.0

        # Initialize trains for each line with the specified fleet size
        for line in self.lines:
            for i in range(fleet_size):
                train_id = f"{line.name}-{i+1:03d}"
                train = Train(train_id=train_id, line=line.name, capacity=100)  # Example capacity
                self.trains.append(train)

    def run(self, duration: float):
        """Run the simulation for a specified duration."""
        end_time = self.current_time + duration
        while self.current_time < end_time:
            self.step()

    def step(self):
        """Advance the simulation by one time step."""
        # Logic to update train positions, manage boarding/alighting, etc.
        for train in self.trains:
            # Example logic for moving trains and managing passengers
            self.update_train(train)

    def update_train(self, train: Train):
        """Update the state of a train."""
        # Logic to update train state, including boarding and alighting passengers
        pass

    def get_train_status(self) -> List[Dict[str, Optional[str]]]:
        """Get the status of all trains."""
        return [
            {
                "train_id": train.id,
                "current_station": train.current_station,
                "occupancy": train.occupancy,
                "state": train.state.name,
            }
            for train in self.trains
        ]