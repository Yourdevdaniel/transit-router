"""The metro network as an undirected, weighted graph.

Stations are the vertices. Every pair of consecutive stops on a line is an
edge, stored in both directions because trains run both ways. Each edge
remembers which line it belongs to and how many minutes the ride takes.

I store the graph as an adjacency list (a dict from station name to a list
of connections) instead of an adjacency matrix: a metro map is sparse, since
most stations only touch two or three others, so a matrix would be mostly
empty cells.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    """One direct ride between two neighbouring stations on a line."""

    to: str
    minutes: int
    line: str


@dataclass(frozen=True)
class LineStyle:
    """How a line is drawn on the map. Only the SVG renderer uses this."""

    color: str = "#555555"
    offset: int = 0  # pixels sideways, for lines that share a corridor
    dashed: bool = False


class UnknownStationError(KeyError):
    """Raised when a station name is not on the map."""


class TransitNetwork:
    def __init__(self, name="Metro", transfer_minutes=0):
        self.name = name
        self.transfer_minutes = transfer_minutes
        self._adjacency = {}
        self._positions = {}
        self.line_styles = {}

    def add_station(self, station, position=None):
        if station not in self._adjacency:
            self._adjacency[station] = []
        if position is not None:
            self._positions[station] = position

    def add_connection(self, a, b, minutes, line):
        if minutes <= 0:
            raise ValueError(f"ride {a} -> {b} must take a positive number of minutes")
        if a == b:
            raise ValueError(f"a connection can't start and end at {a}")
        self.add_station(a)
        self.add_station(b)
        self._adjacency[a].append(Connection(b, minutes, line))
        self._adjacency[b].append(Connection(a, minutes, line))

    def neighbors(self, station):
        self._check(station)
        return list(self._adjacency[station])

    def stations(self):
        return sorted(self._adjacency)

    def position(self, station):
        self._check(station)
        return self._positions.get(station)

    def lines_at(self, station):
        return sorted({c.line for c in self.neighbors(station)})

    def __contains__(self, station):
        return station in self._adjacency

    def __len__(self):
        return len(self._adjacency)

    def _check(self, station):
        if station not in self._adjacency:
            raise UnknownStationError(station)
