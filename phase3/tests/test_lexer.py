import unittest

from campusflow.lexer import Lexer


class LexerTests(unittest.TestCase):
    def test_tokenizes_event_statement_with_positions(self):
        result = Lexer(
            "EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;"
        ).scan()

        actual = [
            (token.kind, token.lexeme, token.line, token.column)
            for token in result.tokens
        ]
        self.assertEqual(
            actual,
            [
                ("KEYWORD", "EVENT", 1, 1),
                ("IDENTIFIER", "TechFest", 1, 7),
                ("KEYWORD", "ON", 1, 16),
                ("DATE", "2026-10-15", 1, 19),
                ("KEYWORD", "AT", 1, 30),
                ("TIME", "10:00", 1, 33),
                ("KEYWORD", "TO", 1, 39),
                ("TIME", "12:00", 1, 42),
                ("SEMICOLON", ";", 1, 47),
                ("EOF", "", 1, 48),
            ],
        )
        self.assertEqual(result.errors, ())

    def test_keywords_are_case_insensitive_and_identifiers_preserve_case(self):
        result = Lexer("event MixedCase on 2026-12-01 at 09:05 to 10:00;").scan()

        self.assertEqual(result.tokens[0].kind, "KEYWORD")
        self.assertEqual(result.tokens[0].lexeme, "event")
        self.assertEqual(result.tokens[1].kind, "IDENTIFIER")
        self.assertEqual(result.tokens[1].lexeme, "MixedCase")
        self.assertEqual(result.errors, ())

    def test_recognizes_longest_comparison_operators(self):
        result = Lexer(">= <= == != > <").scan()

        self.assertEqual(
            [(token.kind, token.lexeme) for token in result.tokens[:-1]],
            [
                ("OPERATOR", ">="),
                ("OPERATOR", "<="),
                ("OPERATOR", "=="),
                ("OPERATOR", "!="),
                ("OPERATOR", ">"),
                ("OPERATOR", "<"),
            ],
        )
        self.assertEqual(result.errors, ())

    def test_skips_comments_and_tracks_next_line(self):
        result = Lexer("# first event\nCANCEL OldMeet;").scan()

        self.assertEqual(
            [(token.kind, token.lexeme, token.line, token.column) for token in result.tokens],
            [
                ("KEYWORD", "CANCEL", 2, 1),
                ("IDENTIFIER", "OldMeet", 2, 8),
                ("SEMICOLON", ";", 2, 15),
                ("EOF", "", 2, 16),
            ],
        )

    def test_reports_illegal_character_and_continues(self):
        result = Lexer("RESERVE @Hall;").scan()

        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].message, "Illegal character '@'")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (1, 9))
        self.assertIn(("IDENTIFIER", "Hall"), [(t.kind, t.lexeme) for t in result.tokens])

    def test_reports_invalid_calendar_date(self):
        result = Lexer("ON 2026-02-30;").scan()

        self.assertEqual(result.tokens[1].kind, "INVALID_DATE")
        self.assertEqual(result.errors[0].message, "Invalid calendar date '2026-02-30'")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (1, 4))

    def test_reports_invalid_time_range(self):
        result = Lexer("AT 25:61;").scan()

        self.assertEqual(result.tokens[1].kind, "INVALID_TIME")
        self.assertEqual(result.errors[0].message, "Invalid time '25:61'")

    def test_reports_unterminated_string(self):
        result = Lexer('EVENT "Guest lecture').scan()

        self.assertEqual(result.tokens[1].kind, "INVALID_STRING")
        self.assertEqual(result.errors[0].message, "Unterminated string literal")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (1, 7))

    def test_recognizes_strings_numbers_and_delimiters(self):
        result = Lexer('"Guest lecture" 150;,( )').scan()

        self.assertEqual(
            [(token.kind, token.lexeme) for token in result.tokens[:-1]],
            [
                ("STRING", '"Guest lecture"'),
                ("NUMBER", "150"),
                ("SEMICOLON", ";"),
                ("COMMA", ","),
                ("LPAREN", "("),
                ("RPAREN", ")"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
