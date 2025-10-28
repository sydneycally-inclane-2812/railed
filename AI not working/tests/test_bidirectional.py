import unittest
from src.rail_sim.models.line import Line
from src.rail_sim.models.train import Train
from src.rail_sim.network.network import Network

class TestBidirectionalTrainTravel(unittest.TestCase):

    def setUp(self):
        # Create a simple line with more than 2 stops
        self.line = Line(
            name="T1",
            stops=["Central", "Town Hall", "Wynyard", "Circular Quay"],
            travel_times=[2.0, 3.0, 4.0],
            fleet_size=3  # Ensure fleet size is greater than 2
        )
        self.network = Network()
        self.network.add_line(self.line)

        # Create a train for the line
        self.train = Train(train_id="T1-001", line=self.line.name, capacity=4)

    def test_forward_travel(self):
        # Simulate forward travel from Central to Circular Quay
        self.train.current_station = "Central"
        self.train.arrival_time = 0.0

        for stop in self.line.stops[1:]:
            travel_time = self.line.get_travel_time(self.train.current_station, stop)
            self.train.arrival_time += travel_time
            self.train.current_station = stop

        self.assertEqual(self.train.current_station, "Circular Quay")
        self.assertAlmostEqual(self.train.arrival_time, 9.0)  # Total travel time

    def test_backward_travel(self):
        # Simulate backward travel from Circular Quay to Central
        self.train.current_station = "Circular Quay"
        self.train.arrival_time = 0.0

        for stop in reversed(self.line.stops[:-1]):
            travel_time = self.line.get_travel_time(self.train.current_station, stop)
            self.train.arrival_time += travel_time
            self.train.current_station = stop

        self.assertEqual(self.train.current_station, "Central")
        self.assertAlmostEqual(self.train.arrival_time, 9.0)  # Total travel time

if __name__ == '__main__':
    unittest.main()