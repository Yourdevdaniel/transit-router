import os
import unittest

from transit_router.loader import load_network
from transit_router.network import TransitNetwork, UnknownStationError
from transit_router.routing import NoRouteError, fewest_stops

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")


class FewestStopsTest(unittest.TestCase):
    def setUp(self):
        self.net = load_network(DATA)

    def test_route_to_the_same_station_is_empty(self):
        route = fewest_stops(self.net, "Central", "Central")
        self.assertEqual(route.stops, ["Central"])
        self.assertEqual(route.stop_count, 0)
        self.assertEqual(route.total_minutes, 0)

    def test_single_line_trip(self):
        route = fewest_stops(self.net, "Northpark", "Old Town")
        self.assertEqual(route.stops, ["Northpark", "Library", "Central", "Old Town"])
        self.assertEqual(route.stop_count, 3)
        self.assertEqual(route.transfers, 0)

    def test_takes_the_express_when_it_skips_stations(self):
        route = fewest_stops(self.net, "Westgate", "Airport")
        self.assertEqual(route.stops, ["Westgate", "Central", "Riverside", "Airport"])

    def test_ferry_is_the_fewest_stops_to_eastfield(self):
        route = fewest_stops(self.net, "Old Town", "Eastfield")
        self.assertEqual(route.stops, ["Old Town", "Harbor", "Eastfield"])
        # ...but it is a slow one: 4 min + 20 min ferry + 4 min to change
        self.assertEqual(route.total_minutes, 28)

    def test_unknown_station(self):
        with self.assertRaises(UnknownStationError):
            fewest_stops(self.net, "Central", "Atlantis")

    def test_disconnected_stations(self):
        net = TransitNetwork()
        net.add_connection("A", "B", 2, "Red")
        net.add_connection("C", "D", 2, "Blue")
        with self.assertRaises(NoRouteError):
            fewest_stops(net, "A", "D")


if __name__ == "__main__":
    unittest.main()
