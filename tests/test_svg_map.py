import os
import unittest
import xml.etree.ElementTree as ET

from transit_router.loader import load_network
from transit_router.routing import fastest_trip
from transit_router.svg_map import _shift, render_svg

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "brookhaven.json")
SVG = "{http://www.w3.org/2000/svg}"


class SvgMapTest(unittest.TestCase):
    def setUp(self):
        self.net = load_network(DATA)

    def test_output_is_valid_xml_with_every_station(self):
        root = ET.fromstring(render_svg(self.net))
        labels = {t.text for t in root.iter(f"{SVG}text")}
        self.assertTrue(set(self.net.stations()) <= labels)
        self.assertEqual(len(list(root.iter(f"{SVG}circle"))), len(self.net))

    def test_route_is_drawn_on_top_of_the_faded_map(self):
        route = fastest_trip(self.net, "Old Town", "Eastfield")
        root = ET.fromstring(render_svg(self.net, route, "Old Town to Eastfield"))
        faded = root.find(f"{SVG}g")
        self.assertEqual(faded.get("opacity"), "0.22")
        # each ride is drawn twice on top: a white outline and the coloured line
        on_top = [el for el in root if el.tag == f"{SVG}line" and el.get("stroke-width") == "10"]
        self.assertEqual(len(on_top), route.stop_count)

    def test_names_are_escaped(self):
        self.net.add_connection("Arts & Crafts", "Central", 2, "Red")
        self.net.add_station("Arts & Crafts", (3, 3))
        ET.fromstring(render_svg(self.net))  # would raise on a raw "&"

    def test_shift_keeps_the_same_side_in_both_directions(self):
        forward = _shift((0, 0), (10, 0), 5)
        backward = _shift((10, 0), (0, 0), 5)
        self.assertEqual(forward[0][1], backward[0][1])


if __name__ == "__main__":
    unittest.main()
