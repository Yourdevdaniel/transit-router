"""Check both searches against brute force on every pair of stations.

The bundled map is small enough to list every simple path between two
stations with a recursive DFS, price each one, and take the minimum.
Slow (exponential in general), but obviously correct - a good referee
for the clever versions.
"""

import os
import unittest

from transit_router.loader import load_network
from transit_router.routing import Route, fastest_trip, fewest_stops

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")


def all_simple_paths(network, station, goal, visited, rides):
    if station == goal:
        yield list(rides)
        return
    for ride in network.neighbors(station):
        if ride.to not in visited:
            visited.add(ride.to)
            rides.append(ride)
            yield from all_simple_paths(network, ride.to, goal, visited, rides)
            rides.pop()
            visited.remove(ride.to)


class BruteForceTest(unittest.TestCase):
    def test_every_pair_of_stations(self):
        net = load_network(DATA)
        for start in net.stations():
            for goal in net.stations():
                with self.subTest(start=start, goal=goal):
                    candidates = [
                        Route([start] + [r.to for r in rides], rides, net.transfer_minutes)
                        for rides in all_simple_paths(net, start, goal, {start}, [])
                    ]
                    self.assertEqual(
                        fastest_trip(net, start, goal).total_minutes,
                        min(c.total_minutes for c in candidates),
                    )
                    self.assertEqual(
                        fewest_stops(net, start, goal).stop_count,
                        min(c.stop_count for c in candidates),
                    )


if __name__ == "__main__":
    unittest.main()
