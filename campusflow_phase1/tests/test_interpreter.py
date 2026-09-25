import unittest

from campusflow.interpreter import Interpreter, format_runtime
from campusflow.ir import IRGenerator
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def execute(source):
    parsed = Parser(Lexer(source).scan().tokens).parse()
    assert not parsed.errors
    return Interpreter().execute(IRGenerator().generate(parsed.program))


class InterpreterTests(unittest.TestCase):
    def test_executes_event_reservation_assignment_and_cancel(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Hall FOR Demo CAPACITY 50;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertTrue(result.state.events["Demo"].cancelled)
        self.assertEqual(result.state.reservations, [])
        self.assertEqual(result.state.assignments, [])
        self.assertEqual(result.state.last_capacity, 50)

    def test_true_condition_executes_body(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 150;",
            "IF capacity >= 100 THEN ASSIGN Projector TO Demo;",
        ]))
        self.assertEqual(
            [item.item for item in result.state.assignments],
            ["Projector"],
        )

    def test_false_condition_skips_body_without_mutating_state(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 50;",
            "IF capacity >= 100 THEN RESERVE Hall FOR Demo CAPACITY 120;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual(
            [item.resource for item in result.state.reservations],
            ["Seed"],
        )
        self.assertEqual(result.state.last_capacity, 50)

    def test_cancel_releases_resource_for_later_overlapping_event(self):
        result = execute("\n".join([
            "EVENT First ON 2026-10-15 AT 10:00 TO 12:00;",
            "EVENT Second ON 2026-10-15 AT 11:00 TO 13:00;",
            "RESERVE Hall FOR First CAPACITY 100;",
            "CANCEL First;",
            "RESERVE Hall FOR Second CAPACITY 80;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual(result.state.reservations[0].event, "Second")

    def test_unknown_opcode_is_runtime_error(self):
        from campusflow.ir import IRProgram, Instruction

        result = Interpreter().execute(IRProgram((
            Instruction("BROKEN", (), 4, 2),
        )))
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Unknown opcode 'BROKEN'", result.errors[0].message)
        self.assertEqual(
            (result.errors[0].line, result.errors[0].column),
            (4, 2),
        )

    def test_condition_without_capacity_is_runtime_error(self):
        from campusflow.ir import IRProgram, Instruction

        instructions = (
            Instruction("JUMP_IF_FALSE", (">=", 10, "end"), 1, 1),
            Instruction("LABEL", ("end",), 1, 1),
        )
        result = Interpreter().execute(IRProgram(instructions))
        self.assertIn("capacity is not available", result.errors[0].message)


if __name__ == "__main__":
    unittest.main()
