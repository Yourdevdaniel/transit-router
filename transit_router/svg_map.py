"""Draw the network (and optionally one route) as an SVG image.

Plain string building - SVG is just XML text, so no plotting library is
needed. Coordinates in the map file are grid units; SCALE turns them
into pixels.
"""

import math
from html import escape

from .network import LineStyle

SCALE = 70
MARGIN = 70
TOP = 70  # room for the title


def render_svg(network, route=None, title=None):
    """Return the SVG source for the map. If a route is given, the rest
    of the network is faded out and the route is drawn on top."""
    xs = [network.position(s)[0] for s in network.stations()]
    ys = [network.position(s)[1] for s in network.stations()]
    min_x, min_y = min(xs), min(ys)
    width = (max(xs) - min_x) * SCALE + 2 * MARGIN + 60
    height = (max(ys) - min_y) * SCALE + 2 * MARGIN + TOP

    def point(station):
        x, y = network.position(station)
        return MARGIN + (x - min_x) * SCALE, TOP + MARGIN + (y - min_y) * SCALE

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
        f'<rect width="100%" height="100%" fill="#fbfaf7"/>',
        f'<text x="{MARGIN - 30}" y="42" font-size="22" font-weight="700" fill="#222">'
        f"{escape(title or network.name)}</text>",
    ]

    fade = route is not None and route.rides
    parts.append(f'<g opacity="{0.22 if fade else 1}">')
    for a, b, line in _segments(network):
        parts.append(_segment(point(a), point(b), network, line, width_px=7))
    parts.append("</g>")

    if fade:
        for station, ride in zip(route.stops, route.rides):
            parts.append(
                _segment(point(station), point(ride.to), network, ride.line, width_px=10,
                         outline=True)
            )

    on_route = set(route.stops) if fade else set()
    ends = {route.stops[0], route.stops[-1]} if fade else set()
    for station in network.stations():
        x, y = point(station)
        interchange = len(network.lines_at(station)) > 1
        radius = 8 if interchange else 6
        stroke = "#222" if not fade or station in on_route else "#bbb"
        fill = "#222" if station in ends else "#fff"
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius + (2 if station in ends else 0)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{3 if interchange else 2.5}"/>'
        )
        parts.append(_label(network, station, point, faded=fade and station not in on_route))

    parts.append(_legend(network))
    parts.append("</svg>")
    return "\n".join(parts)


def _segments(network):
    """Every edge once (the graph stores each one in both directions)."""
    seen = set()
    for station in network.stations():
        for ride in network.neighbors(station):
            key = (min(station, ride.to), max(station, ride.to), ride.line)
            if key not in seen:
                seen.add(key)
                yield station, ride.to, ride.line


def _segment(p, q, network, line, width_px, outline=False):
    style = network.line_styles.get(line, LineStyle())
    (x1, y1), (x2, y2) = _shift(p, q, style.offset)
    color = style.color
    dash = ' stroke-dasharray="10 8"' if style.dashed else ""
    coords = f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
    under = (f'<line {coords} stroke="#fff" stroke-width="{width_px + 5}" stroke-linecap="round"/>'
             if outline else "")
    return (f'{under}<line {coords} stroke="{color}" stroke-width="{width_px}" '
            f'stroke-linecap="round"{dash}/>')


def _shift(p, q, pixels):
    """Move segment p-q sideways by `pixels`, along its normal vector."""
    if not pixels:
        return p, q
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    # always measure the normal from the left-most end, so a line keeps
    # the same side no matter which direction the edge was stored in
    if (dx, dy) < (0, 0):
        dx, dy = -dx, -dy
    nx, ny = -dy / length * pixels, dx / length * pixels
    return (p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny)


# label directions, as angles in degrees (0 = right, 90 = down)
STRAIGHT = [90, 0, -90, 180]
DIAGONAL = [135, 45, -45, -135]


def _label(network, station, point, faded):
    """Put the name below, right, above or left - the first side with no
    track within 90 degrees of it. Busy interchanges where every straight
    side has a track get the clearest diagonal instead."""
    x, y = point(station)
    track_angles = []
    for ride in network.neighbors(station):
        nx, ny = point(ride.to)
        track_angles.append(math.degrees(math.atan2(ny - y, nx - x)))

    def clearance(angle):
        return min((abs((angle - t + 180) % 360 - 180) for t in track_angles), default=180)

    clear = [a for a in STRAIGHT if clearance(a) >= 90]
    angle = clear[0] if clear else max(DIAGONAL, key=clearance)
    rad = math.radians(angle)
    gap = 16 if angle in STRAIGHT else 22  # diagonal text needs more room
    lx, ly = x + math.cos(rad) * gap, y + math.sin(rad) * gap + 5
    anchor = "middle" if abs(math.cos(rad)) < 0.3 else ("start" if math.cos(rad) > 0 else "end")
    color = "#bbb" if faded else "#222"
    return (f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="14" text-anchor="{anchor}" '
            f'fill="{color}" paint-order="stroke" stroke="#fbfaf7" stroke-width="4">'
            f"{escape(station)}</text>")


def _legend(network):
    items = []
    x = MARGIN - 30
    for line, style in network.line_styles.items():
        dash = ' stroke-dasharray="6 5"' if style.dashed else ""
        items.append(
            f'<line x1="{x}" y1="62" x2="{x + 22}" y2="62" stroke="{style.color}" '
            f'stroke-width="6" stroke-linecap="round"{dash}/>'
            f'<text x="{x + 30}" y="67" font-size="13" fill="#444">{escape(line)}</text>'
        )
        x += 40 + 8 * len(line)
    return "".join(items)
