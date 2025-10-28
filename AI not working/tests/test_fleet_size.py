import unittest
from src.rail_sim.models.line import Line
from src.rail_sim.models.train import Train
from src.rail_sim.network.network import Network

class TestFleetSize(unittest.TestCase):
    def setUp(self):
        self.line = Line(
            name="T1",
            stops=["Central", "Town Hall", "Wynyard", "Circular Quay"],
            travel_times=[2.0, 3.0, 4.0],
            fleet_size=3  # Ensure fleet size is greater than 2
        )
        self.network = Network()
        self.network.add_line(self.line)

    def test_fleet_size(self):
        self.assertGreater(self.line.fleet_size, 2, "Fleet size should be greater than 2.")

    def test_train_creation(self):
        trains = [Train(train_id=f"T1-{i:03}", line=self.line.name, capacity=100) for i in range(self.line.fleet_size)]
        self.assertEqual(len(trains), self.line.fleet_size, "Number of trains created should match fleet size.")

if __name__ == "__main__":
    unittest.main()