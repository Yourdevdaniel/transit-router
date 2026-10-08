"""Route searches over a TransitNetwork."""

import heapq
import itertools
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
            return _build_route(network, came_from, start, goal)
        for ride in network.neighbors(station):
            if ride.to not in came_from:
                came_from[ride.to] = (station, ride)
                queue.append(ride.to)

    raise NoRouteError(f"no route from {start} to {goal}")


def fastest_trip(network, start, goal):
    """Dijkstra's algorithm, where a node is (station, line) instead of
    just a station.

    Changing lines costs network.transfer_minutes, but that cost depends
    on which line you arrived on, and a plain station graph forgets that.
    Searching over (station, line) pairs lets the change be an edge cost
    like any other, so Dijkstra's usual guarantee still holds: ride and
    change times are never negative, so once a pair comes out of the heap
    its time is final.
    """
    _check_stations(network, start, goal)

    origin = (start, None)  # standing on the platform, not on a train yet
    best = {origin: 0}
    came_from = {origin: None}  # (station, line) -> (previous pair, ride)
    done = set()
    order = itertools.count()  # tie-breaker so heapq never compares None to a str
    heap = [(0, next(order), origin)]
    while heap:
        minutes, _, state = heapq.heappop(heap)
        if state in done:
            continue  # an older, slower entry for a pair we already settled
        done.add(state)
        station, line = state
        if station == goal:
            return _build_route(network, came_from, start, state)
        for ride in network.neighbors(station):
            arrival = minutes + ride.minutes
            if line is not None and ride.line != line:
                arrival += network.transfer_minutes
            nxt = (ride.to, ride.line)
            if arrival < best.get(nxt, float("inf")):
                best[nxt] = arrival
                came_from[nxt] = (state, ride)
                heapq.heappush(heap, (arrival, next(order), nxt))

    raise NoRouteError(f"no route from {start} to {goal}")


def _build_route(network, came_from, start, end):
    """Walk came_from back from `end`. Keys are stations for BFS and
    (station, line) pairs for Dijkstra; only the rides matter here."""
    rides = []
    step = came_from[end]
    while step is not None:
        previous, ride = step
        rides.append(ride)
        step = came_from[previous]
    rides.reverse()
    stops = [start] + [ride.to for ride in rides]
    return Route(stops, rides, network.transfer_minutes)


def _check_stations(network, start, goal):
    # neighbors() raises UnknownStationError for names that aren't on the map
    network.neighbors(start)
    network.neighbors(goal)
