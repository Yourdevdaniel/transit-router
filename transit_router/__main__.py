"""Command line entry point: python -m transit_router FROM TO"""

import argparse
import difflib
import os
import sys

from .itinerary import describe
from .loader import load_network
from .routing import NoRouteError, fastest_trip, fewest_stops
from .svg_map import render_svg

DEFAULT_MAP = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")

SEARCHES = {
    "time": ("fastest trip", fastest_trip),
    "stops": ("fewest stops", fewest_stops),
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="transit_router", description="Plan a trip on a metro map."
    )
    parser.add_argument("origin", nargs="?", help="station to start from")
    parser.add_argument("destination", nargs="?", help="station to go to")
    parser.add_argument(
        "--by", choices=["time", "stops", "both"], default="both",
        help="what to optimise for (default: show both)",
    )
    parser.add_argument("--map", default=DEFAULT_MAP, help="map file (JSON)")
    parser.add_argument("--list", action="store_true", help="list all stations")
    parser.add_argument(
        "--svg", metavar="FILE",
        help="also save the map with the route highlighted (the fastest one when showing both)",
    )
    args = parser.parse_args(argv)

    network = load_network(args.map)

    if args.list:
        for station in network.stations():
            print(f"{station:<12} {', '.join(network.lines_at(station))}")
        return 0

    if not (args.origin and args.destination):
        parser.error("give an origin and a destination, or use --list")

    try:
        origin = resolve_station(network, args.origin)
        destination = resolve_station(network, args.destination)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    modes = ["time", "stops"] if args.by == "both" else [args.by]
    for i, mode in enumerate(modes):
        label, search = SEARCHES[mode]
        try:
            route = search(network, origin, destination)
        except NoRouteError as error:
            print(error, file=sys.stderr)
            return 1
        if i > 0:
            print()
        print(describe(route, f"{network.name}: {origin} -> {destination} ({label})"))
        if args.svg and i == 0:
            title = f"{label.capitalize()}: {origin} to {destination} ({route.total_minutes} min)"
            with open(args.svg, "w", encoding="utf-8") as f:
                f.write(render_svg(network, route, title))
    if args.svg:
        print(f"\nMap saved to {args.svg}")
    return 0


def resolve_station(network, name):
    """Match a typed name to a station, ignoring case and extra spaces."""
    wanted = " ".join(name.split()).lower()
    for station in network.stations():
        if station.lower() == wanted:
            return station

    close = difflib.get_close_matches(name, network.stations(), n=3, cutoff=0.5)
    hint = f" Did you mean: {', '.join(close)}?" if close else ""
    raise ValueError(f"Unknown station '{name}'.{hint}")


if __name__ == "__main__":
    sys.exit(main())
