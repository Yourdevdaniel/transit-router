import unittest

from transit_router.network import Connection, TransitNetwork, UnknownStationError


class TransitNetworkTest(unittest.TestCase):
    def setUp(self):
        self.net = TransitNetwork("Test Metro")
        self.net.add_connection("A", "B", 3, "Red")
        self.net.add_connection("B", "C", 4, "Red")

    def test_connections_go_both_ways(self):
        self.assertIn(Connection("B", 3, "Red"), self.net.neighbors("A"))
        self.assertIn(Connection("A", 3, "Red"), self.net.neighbors("B"))

    def test_stations_are_added_implicitly_by_connections(self):
        self.assertEqual(self.net.stations(), ["A", "B", "C"])
        self.assertEqual(len(self.net), 3)
        self.assertIn("C", self.net)

    def test_a_station_can_be_served_by_several_lines(self):
        self.net.add_connection("B", "D", 2, "Blue")
        self.assertEqual(self.net.lines_at("B"), ["Blue", "Red"])

    def test_unknown_station_raises(self):
        with self.assertRaises(UnknownStationError):
            self.net.neighbors("Nowhere")

    def test_rejects_non_positive_minutes(self):
        with self.assertRaises(ValueError):
            self.net.add_connection("C", "D", 0, "Red")

    def test_rejects_self_loops(self):
        with self.assertRaises(ValueError):
            self.net.add_connection("A", "A", 2, "Red")

    def test_neighbors_returns_a_copy(self):
        self.net.neighbors("A").clear()
        self.assertEqual(len(self.net.neighbors("A")), 1)


if __name__ == "__main__":
    unittest.main()
