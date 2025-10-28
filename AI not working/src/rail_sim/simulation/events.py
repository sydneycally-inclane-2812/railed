from typing import List, Dict, Any

class Event:
    """Base class for all events in the simulation."""
    def __init__(self, time: float):
        self.time = time

    def execute(self, simulation: Any):
        """Execute the event in the context of the simulation."""
        raise NotImplementedError("Subclasses should implement this method.")

class BoardingEvent(Event):
    """Event representing a passenger boarding a train."""
    def __init__(self, time: float, passenger_id: int, train_id: str):
        super().__init__(time)
        self.passenger_id = passenger_id
        self.train_id = train_id

    def execute(self, simulation: Any):
        """Handle the boarding of a passenger."""
        train = simulation.get_train(self.train_id)
        if train:
            boarded = train.board_passenger(self.passenger_id)
            if boarded:
                print(f"Passenger {self.passenger_id} boarded train {self.train_id} at time {self.time}.")

class AlightingEvent(Event):
    """Event representing a passenger alighting from a train."""
    def __init__(self, time: float, passenger_id: int, train_id: str):
        super().__init__(time)
        self.passenger_id = passenger_id
        self.train_id = train_id

    def execute(self, simulation: Any):
        """Handle the alighting of a passenger."""
        train = simulation.get_train(self.train_id)
        if train:
            alighted = train.alight_passenger(self.passenger_id)
            if alighted:
                print(f"Passenger {self.passenger_id} alighted from train {self.train_id} at time {self.time}.")

class TrainDepartureEvent(Event):
    """Event representing a train departing from a station."""
    def __init__(self, time: float, train_id: str, station_id: str):
        super().__init__(time)
        self.train_id = train_id
        self.station_id = station_id

    def execute(self, simulation: Any):
        """Handle the departure of a train."""
        train = simulation.get_train(self.train_id)
        if train:
            train.depart(self.station_id)
            print(f"Train {self.train_id} departed from {self.station_id} at time {self.time}.")

class TrainArrivalEvent(Event):
    """Event representing a train arriving at a station."""
    def __init__(self, time: float, train_id: str, station_id: str):
        super().__init__(time)
        self.train_id = train_id
        self.station_id = station_id

    def execute(self, simulation: Any):
        """Handle the arrival of a train."""
        train = simulation.get_train(self.train_id)
        if train:
            train.arrive(self.station_id)
            print(f"Train {self.train_id} arrived at {self.station_id} at time {self.time}.")

class SimulationEventQueue:
    """Class to manage events in the simulation."""
    def __init__(self):
        self.events: List[Event] = []

    def add_event(self, event: Event):
        """Add an event to the queue."""
        self.events.append(event)
        self.events.sort(key=lambda e: e.time)

    def execute_events(self, simulation: Any):
        """Execute all events in the queue."""
        while self.events:
            event = self.events.pop(0)
            event.execute(simulation)