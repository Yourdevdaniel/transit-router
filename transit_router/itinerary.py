"""Turn a Route into something a person can follow.

A route is stored ride by ride, but nobody reads directions that way.
Consecutive rides on the same line are grouped into one leg
("Red: Central -> Eastfield, 3 stops"), with a change between legs.
"""

from dataclasses import dataclass


@dataclass
class Leg:
    line: str
    stations: list  # boarding station first, getting-off station last
    minutes: int

    @property
    def stop_count(self):
        return len(self.stations) - 1


def split_into_legs(route):
    legs = []
    for i, ride in enumerate(route.rides):
        if legs and legs[-1].line == ride.line:
            legs[-1].stations.append(ride.to)
            legs[-1].minutes += ride.minutes
        else:
            legs.append(Leg(ride.line, [route.stops[i], ride.to], ride.minutes))
    return legs


def describe(route, title):
    lines = [title, ""]
    legs = split_into_legs(route)
    if not legs:
        lines.append("  You are already there.")
        return "\n".join(lines)

    for i, leg in enumerate(legs):
        if i > 0:
            lines.append(_row("", f"change at {leg.stations[0]}", "", route.transfer_minutes))
        stops = f"{leg.stop_count} stop" + ("" if leg.stop_count == 1 else "s")
        trip = f"{leg.stations[0]} -> {leg.stations[-1]}"
        lines.append(_row(leg.line, trip, stops, leg.minutes))

    changes = route.transfers
    lines.append("")
    lines.append(
        f"  Total: {route.total_minutes} min, {route.stop_count} stops, "
        f"{changes} change" + ("" if changes == 1 else "s")
    )
    return "\n".join(lines)


def _row(line, trip, stops, minutes):
    return f"  {line:<7} {trip:<28} {stops:>8} {minutes:>4} min"
