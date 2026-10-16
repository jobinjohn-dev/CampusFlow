"""Safe, deterministic optimization for CampusFlow intermediate code."""

from dataclasses import dataclass
import operator

from .ir import IRProgram, Instruction


COMPARISONS = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


@dataclass(frozen=True)
class OptimizerDiagnostic:
    message: str
    line: int
    column: int


@dataclass(frozen=True)
class OptimizationStats:
    original_count: int
    optimized_count: int
    folded_true: int
    folded_false: int

    @property
    def removed_count(self) -> int:
        return self.original_count - self.optimized_count

    @property
    def reduction_percent(self) -> float:
        if self.original_count == 0:
            return 0.0
        return self.removed_count * 100.0 / self.original_count


@dataclass(frozen=True)
class OptimizationResult:
    original: IRProgram
    optimized: IRProgram
    stats: OptimizationStats
    log: tuple[str, ...]
    errors: tuple[OptimizerDiagnostic, ...]


class IROptimizer:
    """Fold conditional IR when the current capacity is statically known."""

    def optimize(self, program: IRProgram) -> OptimizationResult:
        source = program.instructions
        labels, errors = self._validate(source)
        if errors:
            stats = OptimizationStats(len(source), len(source), 0, 0)
            return OptimizationResult(program, program, stats, (), tuple(errors))

        optimized: list[Instruction] = []
        known_capacity: int | None = None
        folded_true = 0
        folded_false = 0
        log: list[str] = []
        index = 0

        while index < len(source):
            current = source[index]
            if current.opcode == "RESERVE_RESOURCE":
                optimized.append(current)
                known_capacity = current.operands[2]
                index += 1
                continue

            if current.opcode == "JUMP_IF_FALSE":
                comparison, right, label = current.operands
                label_index = labels[label]
                body = source[index + 1:label_index]

                # A preserved branch can change capacity in ways that are not
                # statically knowable. Keep the entire region and invalidate
                # the proof state rather than making an unsafe later fold.
                has_nested_flow = any(
                    item.opcode in {"JUMP_IF_FALSE", "LABEL"} for item in body
                )
                if known_capacity is None or has_nested_flow:
                    optimized.extend(source[index:label_index + 1])
                    known_capacity = None
                    index = label_index + 1
                    continue

                if COMPARISONS[comparison](known_capacity, right):
                    optimized.extend(body)
                    for body_instruction in body:
                        if body_instruction.opcode == "RESERVE_RESOURCE":
                            known_capacity = body_instruction.operands[2]
                    folded_true += 1
                    log.append(
                        f"{current.line}:{current.column} folded condition true"
                    )
                    index = label_index + 1
                    continue
                folded_false += 1
                log.append(
                    f"{current.line}:{current.column} folded condition false"
                )
                index = label_index + 1
                continue

            optimized.append(current)
            index += 1

        result_program = IRProgram(tuple(optimized))
        stats = OptimizationStats(
            len(source), len(optimized), folded_true, folded_false
        )
        return OptimizationResult(program, result_program, stats, tuple(log), ())

    @staticmethod
    def _validate(
        instructions: tuple[Instruction, ...],
    ) -> tuple[dict[str, int], list[OptimizerDiagnostic]]:
        labels: dict[str, int] = {}
        errors: list[OptimizerDiagnostic] = []

        for index, instruction in enumerate(instructions):
            if instruction.opcode != "LABEL":
                continue
            if len(instruction.operands) != 1 or not isinstance(
                instruction.operands[0], str
            ):
                errors.append(OptimizerDiagnostic(
                    "LABEL requires one string operand",
                    instruction.line,
                    instruction.column,
                ))
                continue
            label = instruction.operands[0]
            if label in labels:
                errors.append(OptimizerDiagnostic(
                    f"Duplicate label '{label}'",
                    instruction.line,
                    instruction.column,
                ))
            else:
                labels[label] = index

        for index, instruction in enumerate(instructions):
            if instruction.opcode != "JUMP_IF_FALSE":
                continue
            if len(instruction.operands) != 3:
                errors.append(OptimizerDiagnostic(
                    "JUMP_IF_FALSE requires comparison, value, and label operands",
                    instruction.line,
                    instruction.column,
                ))
                continue
            comparison, _right, label = instruction.operands
            if comparison not in COMPARISONS:
                errors.append(OptimizerDiagnostic(
                    f"Unknown comparison operator '{comparison}'",
                    instruction.line,
                    instruction.column,
                ))
            if not isinstance(label, str) or label not in labels:
                errors.append(OptimizerDiagnostic(
                    f"Unknown label '{label}'",
                    instruction.line,
                    instruction.column,
                ))
            elif labels[label] <= index:
                errors.append(OptimizerDiagnostic(
                    f"Conditional jump to '{label}' must target a later instruction",
                    instruction.line,
                    instruction.column,
                ))

        return labels, errors


def format_optimization(result: OptimizationResult) -> str:
    """Format stable optimization statistics for CLI output and reports."""
    stats = result.stats
    lines = [
        f"Original instructions: {stats.original_count}",
        f"Optimized instructions: {stats.optimized_count}",
        f"Instructions removed: {stats.removed_count}",
        f"Instruction reduction: {stats.reduction_percent:.2f}%",
        f"Conditions folded true: {stats.folded_true}",
        f"Conditions folded false: {stats.folded_false}",
    ]
    if result.errors:
        lines.append("Optimization diagnostics:")
        lines.extend(
            f"- {error.line}:{error.column} {error.message}"
            for error in result.errors
        )
    elif result.log:
        lines.append("Transformations:")
        lines.extend(f"- {entry}" for entry in result.log)
    return "\n".join(lines)
