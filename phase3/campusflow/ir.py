"""Readable intermediate representation for CampusFlow programs."""

from dataclasses import dataclass

from .ast_nodes import (
    AssignStatement,
    CancelStatement,
    EventStatement,
    IfStatement,
    Program,
    ReserveStatement,
    Statement,
)


@dataclass(frozen=True)
class Instruction:
    opcode: str
    operands: tuple[object, ...]
    line: int
    column: int


@dataclass(frozen=True)
class IRProgram:
    instructions: tuple[Instruction, ...]


class IRGenerator:
    """Lower AST statements into a small linear instruction sequence."""

    def __init__(self):
        self.label_count = 0

    def generate(self, program: Program) -> IRProgram:
        self.label_count = 0
        instructions: list[Instruction] = []
        for statement in program.statements:
            instructions.extend(self._lower(statement))
        return IRProgram(tuple(instructions))

    def _lower(self, statement: Statement) -> list[Instruction]:
        if isinstance(statement, EventStatement):
            return [Instruction(
                "CREATE_EVENT",
                (
                    statement.name,
                    statement.date,
                    statement.start_time,
                    statement.end_time,
                ),
                statement.line,
                statement.column,
            )]
        if isinstance(statement, ReserveStatement):
            return [Instruction(
                "RESERVE_RESOURCE",
                (statement.resource, statement.event, statement.capacity),
                statement.line,
                statement.column,
            )]
        if isinstance(statement, AssignStatement):
            return [Instruction(
                "ASSIGN_ITEM",
                (statement.item, statement.event),
                statement.line,
                statement.column,
            )]
        if isinstance(statement, CancelStatement):
            return [Instruction(
                "CANCEL_EVENT",
                (statement.event,),
                statement.line,
                statement.column,
            )]

        self.label_count += 1
        label = f"if_end_{self.label_count}"
        condition = statement.condition
        return [
            Instruction(
                "JUMP_IF_FALSE",
                (condition.operator, condition.right.value, label),
                condition.line,
                condition.column,
            ),
            *self._lower(statement.body),
            Instruction(
                "LABEL",
                (label,),
                statement.line,
                statement.column,
            ),
        ]


def format_ir(program: IRProgram) -> str:
    """Format instructions with stable numeric addresses."""
    lines = []
    for index, instruction in enumerate(program.instructions):
        operands = ", ".join(repr(value) for value in instruction.operands)
        operand_text = f" {operands}" if operands else ""
        lines.append(
            f"{index:04d}  {instruction.opcode}{operand_text}  "
            f"@{instruction.line}:{instruction.column}"
        )
    return "\n".join(lines)
