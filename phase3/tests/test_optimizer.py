import unittest

from campusflow.ir import IRProgram, Instruction
from campusflow.optimizer import IROptimizer, format_optimization


def instruction(opcode, operands=(), line=1, column=1):
    return Instruction(opcode, operands, line, column)


class OptimizerTests(unittest.TestCase):
    def test_folds_provably_true_condition_and_keeps_body(self):
        program = IRProgram((
            instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100)),
            instruction("JUMP_IF_FALSE", (">=", 50, "if_end_1"), 2, 4),
            instruction("ASSIGN_ITEM", ("Projector", "Demo"), 2, 25),
            instruction("LABEL", ("if_end_1",), 2, 1),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(
            [item.opcode for item in result.optimized.instructions],
            ["RESERVE_RESOURCE", "ASSIGN_ITEM"],
        )
        self.assertEqual(result.stats.original_count, 4)
        self.assertEqual(result.stats.optimized_count, 2)
        self.assertEqual(result.stats.folded_true, 1)
        self.assertEqual(result.stats.folded_false, 0)
        self.assertEqual(result.stats.removed_count, 2)
        self.assertEqual(result.stats.reduction_percent, 50.0)
        self.assertEqual(result.errors, ())

    def test_eliminates_provably_false_condition_and_body(self):
        program = IRProgram((
            instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100)),
            instruction("JUMP_IF_FALSE", (">", 200, "if_end_1"), 2, 4),
            instruction("ASSIGN_ITEM", ("Projector", "Demo"), 2, 24),
            instruction("LABEL", ("if_end_1",), 2, 1),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(
            [item.opcode for item in result.optimized.instructions],
            ["RESERVE_RESOURCE"],
        )
        self.assertEqual(result.stats.folded_true, 0)
        self.assertEqual(result.stats.folded_false, 1)
        self.assertEqual(result.stats.removed_count, 3)

    def test_true_reservation_body_updates_capacity_for_following_fold(self):
        program = IRProgram((
            instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100)),
            instruction("JUMP_IF_FALSE", (">=", 100, "if_end_1"), 2, 4),
            instruction("RESERVE_RESOURCE", ("Lab", "Demo", 20), 2, 26),
            instruction("LABEL", ("if_end_1",), 2, 1),
            instruction("JUMP_IF_FALSE", (">=", 50, "if_end_2"), 3, 4),
            instruction("ASSIGN_ITEM", ("Speaker", "Demo"), 3, 24),
            instruction("LABEL", ("if_end_2",), 3, 1),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(
            [item.opcode for item in result.optimized.instructions],
            ["RESERVE_RESOURCE", "RESERVE_RESOURCE"],
        )
        self.assertEqual(result.stats.folded_true, 1)
        self.assertEqual(result.stats.folded_false, 1)

    def test_missing_label_returns_positioned_diagnostic(self):
        program = IRProgram((
            instruction("JUMP_IF_FALSE", (">=", 1, "missing"), 4, 7),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(result.optimized, program)
        self.assertEqual(result.errors[0].message, "Unknown label 'missing'")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (4, 7))

    def test_duplicate_label_returns_diagnostic(self):
        program = IRProgram((
            instruction("LABEL", ("same",), 1, 1),
            instruction("LABEL", ("same",), 2, 3),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(result.optimized, program)
        self.assertEqual(result.errors[0].message, "Duplicate label 'same'")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (2, 3))

    def test_backward_target_returns_diagnostic(self):
        program = IRProgram((
            instruction("LABEL", ("earlier",), 1, 1),
            instruction("JUMP_IF_FALSE", ("==", 1, "earlier"), 3, 5),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(result.optimized, program)
        self.assertEqual(
            result.errors[0].message,
            "Conditional jump to 'earlier' must target a later instruction",
        )

    def test_unknown_operator_returns_diagnostic(self):
        program = IRProgram((
            instruction("JUMP_IF_FALSE", ("??", 1, "end"), 3, 5),
            instruction("ASSIGN_ITEM", ("Mic", "Demo")),
            instruction("LABEL", ("end",)),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(result.optimized, program)
        self.assertEqual(
            result.errors[0].message, "Unknown comparison operator '??'"
        )

    def test_unknown_capacity_preserves_condition_and_invalidates_later_proof(self):
        program = IRProgram((
            instruction("JUMP_IF_FALSE", (">=", 1, "if_end_1"), 1, 4),
            instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100), 1, 20),
            instruction("LABEL", ("if_end_1",), 1, 1),
            instruction("JUMP_IF_FALSE", (">=", 50, "if_end_2"), 2, 4),
            instruction("ASSIGN_ITEM", ("Mic", "Demo"), 2, 20),
            instruction("LABEL", ("if_end_2",), 2, 1),
        ))

        result = IROptimizer().optimize(program)

        self.assertEqual(result.optimized, program)
        self.assertEqual(result.stats.folded_true, 0)
        self.assertEqual(result.stats.folded_false, 0)
        self.assertEqual(result.errors, ())

    def test_formats_statistics_and_transformation_log_deterministically(self):
        program = IRProgram((
            instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100)),
            instruction("JUMP_IF_FALSE", (">=", 50, "end"), 2, 4),
            instruction("ASSIGN_ITEM", ("Mic", "Demo")),
            instruction("LABEL", ("end",)),
        ))

        text = format_optimization(IROptimizer().optimize(program))

        self.assertEqual(
            text,
            "\n".join((
                "Original instructions: 4",
                "Optimized instructions: 2",
                "Instructions removed: 2",
                "Instruction reduction: 50.00%",
                "Conditions folded true: 1",
                "Conditions folded false: 0",
                "Transformations:",
                "- 2:4 folded condition true",
            )),
        )


if __name__ == "__main__":
    unittest.main()
