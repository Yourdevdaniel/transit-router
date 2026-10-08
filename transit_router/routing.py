"""Route searches over a TransitNetwork."""

from collections import deque
from dataclasses import dataclass


class NoRouteError(Exception):
    """Raised when the two stations are not connected at all."""


@dataclass
class Route:
    """A trip as a list of stations plus the ride used between each pair.

    rides[i] is the connection taken from stops[i] to stops[i + 1].
    """

    stops: list
    rides: list
    transfer_minutes: int = 0

    @property
    def stop_count(self):
        return len(self.rides)

    @property
    def ride_minutes(self):
        return sum(ride.minutes for ride in self.rides)

    @property
    def transfers(self):
        return sum(1 for a, b in zip(self.rides, self.rides[1:]) if a.line != b.line)

    @property
    def total_minutes(self):
        return self.ride_minutes + self.transfers * self.transfer_minutes


def fewest_stops(network, start, goal):
    """Breadth-first search: the first time BFS reaches the goal, it has
    used the smallest possible number of rides, because it explores the
    map one "ring" of stations at a time."""
    _check_stations(network, start, goal)

    came_from = {start: None}  # station -> (previous station, ride used)
    queue = deque([start])
    while queue:
        station = queue.popleft()
        if station == goal:
            return _build_route(network, came_from, goal)
        for ride in network.neighbors(station):
            if ride.to not in came_from:
                came_from[ride.to] = (station, ride)
                queue.append(ride.to)

    raise NoRouteError(f"no route from {start} to {goal}")


def _build_route(network, came_from, goal):
    stops, rides = [goal], []
    step = came_from[goal]
    while step is not None:
        previous, ride = step
        stops.append(previous)
        rides.append(ride)
        step = came_from[previous]
    stops.reverse()
    rides.reverse()
    return Route(stops, rides, network.transfer_minutes)


def _check_stations(network, start, goal):
    # neighbors() raises UnknownStationError for names that aren't on the map
    network.neighbors(start)
    network.neighbors(goal)
