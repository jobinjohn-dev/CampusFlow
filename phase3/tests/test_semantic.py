import unittest

from campusflow.lexer import Lexer
from campusflow.parser import Parser
from campusflow.semantic import SemanticAnalyzer


def analyze(source):
    scan = Lexer(source).scan()
    assert not scan.errors
    parsed = Parser(scan.tokens).parse()
    assert not parsed.errors
    return SemanticAnalyzer().analyze(parsed.program)


class SemanticTests(unittest.TestCase):
    def test_builds_symbols_for_valid_program(self):
        result = analyze("\n".join([
            "EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;",
            "RESERVE Auditorium_A FOR TechFest CAPACITY 150;",
            "ASSIGN Projector TO TechFest;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertIn("TechFest", result.symbols.events)
        self.assertEqual(result.symbols.reservations[0].capacity, 150)

    def test_reports_duplicate_event_invalid_time_and_nonpositive_capacity(self):
        result = analyze("\n".join([
            "EVENT BadTime ON 2026-10-15 AT 12:00 TO 10:00;",
            "EVENT Dup ON 2026-10-15 AT 13:00 TO 14:00;",
            "EVENT Dup ON 2026-10-16 AT 13:00 TO 14:00;",
            "RESERVE Hall FOR Dup CAPACITY 0;",
        ]))
        messages = [error.message for error in result.errors]
        self.assertTrue(any("end time" in message for message in messages))
        self.assertTrue(any("Duplicate event 'Dup'" in message for message in messages))
        self.assertTrue(any(
            "Capacity must be greater than zero" in message
            for message in messages
        ))

    def test_reports_undeclared_cancelled_duplicate_and_capacity_use(self):
        result = analyze("\n".join([
            "ASSIGN Projector TO Missing;",
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "ASSIGN Projector TO Demo;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
            "RESERVE Hall FOR Demo CAPACITY 10;",
            "IF capacity >= 5 THEN CANCEL Demo;",
        ]))
        messages = [error.message for error in result.errors]
        self.assertTrue(any(
            "Undeclared event 'Missing'" in message for message in messages
        ))
        self.assertTrue(any("already assigned" in message for message in messages))
        self.assertTrue(any(
            "cancelled event 'Demo'" in message for message in messages
        ))
        self.assertTrue(any(
            "capacity is not available" in message for message in messages
        ))

    def test_detects_overlap_but_allows_boundary_and_reuse_after_cancel(self):
        result = analyze("\n".join([
            "EVENT First ON 2026-10-15 AT 10:00 TO 11:00;",
            "EVENT Adjacent ON 2026-10-15 AT 11:00 TO 12:00;",
            "EVENT Overlap ON 2026-10-15 AT 10:15 TO 10:45;",
            "RESERVE Hall FOR First CAPACITY 100;",
            "RESERVE Hall FOR Adjacent CAPACITY 100;",
            "RESERVE Hall FOR Overlap CAPACITY 100;",
            "CANCEL First;",
            "RESERVE Hall FOR Overlap CAPACITY 100;",
        ]))
        conflicts = [
            error for error in result.errors if "conflicts" in error.message
        ]
        self.assertEqual(len(conflicts), 1)

    def test_conditional_body_is_validated_without_committing_effects(self):
        result = analyze("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 50;",
            "IF capacity >= 100 THEN ASSIGN Projector TO Demo;",
            "ASSIGN Projector TO Demo;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual(len(result.symbols.assignments), 1)


if __name__ == "__main__":
    unittest.main()
