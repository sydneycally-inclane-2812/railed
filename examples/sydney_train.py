from rail_sim import Station

station_central = Station(
    station_id=1,
    name="Central",
    line_codes=["T1", "T2", "T3", "T4", "T8", "T9"],
    theoretical_capacity=10000
)

station_redfern = Station(
    station_id=2,
    name="Redfern",
    line_codes=["T1", "T2", "T3", "T4", "T8", "T9"],
    theoretical_capacity=2000
)

station_erskineville = Station(
    station_id=3,
    name="Erskineville",
    line_codes=["T3"],
    theoretical_capacity=1500
)

station_newtown = Station(
    station_id=4,
    name="Newtown",
    line_codes=["T2"],
    theoretical_capacity=1800
)

station_strathfield = Station(
    station_id=5,
    name="Strathfield",
    line_codes=["T1", "T2", "T9"],
    theoretical_capacity=4000
)

station_parramatta = Station(
    station_id=6,
    name="Parramatta",
    line_codes=["T1"],
    theoretical_capacity=3500
)

station_penrith = Station(
    station_id=7,
    name="Penrith",
    line_codes=["T1"],
    theoretical_capacity=2500
)

station_airport = Station(
    station_id=8,
    name="International Airport",
    line_codes=["T8"],
    theoretical_capacity=2200
)

station_bondi = Station(
    station_id=9,
    name="Bondi Junction",
    line_codes=["T4"],
    theoretical_capacity=3000
)


# More stations
station_townhall = Station(
    station_id=10,
    name="Town Hall",
    line_codes=["T1", "T2", "T3", "T8", "T9"],
    theoretical_capacity=9000
)

station_wynyard = Station(
    station_id=11,
    name="Wynyard",
    line_codes=["T1", "T2", "T3", "T8", "T9"],
    theoretical_capacity=8500
)

station_circularquay = Station(
    station_id=12,
    name="Circular Quay",
    line_codes=["T2", "T3", "T8"],
    theoretical_capacity=7000
)

station_north_sydney = Station(
    station_id=13,
    name="North Sydney",
    line_codes=["T1", "T9"],
    theoretical_capacity=6000
)

station_hornsby = Station(
    station_id=14,
    name="Hornsby",
    line_codes=["T1", "T9"],
    theoretical_capacity=4000
)

station_epping = Station(
    station_id=15,
    name="Epping",
    line_codes=["T9"],
    theoretical_capacity=3500
)


from rail_sim import Line

class SydneyNetwork:
    def __init__(self):
        self.stations = [
            station_central,
            station_redfern,
            station_erskineville,
            station_newtown,
            station_strathfield,
            station_parramatta,
            station_penrith,
            station_airport,
            station_bondi,
            station_townhall,
            station_wynyard,
            station_circularquay,
            station_north_sydney,
            station_hornsby,
            station_epping
        ]

        self.lines = [
            Line(
                line_id="T1",
                line_code="T1",
                station_list=[1, 2, 5, 6, 7, 10, 11, 13, 14],
                time_between_stations=[120, 180, 300, 400, 180, 120, 150, 200],
                schedule={'headway': 300, 'service_hours': (5, 23), 'capacity': 1000},
                fleet_size=15,
                bidirectional=True
            ),
            Line(
                line_id="T2",
                line_code="T2",
                station_list=[1, 4, 5, 10, 11, 12],
                time_between_stations=[180, 240, 180, 120, 100],
                schedule={'headway': 400, 'service_hours': (5, 23), 'capacity': 900},
                fleet_size=10,
                bidirectional=True
            ),
            Line(
                line_id="T9",
                line_code="T9",
                station_list=[1, 5, 13, 14, 15],
                time_between_stations=[200, 300, 250, 180],
                schedule={'headway': 350, 'service_hours': (5, 23), 'capacity': 800},
                fleet_size=8,
                bidirectional=True
            )
        ]

        # Add additional lines referenced by stations
        self.lines.extend([
            Line(
                line_id="T3",
                line_code="T3",
                station_list=[1, 3, 10, 11, 12],
                time_between_stations=[120, 140, 110, 130],
                schedule={'headway': 300, 'service_hours': (5, 23), 'capacity': 800},
                fleet_size=9,
                bidirectional=True
            ),
            Line(
                line_id="T4",
                line_code="T4",
                station_list=[1, 2, 9],
                time_between_stations=[100, 160],
                schedule={'headway': 360, 'service_hours': (5, 23), 'capacity': 700},
                fleet_size=6,
                bidirectional=True
            ),
            Line(
                line_id="T8",
                line_code="T8",
                station_list=[8, 1, 10, 11, 12],
                time_between_stations=[300, 120, 100, 100],
                schedule={'headway': 400, 'service_hours': (5, 23), 'capacity': 600},
                fleet_size=7,
                bidirectional=True
            )
        ])

# expose module-level lists for easy import
network = SydneyNetwork()
sydney_stations = network.stations
sydney_lines = network.lines

__all__ = ["sydney_stations", "sydney_lines"]

