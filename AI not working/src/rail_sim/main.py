from rail_sim.models.line import Line
from rail_sim.models.train import Train
from rail_sim.network.network import Network
from rail_sim.models.passenger import Passenger
import random

def main():
    # Define a simple line and network
    line = Line(
        name="T1",
        stops=["Central", "Town Hall", "Wynyard", "Circular Quay"],
        travel_times=[2.0, 3.0, 4.0],
        fleet_size=3  # Updated fleet size to be greater than 2
    )
    
    net = Network(transfer_time=2.0)
    net.add_line(line)

    # Create a few passengers with both forward and backward trips
    rng = random.Random(42)
    passengers = {}
    pid = 1
    for _ in range(8):
        oi = rng.randrange(0, len(line.stops))
        di = rng.randrange(0, len(line.stops))
        if oi == di:  # Ensure origin and destination are different
            di = (oi + 1) % len(line.stops)  # Simple wrap-around for valid destination
        p = Passenger(id=pid, origin_id=line.stops[oi], dest_id=line.stops[di], created_at=0.0, queued_at=0.0)
        passengers[pid] = p
        net.stations[p.origin_id].add_passenger_to_queue(p.id, line.name)
        pid += 1

    # Initialize trains for the line
    trains = [Train(train_id=f"T1-{i:03}", line=line.name, capacity=4) for i in range(line.fleet_size)]

    # Start the simulation (simplified)
    print("Starting simulation...")
    for train in trains:
        print(f"Train {train.id} is ready on line {train.line}.")

if __name__ == "__main__":
    main()