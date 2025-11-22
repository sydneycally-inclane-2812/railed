from pathlib import Path
import sys
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rail_sim import (
    Station,
    Line,
    Map,
    DrawMap
)

station_central = Station(
    station_id="central",
    name="Central",
    theoretical_capacity=10000
)

station_redfern = Station(
    station_id="redfern",
    name="Redfern",
    theoretical_capacity=2000
)

station_erskineville = Station(
    station_id="erskineville",
    name="Erskineville",
    theoretical_capacity=1500
)

station_newtown = Station(
    station_id="newtown",
    name="Newtown",
    theoretical_capacity=1800
)

station_strathfield = Station(
    station_id="strathfield",
    name="Strathfield",
    theoretical_capacity=4000
)

station_parramatta = Station(
    station_id="parramatta",
    name="Parramatta",
    theoretical_capacity=3500
)

station_penrith = Station(
    station_id="penrith",
    name="Penrith",
    theoretical_capacity=2500
)

station_airport = Station(
    station_id="airport",
    name="International Airport",
    theoretical_capacity=2200
)

station_bondi = Station(
    station_id="bondi",
    name="Bondi Junction",
    theoretical_capacity=3000
)

station_townhall = Station(
    station_id="townhall",
    name="Town Hall",
    theoretical_capacity=9000
)

station_wynyard = Station(
    station_id="wynyard",
    name="Wynyard",
    theoretical_capacity=8500
)

station_circular_quay = Station(
    station_id="circular_quay",
    name="Circular Quay",
    theoretical_capacity=7000
)

station_north_sydney = Station(
    station_id="north_sydney",
    name="North Sydney",
    theoretical_capacity=6000
)

station_hornsby = Station(
    station_id="hornsby",
    name="Hornsby",
    theoretical_capacity=4000
)

station_epping = Station(
    station_id="epping",
    name="Epping",
    theoretical_capacity=3500
)

station_lidcombe = Station(
    station_id="lidcombe",
    name="Lidcombe",
    theoretical_capacity=3500
)

station_berowra = Station(station_id="berowra", name="Berowra", theoretical_capacity=2000)
station_gordon = Station(station_id="gordon", name="Gordon", theoretical_capacity=2500)
station_chatswood = Station(station_id="chatswood", name="Chatswood", theoretical_capacity=5000)
station_auburn = Station(station_id="auburn", name="Auburn", theoretical_capacity=2500)
station_clyde = Station(station_id="clyde", name="Clyde", theoretical_capacity=2000)
station_granville = Station(station_id="granville", name="Granville", theoretical_capacity=2500)
station_seven_hills = Station(station_id="seven_hills", name="Seven Hills", theoretical_capacity=2000)
station_blacktown = Station(station_id="blacktown", name="Blacktown", theoretical_capacity=3500)
station_st_marys = Station(station_id="st_marys", name="St Marys", theoretical_capacity=2500)
station_emu_plains = Station(station_id="emu_plains", name="Emu Plains", theoretical_capacity=2000)
station_museum = Station(station_id="museum", name="Museum", theoretical_capacity=3000)
station_mcdtown = Station(station_id="mcdtown", name="Macdonaldtown", theoretical_capacity=1500)
station_ashfield = Station(station_id="ashfield", name="Ashfield", theoretical_capacity=2500)
station_rhodes = Station(station_id="rhodes", name="Rhodes", theoretical_capacity=2500)
station_sydenham = Station(station_id="sydenham", name="Sydenham", theoretical_capacity=2500)
station_campsie = Station(station_id="campsie", name="Campsie", theoretical_capacity=2000)
station_bankstown = Station(station_id="bankstown", name="Bankstown", theoretical_capacity=3500)
station_wolli_creek = Station(station_id="wolli_creek", name="Wolli Creek", theoretical_capacity=2500)
station_hurstville = Station(station_id="hurstville", name="Hurstville", theoretical_capacity=3000)
station_cronulla = Station(station_id="cronulla", name="Cronulla", theoretical_capacity=2500)
station_revesby = Station(station_id="revesby", name="Revesby", theoretical_capacity=2000)
station_glenfield = Station(station_id="glenfield", name="Glenfield", theoretical_capacity=2000)
station_campbelltown = Station(station_id="campbelltown", name="Campbelltown", theoretical_capacity=3500)
station_macarthur = Station(station_id="macarthur", name="Macarthur", theoretical_capacity=3000)

from rail_sim import Line

