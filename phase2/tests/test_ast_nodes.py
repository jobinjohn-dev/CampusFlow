import unittest
from dataclasses import FrozenInstanceError

from campusflow.ast_nodes import (
    CapacityExpression,
    ComparisonExpression,
    EventStatement,
    IfStatement,
    NumberLiteral,
    Program,
    ReserveStatement,
    format_ast,
)


class AstNodeTests(unittest.TestCase):
    def test_formats_nested_program_deterministically(self):
        program = Program((
            EventStatement("TechFest", "2026-10-15", "10:00", "12:00", 1, 1),
            IfStatement(
                ComparisonExpression(
                    CapacityExpression(2, 4),
                    ">=",
                    NumberLiteral(100, 2, 16),
                    2,
                    4,
                ),
                ReserveStatement("Hall_A", "TechFest", 120, 2, 25),
                2,
                1,
            ),
        ))

        self.assertEqual(
            format_ast(program),
            "\n".join([
                "Program",
                "  Event TechFest date=2026-10-15 start=10:00 end=12:00 @1:1",
                "  If @2:1",
                "    Compare >= @2:4",
                "      Capacity @2:4",
                "      Number 100 @2:16",
                "    Then",
                "      Reserve Hall_A for=TechFest capacity=120 @2:25",
            ]),
        )

    def test_nodes_are_immutable(self):
        event = EventStatement(
            "TechFest", "2026-10-15", "10:00", "12:00", 1, 1
        )
        with self.assertRaises(FrozenInstanceError):
            event.name = "Changed"


if __name__ == "__main__":
    unittest.main()
