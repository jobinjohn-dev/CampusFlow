import unittest

from campusflow.ast_nodes import (
    AssignStatement,
    CancelStatement,
    EventStatement,
    IfStatement,
    ReserveStatement,
)
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def parse(source):
    scan = Lexer(source).scan()
    assert not scan.errors
    return Parser(scan.tokens).parse()


class ParserTests(unittest.TestCase):
    def test_parses_all_statement_forms(self):
        result = parse("\n".join([
            "EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;",
            "RESERVE Auditorium_A FOR TechFest CAPACITY 150;",
            "ASSIGN Projector TO TechFest;",
            "IF capacity >= 100 THEN RESERVE Hall_A FOR TechFest CAPACITY 120;",
            "CANCEL TechFest;",
        ]))

        self.assertEqual(result.errors, ())
        self.assertEqual(
            [type(statement) for statement in result.program.statements],
            [
                EventStatement,
                ReserveStatement,
                AssignStatement,
                IfStatement,
                CancelStatement,
            ],
        )
        conditional = result.program.statements[3]
        self.assertEqual(conditional.condition.operator, ">=")
        self.assertEqual(conditional.condition.right.value, 100)

    def test_keywords_are_case_insensitive(self):
        result = parse(
            "event MixedCase on 2026-12-01 at 09:05 to 10:00;"
        )
        self.assertEqual(result.errors, ())
        self.assertEqual(result.program.statements[0].name, "MixedCase")

    def test_wrong_keyword_reports_position(self):
        result = parse(
            "EVENT TechFest FOR 2026-10-15 AT 10:00 TO 12:00;"
        )
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Expected ON", result.errors[0].message)
        self.assertEqual(
            (result.errors[0].line, result.errors[0].column),
            (1, 16),
        )

    def test_recovers_at_semicolon_and_parses_later_statement(self):
        result = parse(
            "EVENT Broken ON 2026-10-15 AT ; CANCEL Missing;"
        )
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.program.statements), 1)
        self.assertIsInstance(result.program.statements[0], CancelStatement)

    def test_missing_semicolon_at_eof_reports_once_without_hanging(self):
        result = parse("CANCEL OldMeet")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Expected ';'", result.errors[0].message)
        self.assertEqual(result.program.statements, ())

    def test_if_rejects_nested_event_declaration(self):
        result = parse(
            "IF capacity >= 100 THEN EVENT Extra ON 2026-10-15 "
            "AT 13:00 TO 14:00;"
        )
        self.assertEqual(len(result.errors), 1)
        self.assertIn(
            "Expected RESERVE, ASSIGN, or CANCEL after THEN",
            result.errors[0].message,
        )


if __name__ == "__main__":
    unittest.main()
