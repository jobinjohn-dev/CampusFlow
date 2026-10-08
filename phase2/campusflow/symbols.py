"""Symbol records and schedule-overlap helpers for CampusFlow."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EventSymbol:
    name: str
    date: str
    start_time: str
    end_time: str
    cancelled: bool = False


@dataclass(frozen=True)
class ReservationSymbol:
    resource: str
    event: str
    capacity: int


@dataclass(frozen=True)
class AssignmentSymbol:
    item: str
    event: str


@dataclass
class SymbolTable:
    events: dict[str, EventSymbol] = field(default_factory=dict)
    reservations: list[ReservationSymbol] = field(default_factory=list)
    assignments: list[AssignmentSymbol] = field(default_factory=list)

    def lookup_event(self, name: str) -> EventSymbol | None:
        return self.events.get(name)

    def add_event(self, symbol: EventSymbol) -> None:
        self.events[symbol.name] = symbol

    def add_reservation(self, symbol: ReservationSymbol) -> None:
        self.reservations.append(symbol)

    def add_assignment(self, symbol: AssignmentSymbol) -> None:
        self.assignments.append(symbol)

    def cancel_event(self, name: str) -> None:
        event = self.events[name]
        event.cancelled = True
        self.reservations = [
            reservation
            for reservation in self.reservations
            if reservation.event != name
        ]
        self.assignments = [
            assignment
            for assignment in self.assignments
            if assignment.event != name
        ]


def intervals_overlap(
    left_date: str,
    left_start: str,
    left_end: str,
    right_date: str,
    right_start: str,
    right_end: str,
) -> bool:
    """Return whether two half-open event intervals overlap."""
    if left_date != right_date:
        return False
    left_start_time = datetime.strptime(left_start, "%H:%M").time()
    left_end_time = datetime.strptime(left_end, "%H:%M").time()
    right_start_time = datetime.strptime(right_start, "%H:%M").time()
    right_end_time = datetime.strptime(right_end, "%H:%M").time()
    return left_start_time < right_end_time and right_start_time < left_end_time
