"""Build a TransitNetwork from a JSON description of the lines.

The file lists each line as an ordered list of stops plus the ride time
between each pair of consecutive stops, which is how a real timetable reads.
The loader turns that into graph edges.
"""

import json

from .network import TransitNetwork


class MapFormatError(ValueError):
    """Raised when the map file is missing data or is inconsistent."""


def load_network(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return network_from_dict(data)


def network_from_dict(data):
    try:
        network = TransitNetwork(data["name"], data.get("transfer_minutes", 0))
        positions = data.get("stations", {})
        lines = data["lines"]
    except KeyError as missing:
        raise MapFormatError(f"map is missing the {missing} field") from None

    for station, position in positions.items():
        network.add_station(station, tuple(position))

    for line in lines:
        _add_line(network, line, positions)

    return network


def _add_line(network, line, positions):
    name = line["name"]
    stops = line["stops"]
    minutes = line["minutes"]

    if len(stops) < 2:
        raise MapFormatError(f"line {name} needs at least two stops")
    if len(minutes) != len(stops) - 1:
        raise MapFormatError(
            f"line {name} has {len(stops)} stops, so it needs "
            f"{len(stops) - 1} ride times, got {len(minutes)}"
        )
    if positions:
        unknown = [s for s in stops if s not in positions]
        if unknown:
            raise MapFormatError(f"line {name} uses stations with no position: {unknown}")

    for a, b, ride in zip(stops, stops[1:], minutes):
        network.add_connection(a, b, ride, name)
    network.line_colors[name] = line.get("color", "#555555")
