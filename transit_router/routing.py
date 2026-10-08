"""Route searches over a TransitNetwork."""

import heapq
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


def fastest_trip(network, start, goal):
    """Dijkstra's algorithm: always expand the station with the smallest
    known travel time next. Ride times are never negative, so once a
    station comes out of the heap its time is final."""
    _check_stations(network, start, goal)

    best = {start: 0}
    came_from = {start: None}
    done = set()
    heap = [(0, start)]
    while heap:
        minutes, station = heapq.heappop(heap)
        if station in done:
            continue  # an older, slower entry for a station we already settled
        done.add(station)
        if station == goal:
            return _build_route(network, came_from, goal)
        for ride in network.neighbors(station):
            arrival = minutes + ride.minutes
            if arrival < best.get(ride.to, float("inf")):
                best[ride.to] = arrival
                came_from[ride.to] = (station, ride)
                heapq.heappush(heap, (arrival, ride.to))

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
