import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from transit_router.__main__ import main, resolve_station
from transit_router.itinerary import describe, split_into_legs
from transit_router.loader import load_network
from transit_router.routing import fewest_stops

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")


class ItineraryTest(unittest.TestCase):
    def setUp(self):
        self.net = load_network(DATA)

    def test_rides_on_the_same_line_become_one_leg(self):
        route = fewest_stops(self.net, "Northpark", "Harbor")
        legs = split_into_legs(route)
        self.assertEqual(len(legs), 1)
        self.assertEqual(legs[0].line, "Blue")
        self.assertEqual(legs[0].stop_count, 4)
        self.assertEqual(legs[0].minutes, 13)

    def test_a_line_change_starts_a_new_leg(self):
        route = fewest_stops(self.net, "Old Town", "Eastfield")
        legs = split_into_legs(route)
        self.assertEqual([leg.line for leg in legs], ["Blue", "Ferry"])
        self.assertEqual(legs[1].stations, ["Harbor", "Eastfield"])

    def test_describe_shows_the_change_and_the_total(self):
        text = describe(fewest_stops(self.net, "Old Town", "Eastfield"), "trip")
        self.assertIn("change at Harbor", text)
        self.assertIn("Total: 28 min, 2 stops, 1 change", text)

    def test_describe_an_empty_route(self):
        text = describe(fewest_stops(self.net, "Market", "Market"), "trip")
        self.assertIn("already there", text)


class CommandLineTest(unittest.TestCase):
    def setUp(self):
        self.net = load_network(DATA)

    def test_station_names_ignore_case_and_spaces(self):
        self.assertEqual(resolve_station(self.net, "  old   TOWN "), "Old Town")

    def test_typo_gets_a_suggestion(self):
        with self.assertRaisesRegex(ValueError, "Did you mean: Library"):
            resolve_station(self.net, "Libary")

    def test_main_prints_both_searches_by_default(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["Northpark", "Harbor"])
        self.assertEqual(code, 0)
        self.assertIn("(fastest trip)", out.getvalue())
        self.assertIn("(fewest stops)", out.getvalue())

    def test_main_rejects_unknown_station(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["Northpark", "Atlantis"])
        self.assertEqual(code, 2)
        self.assertIn("Unknown station 'Atlantis'", err.getvalue())

    def test_main_saves_the_map_when_asked(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "trip.svg")
            with redirect_stdout(io.StringIO()):
                main(["Old Town", "Eastfield", "--svg", path])
            with open(path, encoding="utf-8") as f:
                self.assertIn("Fastest trip: Old Town to Eastfield (19 min)", f.read())


if __name__ == "__main__":
    unittest.main()
