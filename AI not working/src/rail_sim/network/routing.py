# routing.py

def find_route(network, origin, destination):
    """
    Find a route between two stations in the network.
    This function accommodates both forward and backward directions.
    Returns a list of (line_id, from_station, to_station) tuples.
    """
    routes = []

    # Check for direct routes
    for line in network.lines.values():
        if origin in line.stops and destination in line.stops:
            orig_idx = line.stops.index(origin)
            dest_idx = line.stops.index(destination)
            if orig_idx < dest_idx:
                routes.append((line.name, origin, destination))
            elif orig_idx > dest_idx:
                routes.append((line.name, destination, origin))  # Backward route

    # Check for routes with one transfer
    for line1 in network.lines.values():
        if origin not in line1.stops:
            continue
        for transfer_station in line1.stops:
            if transfer_station == origin:
                continue
            for line2 in network.lines.values():
                if line2.name == line1.name:
                    continue
                if transfer_station in line2.stops and destination in line2.stops:
                    orig_idx = line1.stops.index(origin)
                    transfer_idx = line1.stops.index(transfer_station)
                    transfer_idx2 = line2.stops.index(transfer_station)
                    dest_idx = line2.stops.index(destination)
                    if orig_idx < transfer_idx and transfer_idx2 < dest_idx:
                        routes.append((line1.name, origin, transfer_station))
                        routes.append((line2.name, transfer_station, destination))
                    elif orig_idx > transfer_idx and transfer_idx2 > dest_idx:
                        routes.append((line1.name, transfer_station, origin))
                        routes.append((line2.name, destination, transfer_station))

    return routes if routes else None  # No route found