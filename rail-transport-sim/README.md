# Rail Transport Simulation

## Overview
The Rail Transport Simulation project is designed to model and simulate a rail transport system, accommodating both forward and backward directions of travel. The simulation includes various components such as passengers, trains, stations, and a network that connects them.

## Features
- **Passenger Management**: Track individual passengers, their journeys, and waiting times.
- **Train Operations**: Simulate train schedules, boarding, and alighting of passengers.
- **Network Management**: Manage stations and lines, including route finding and optimization.
- **Bidirectional Travel**: Support for trains operating in both forward and backward directions.
- **Flexible Fleet Size**: Configurable fleet size to ensure efficient operations.

## Getting Started

### Prerequisites
- Python 3.x
- Required packages listed in `requirements.txt`

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd rail-transport-sim
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Running the Simulation
To run the simulation, execute the following command:
```
python src/rail_sim/main.py
```

### Testing
To run the tests, use:
```
pytest tests/
```

## Project Structure
```
rail-transport-sim
├── src
│   └── rail_sim
│       ├── __init__.py
│       ├── main.py
│       ├── models
│       │   ├── passenger.py
│       │   ├── station.py
│       │   ├── line.py
│       │   └── train.py
│       ├── network
│       │   ├── network.py
│       │   └── routing.py
│       ├── scheduling
│       │   ├── demand.py
│       │   └── timetable.py
│       ├── simulation
│       │   ├── engine.py
│       │   └── events.py
│       └── config
│           └── settings.yaml
├── notebooks
│   └── test.ipynb
├── tests
│   ├── test_bidirectional.py
│   └── test_fleet_size.py
├── requirements.txt
└── README.md
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.