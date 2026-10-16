"""Abstract syntax tree nodes for the CampusFlow language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Program:
    statements: tuple[Statement, ...]


@dataclass(frozen=True)
class EventStatement:
    name: str
    date: str
    start_time: str
    end_time: str
    line: int
    column: int


@dataclass(frozen=True)
class ReserveStatement:
    resource: str
    event: str
    capacity: int
    line: int
    column: int


@dataclass(frozen=True)
class AssignStatement:
    item: str
    event: str
    line: int
    column: int


@dataclass(frozen=True)
class CancelStatement:
    event: str
    line: int
    column: int


@dataclass(frozen=True)
class CapacityExpression:
    line: int
    column: int


@dataclass(frozen=True)
class NumberLiteral:
    value: int
    line: int
    column: int


@dataclass(frozen=True)
class ComparisonExpression:
    left: CapacityExpression
    operator: str
    right: NumberLiteral
    line: int
    column: int


@dataclass(frozen=True)
class IfStatement:
    condition: ComparisonExpression
    body: ConditionalStatement
    line: int
    column: int


ConditionalStatement: TypeAlias = (
    ReserveStatement | AssignStatement | CancelStatement
)
Statement: TypeAlias = (
    EventStatement
    | ReserveStatement
    | AssignStatement
    | CancelStatement
    | IfStatement
)


def format_ast(program: Program) -> str:
    """Return a stable indented representation of an AST."""
    lines = ["Program"]
    for statement in program.statements:
        lines.extend(_format_statement(statement, 1))
    return "\n".join(lines)


def _format_statement(statement: Statement, depth: int) -> list[str]:
    indent = "  " * depth
    location = f"@{statement.line}:{statement.column}"
    if isinstance(statement, EventStatement):
        return [
            f"{indent}Event {statement.name} date={statement.date} "
            f"start={statement.start_time} end={statement.end_time} {location}"
        ]
    if isinstance(statement, ReserveStatement):
        return [
            f"{indent}Reserve {statement.resource} for={statement.event} "
            f"capacity={statement.capacity} {location}"
        ]
    if isinstance(statement, AssignStatement):
        return [
            f"{indent}Assign {statement.item} to={statement.event} {location}"
        ]
    if isinstance(statement, CancelStatement):
        return [f"{indent}Cancel {statement.event} {location}"]

    lines = [f"{indent}If {location}"]
    condition = statement.condition
    condition_indent = "  " * (depth + 1)
    operand_indent = "  " * (depth + 2)
    lines.extend([
        f"{condition_indent}Compare {condition.operator} "
        f"@{condition.line}:{condition.column}",
        f"{operand_indent}Capacity "
        f"@{condition.left.line}:{condition.left.column}",
        f"{operand_indent}Number {condition.right.value} "
        f"@{condition.right.line}:{condition.right.column}",
        f"{condition_indent}Then",
    ])
    lines.extend(_format_statement(statement.body, depth + 2))
    return lines