class SydneyNetwork:
    def __init__(self):
        self.stations = [
            station_central, station_redfern, station_erskineville, station_newtown,
            station_strathfield, station_parramatta, station_penrith, station_airport,
            station_bondi, station_townhall, station_wynyard, station_circular_quay,
            station_north_sydney, station_hornsby, station_epping, station_lidcombe,
            station_berowra, station_gordon, station_chatswood, station_auburn,
            station_clyde, station_granville, station_seven_hills, station_blacktown,
            station_st_marys, station_emu_plains, station_museum, station_mcdtown,
            station_ashfield, station_rhodes, station_sydenham, station_campsie,
            station_bankstown, station_wolli_creek, station_hurstville, station_cronulla,
            station_revesby, station_glenfield, station_campbelltown, station_macarthur
        ]

        self.lines = [
            Line(
                line_id="T1",
                line_code="T1",
                station_list=["berowra", "hornsby", "gordon", "chatswood", "wynyard", "townhall", "central", "redfern", "strathfield", "lidcombe", "auburn", "clyde", "granville", "parramatta", "seven_hills", "blacktown", "st_marys", "penrith", "emu_plains"],
                time_between_stations=[180, 240, 300, 180, 120, 60, 120, 180, 120, 90, 120, 120, 180, 240, 180, 180, 240, 180],
                schedule={'headway': 600, 'service_hours': (5, 23), 'capacity': 1000},
                fleet_size=15,
                bidirectional=True
            ),
            Line(
                line_id="T2",
                line_code="T2",
                station_list=["circular_quay", "wynyard", "townhall", "central", "museum", "circular_quay", "wynyard", "townhall", "central", "redfern", "mcdtown", "newtown", "ashfield", "strathfield", "lidcombe", "auburn", "clyde", "granville", "parramatta"],
                time_between_stations=[100, 60, 60, 80, 100, 100, 60, 60, 120, 90, 120, 150, 180, 120, 90, 120, 120, 180],
                schedule={'headway': 450, 'service_hours': (5, 23), 'capacity': 900},
                fleet_size=10,
                bidirectional=True
            ),
            Line(
                line_id="T9",
                line_code="T9",
                station_list=["hornsby", "epping", "rhodes", "strathfield", "redfern", "central", "townhall", "wynyard", "chatswood", "gordon"],
                time_between_stations=[240, 300, 180, 180, 120, 60, 120, 300, 240],
                schedule={'headway': 550, 'service_hours': (5, 23), 'capacity': 800},
                fleet_size=8,
                bidirectional=True
            )
        ]

        # Add additional lines referenced by stations
        self.lines.extend([
            Line(
                line_id="T3",
                line_code="T3",
                station_list=["bankstown", "campsie", "sydenham", "redfern", "central", "townhall", "wynyard", "circular_quay"],
                time_between_stations=[180, 120, 180, 120, 60, 120, 100],
                schedule={'headway': 300, 'service_hours': (5, 23), 'capacity': 800},
                fleet_size=9,
                bidirectional=True
            ),
            Line(
                line_id="T4",
                line_code="T4",
                station_list=["bondi", "central", "redfern", "sydenham", "wolli_creek", "hurstville", "cronulla"],
                time_between_stations=[300, 120, 180, 150, 240, 360],
                schedule={'headway': 360, 'service_hours': (5, 23), 'capacity': 700},
                fleet_size=6,
                bidirectional=True
            ),
            Line(
                line_id="T8",
                line_code="T8",
                station_list=["macarthur", "campbelltown", "glenfield", "revesby", "wolli_creek", "airport", "central", "museum", "circular_quay", "wynyard", "townhall", "central"],
                time_between_stations=[180, 240, 300, 240, 360, 240, 80, 100, 100, 60, 60],
                schedule={'headway': 500, 'service_hours': (5, 23), 'capacity': 600},
                fleet_size=7,
                bidirectional=True
            )
        ])

# expose module-level lists for easy import
network = SydneyNetwork()
sydney_stations = network.stations
sydney_lines = network.lines

__all__ = ["sydney_stations", "sydney_lines"]

if __name__ == "__main__":
    from rail_sim import Map
    
    # Create a map and add stations and lines
    map_obj = Map()
    
    for station in sydney_stations:
        map_obj.add_station(station)
    
    for line in sydney_lines:
        map_obj.add_line(line)
    
    # Draw the network
    drawer = DrawMap(show_labels=True, figsize=(14, 10))
    drawer.draw(map_obj)
    

