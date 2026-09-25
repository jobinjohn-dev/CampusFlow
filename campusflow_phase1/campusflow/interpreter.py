"""In-memory execution engine for CampusFlow intermediate code."""

from dataclasses import dataclass, field
import operator

from .ir import IRProgram, Instruction
from .symbols import intervals_overlap


@dataclass
class RuntimeEvent:
    name: str
    date: str
    start_time: str
    end_time: str
    cancelled: bool = False


@dataclass(frozen=True)
class RuntimeReservation:
    resource: str
    event: str
    capacity: int


@dataclass(frozen=True)
class RuntimeAssignment:
    item: str
    event: str


@dataclass
class RuntimeState:
    events: dict[str, RuntimeEvent] = field(default_factory=dict)
    reservations: list[RuntimeReservation] = field(default_factory=list)
    assignments: list[RuntimeAssignment] = field(default_factory=list)
    last_capacity: int | None = None
    execution_log: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuntimeDiagnostic:
    message: str
    line: int
    column: int


@dataclass(frozen=True)
class ExecutionResult:
    state: RuntimeState
    errors: tuple[RuntimeDiagnostic, ...]


COMPARISONS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class Interpreter:
    """Execute CampusFlow IR while protecting runtime invariants."""

    def execute(self, program: IRProgram) -> ExecutionResult:
        state = RuntimeState()
        labels: dict[str, int] = {}
        for index, instruction in enumerate(program.instructions):
            if instruction.opcode != "LABEL":
                continue
            try:
                self._validate_operands(instruction, (str,))
                label = instruction.operands[0]
                if label in labels:
                    raise ValueError(f"Duplicate label '{label}'")
                labels[label] = index
            except (ValueError, TypeError) as error:
                return ExecutionResult(state, (RuntimeDiagnostic(
                    str(error), instruction.line, instruction.column
                ),))
        pointer = 0
        while pointer < len(program.instructions):
            instruction = program.instructions[pointer]
            try:
                if instruction.opcode == "CREATE_EVENT":
                    self._validate_operands(instruction, (str, str, str, str))
                    self._create_event(state, instruction)
                elif instruction.opcode == "RESERVE_RESOURCE":
                    self._validate_operands(instruction, (str, str, int))
                    self._reserve_resource(state, instruction)
                elif instruction.opcode == "ASSIGN_ITEM":
                    self._validate_operands(instruction, (str, str))
                    self._assign_item(state, instruction)
                elif instruction.opcode == "CANCEL_EVENT":
                    self._validate_operands(instruction, (str,))
                    self._cancel_event(state, instruction)
                elif instruction.opcode == "JUMP_IF_FALSE":
                    self._validate_operands(instruction, (str, int, str))
                    comparison, right, label = instruction.operands
                    if state.last_capacity is None:
                        raise ValueError(
                            "Built-in capacity is not available at runtime"
                        )
                    if comparison not in COMPARISONS:
                        raise ValueError(
                            f"Unknown comparison operator '{comparison}'"
                        )
                    if label not in labels:
                        raise ValueError(f"Unknown label '{label}'")
                    if not COMPARISONS[comparison](state.last_capacity, right):
                        pointer = labels[label] + 1
                        continue
                elif instruction.opcode == "LABEL":
                    pass
                else:
                    raise ValueError(
                        f"Unknown opcode '{instruction.opcode}'"
                    )
            except (ValueError, TypeError, KeyError, IndexError) as error:
                return ExecutionResult(state, (RuntimeDiagnostic(
                    str(error), instruction.line, instruction.column
                ),))
            pointer += 1
        return ExecutionResult(state, ())

    @staticmethod
    def _validate_operands(
        instruction: Instruction, expected_types: tuple[type, ...]
    ) -> None:
        if len(instruction.operands) != len(expected_types):
            raise ValueError(
                f"Opcode {instruction.opcode} expects "
                f"{len(expected_types)} operands, got "
                f"{len(instruction.operands)}"
            )
        for index, (value, expected_type) in enumerate(
            zip(instruction.operands, expected_types), start=1
        ):
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Operand {index} for {instruction.opcode} must be "
                    f"{expected_type.__name__}"
                )

    @staticmethod
    def _create_event(state: RuntimeState, instruction: Instruction) -> None:
        name, date, start, end = instruction.operands
        if name in state.events:
            raise ValueError(f"Duplicate event '{name}'")
        state.events[name] = RuntimeEvent(name, date, start, end)
        state.execution_log.append(f"Created event {name}")

    def _reserve_resource(
        self, state: RuntimeState, instruction: Instruction
    ) -> None:
        resource, event_name, capacity = instruction.operands
        event = self._active_event(state, event_name)
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero")
        if any(
            item.resource == resource and item.event == event_name
            for item in state.reservations
        ):
            raise ValueError(
                f"Resource '{resource}' is already reserved for event "
                f"'{event_name}'"
            )
        for reservation in state.reservations:
            if reservation.resource != resource:
                continue
            other = state.events[reservation.event]
            if intervals_overlap(
                event.date,
                event.start_time,
                event.end_time,
                other.date,
                other.start_time,
                other.end_time,
            ):
                raise ValueError(
                    f"Resource '{resource}' conflicts with event "
                    f"'{reservation.event}'"
                )
        state.reservations.append(
            RuntimeReservation(resource, event_name, capacity)
        )
        state.last_capacity = capacity
        state.execution_log.append(
            f"Reserved {resource} for {event_name} with capacity {capacity}"
        )

    def _assign_item(self, state: RuntimeState, instruction: Instruction) -> None:
        item, event_name = instruction.operands
        event = self._active_event(state, event_name)
        if any(
            assignment.item == item and assignment.event == event_name
            for assignment in state.assignments
        ):
            raise ValueError(
                f"Item '{item}' is already assigned to event '{event_name}'"
            )
        for assignment in state.assignments:
            if assignment.item != item:
                continue
            other = state.events[assignment.event]
            if intervals_overlap(
                event.date,
                event.start_time,
                event.end_time,
                other.date,
                other.start_time,
                other.end_time,
            ):
                raise ValueError(
                    f"Item '{item}' conflicts with event '{assignment.event}'"
                )
        state.assignments.append(RuntimeAssignment(item, event_name))
        state.execution_log.append(f"Assigned {item} to {event_name}")

    @staticmethod
    def _cancel_event(state: RuntimeState, instruction: Instruction) -> None:
        (event_name,) = instruction.operands
        event = state.events.get(event_name)
        if event is None:
            raise ValueError(f"Undeclared event '{event_name}'")
        if event.cancelled:
            raise ValueError(f"Event '{event_name}' is already cancelled")
        event.cancelled = True
        state.reservations = [
            reservation
            for reservation in state.reservations
            if reservation.event != event_name
        ]
        state.assignments = [
            assignment
            for assignment in state.assignments
            if assignment.event != event_name
        ]
        state.execution_log.append(f"Cancelled event {event_name}")

    @staticmethod
    def _active_event(state: RuntimeState, name: str) -> RuntimeEvent:
        event = state.events.get(name)
        if event is None:
            raise ValueError(f"Undeclared event '{name}'")
        if event.cancelled:
            raise ValueError(f"Cannot use cancelled event '{name}'")
        return event


def format_runtime(state: RuntimeState) -> str:
    """Return a deterministic human-readable runtime report."""
    lines = ["FINAL RUNTIME STATE", "-------------------"]
    for event in state.events.values():
        status = "CANCELLED" if event.cancelled else "ACTIVE"
        lines.append(
            f"{event.name} [{status}] {event.date} "
            f"{event.start_time}-{event.end_time}"
        )
        for reservation in state.reservations:
            if reservation.event == event.name:
                lines.append(
                    f"  RESERVATION {reservation.resource} "
                    f"capacity={reservation.capacity}"
                )
        for assignment in state.assignments:
            if assignment.event == event.name:
                lines.append(f"  ASSIGNMENT {assignment.item}")
    lines.extend(["", "EXECUTION LOG", "-------------"])
    lines.extend(f"- {message}" for message in state.execution_log)
    return "\n".join(lines)
