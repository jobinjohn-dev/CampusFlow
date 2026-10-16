"""Semantic validation and symbol-table construction for CampusFlow."""

from dataclasses import dataclass
from datetime import datetime

from .ast_nodes import (
    AssignStatement,
    CancelStatement,
    EventStatement,
    IfStatement,
    Program,
    ReserveStatement,
    Statement,
)
from .symbols import (
    AssignmentSymbol,
    EventSymbol,
    ReservationSymbol,
    SymbolTable,
    intervals_overlap,
)


@dataclass(frozen=True)
class SemanticDiagnostic:
    message: str
    line: int
    column: int


@dataclass(frozen=True)
class SemanticResult:
    symbols: SymbolTable
    errors: tuple[SemanticDiagnostic, ...]


class SemanticAnalyzer:
    """Validate an AST in source order and build its definite symbols."""

    def __init__(self):
        self.symbols = SymbolTable()
        self.errors: list[SemanticDiagnostic] = []
        self.capacity_defined = False

    def analyze(self, program: Program) -> SemanticResult:
        for statement in program.statements:
            self._analyze_statement(statement, commit=True)
        return SemanticResult(self.symbols, tuple(self.errors))

    def _analyze_statement(self, statement: Statement, commit: bool) -> None:
        if isinstance(statement, EventStatement):
            self._analyze_event(statement, commit)
        elif isinstance(statement, ReserveStatement):
            self._analyze_reserve(statement, commit)
        elif isinstance(statement, AssignStatement):
            self._analyze_assign(statement, commit)
        elif isinstance(statement, CancelStatement):
            self._analyze_cancel(statement, commit)
        elif isinstance(statement, IfStatement):
            self._analyze_if(statement)

    def _analyze_event(self, statement: EventStatement, commit: bool) -> None:
        if self.symbols.lookup_event(statement.name) is not None:
            self._error(f"Duplicate event '{statement.name}'", statement)
            return
        start = datetime.strptime(statement.start_time, "%H:%M").time()
        end = datetime.strptime(statement.end_time, "%H:%M").time()
        if end <= start:
            self._error(
                f"Event '{statement.name}' end time must be later than start time",
                statement,
            )
            return
        if commit:
            self.symbols.add_event(EventSymbol(
                statement.name,
                statement.date,
                statement.start_time,
                statement.end_time,
            ))

    def _analyze_reserve(
        self, statement: ReserveStatement, commit: bool
    ) -> None:
        event = self._active_event(statement.event, statement)
        if event is None:
            return
        if statement.capacity <= 0:
            self._error("Capacity must be greater than zero", statement)
            return
        if any(
            reservation.resource == statement.resource
            and reservation.event == statement.event
            for reservation in self.symbols.reservations
        ):
            self._error(
                f"Resource '{statement.resource}' is already reserved for "
                f"event '{statement.event}'",
                statement,
            )
            return
        for reservation in self.symbols.reservations:
            if reservation.resource != statement.resource:
                continue
            other = self.symbols.lookup_event(reservation.event)
            if other is not None and intervals_overlap(
                event.date,
                event.start_time,
                event.end_time,
                other.date,
                other.start_time,
                other.end_time,
            ):
                self._error(
                    f"Resource '{statement.resource}' conflicts with event "
                    f"'{reservation.event}'",
                    statement,
                )
                return
        if commit:
            self.symbols.add_reservation(ReservationSymbol(
                statement.resource, statement.event, statement.capacity
            ))
            self.capacity_defined = True

    def _analyze_assign(self, statement: AssignStatement, commit: bool) -> None:
        event = self._active_event(statement.event, statement)
        if event is None:
            return
        if any(
            assignment.item == statement.item
            and assignment.event == statement.event
            for assignment in self.symbols.assignments
        ):
            self._error(
                f"Item '{statement.item}' is already assigned to event "
                f"'{statement.event}'",
                statement,
            )
            return
        for assignment in self.symbols.assignments:
            if assignment.item != statement.item:
                continue
            other = self.symbols.lookup_event(assignment.event)
            if other is not None and intervals_overlap(
                event.date,
                event.start_time,
                event.end_time,
                other.date,
                other.start_time,
                other.end_time,
            ):
                self._error(
                    f"Item '{statement.item}' conflicts with event "
                    f"'{assignment.event}'",
                    statement,
                )
                return
        if commit:
            self.symbols.add_assignment(
                AssignmentSymbol(statement.item, statement.event)
            )

    def _analyze_cancel(self, statement: CancelStatement, commit: bool) -> None:
        event = self.symbols.lookup_event(statement.event)
        if event is None:
            self._error(f"Undeclared event '{statement.event}'", statement)
            return
        if event.cancelled:
            self._error(
                f"Event '{statement.event}' is already cancelled", statement
            )
            return
        if commit:
            self.symbols.cancel_event(statement.event)

    def _analyze_if(self, statement: IfStatement) -> None:
        if not self.capacity_defined:
            self._error(
                "Built-in capacity is not available before a successful reservation",
                statement,
            )
        self._analyze_statement(statement.body, commit=False)

    def _active_event(
        self,
        name: str,
        statement: ReserveStatement | AssignStatement,
    ) -> EventSymbol | None:
        event = self.symbols.lookup_event(name)
        if event is None:
            self._error(f"Undeclared event '{name}'", statement)
            return None
        if event.cancelled:
            self._error(f"Cannot use cancelled event '{name}'", statement)
            return None
        return event

    def _error(self, message: str, statement: Statement) -> None:
        self.errors.append(SemanticDiagnostic(
            message, statement.line, statement.column
        ))
