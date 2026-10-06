import os
import unittest

from transit_router.loader import MapFormatError, load_network, network_from_dict

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")


def small_map(**changes):
    data = {
        "name": "Tiny",
        "transfer_minutes": 2,
        "stations": {"A": [0, 0], "B": [1, 0], "C": [2, 0]},
        "lines": [{"name": "Red", "stops": ["A", "B", "C"], "minutes": [3, 4]}],
    }
    data.update(changes)
    return data


class LoaderTest(unittest.TestCase):
    def test_consecutive_stops_become_connections(self):
        net = network_from_dict(small_map())
        self.assertEqual([c.to for c in net.neighbors("B")], ["A", "C"])
        self.assertEqual(net.transfer_minutes, 2)

    def test_positions_are_kept_for_drawing(self):
        net = network_from_dict(small_map())
        self.assertEqual(net.position("C"), (2, 0))

    def test_wrong_number_of_ride_times(self):
        bad = small_map(lines=[{"name": "Red", "stops": ["A", "B", "C"], "minutes": [3]}])
        with self.assertRaisesRegex(MapFormatError, "needs 2 ride times, got 1"):
            network_from_dict(bad)

    def test_line_with_a_single_stop(self):
        bad = small_map(lines=[{"name": "Red", "stops": ["A"], "minutes": []}])
        with self.assertRaises(MapFormatError):
            network_from_dict(bad)

    def test_station_without_position(self):
        bad = small_map(lines=[{"name": "Red", "stops": ["A", "Z"], "minutes": [3]}])
        with self.assertRaisesRegex(MapFormatError, "Z"):
            network_from_dict(bad)

    def test_missing_lines_field(self):
        with self.assertRaisesRegex(MapFormatError, "lines"):
            network_from_dict({"name": "Empty"})

    def test_bundled_map_loads(self):
        net = load_network(DATA)
        self.assertEqual(net.name, "Brookhaven Metro")
        self.assertEqual(len(net), 13)
        self.assertEqual(net.lines_at("Central"), ["Blue", "Red", "Yellow"])


if __name__ == "__main__":
    unittest.main()
