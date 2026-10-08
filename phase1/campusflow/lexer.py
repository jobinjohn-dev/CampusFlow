"""Left-to-right lexical analyzer for the CampusFlow language."""

from datetime import datetime
import re

from .model import LexicalError, ScanResult, Token


KEYWORDS = {
    "EVENT",
    "ON",
    "AT",
    "TO",
    "RESERVE",
    "FOR",
    "CAPACITY",
    "ASSIGN",
    "IF",
    "THEN",
    "CANCEL",
}

TWO_CHARACTER_OPERATORS = {">=", "<=", "==", "!="}
ONE_CHARACTER_OPERATORS = {">", "<"}
INVALID_OPERATOR_PAIRS = {"=>", "=<"}
DELIMITERS = {
    ";": "SEMICOLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
}

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
TIME_PATTERN = re.compile(r"\d{2}:\d{2}")
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
NUMBER_PATTERN = re.compile(r"\d+")


class Lexer:
    """Convert CampusFlow source text into tokens while collecting errors."""

    def __init__(self, source: str):
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []

    def scan(self) -> ScanResult:
        """Scan all source characters and append an EOF token."""
        while not self._at_end():
            character = self._current()

            if character in " \t\r":
                self._advance()
            elif character == "\n":
                self._advance_newline()
            elif character == "#":
                self._skip_comment()
            elif character == '"':
                self._scan_string()
            elif character.isdigit():
                self._scan_numeric_literal()
            elif character.isalpha() or character == "_":
                self._scan_word()
            elif self._scan_operator_or_delimiter():
                continue
            else:
                start_line, start_column = self.line, self.column
                illegal = self._advance()
                self._error(f"Illegal character '{illegal}'", start_line, start_column)

        self.tokens.append(Token("EOF", "", self.line, self.column))
        return ScanResult(tuple(self.tokens), tuple(self.errors))

    def _scan_word(self) -> None:
        start_index, start_line, start_column = self.index, self.line, self.column
        match = IDENTIFIER_PATTERN.match(self.source, self.index)
        if match is None:
            return
        self._advance_count(len(match.group(0)))
        lexeme = self.source[start_index:self.index]
        kind = "KEYWORD" if lexeme.upper() in KEYWORDS else "IDENTIFIER"
        self.tokens.append(Token(kind, lexeme, start_line, start_column))

    def _scan_numeric_literal(self) -> None:
        start_index, start_line, start_column = self.index, self.line, self.column

        date_match = DATE_PATTERN.match(self.source, self.index)
        if date_match is not None:
            lexeme = date_match.group(0)
            self._advance_count(len(lexeme))
            try:
                datetime.strptime(lexeme, "%Y-%m-%d")
                kind = "DATE"
            except ValueError:
                kind = "INVALID_DATE"
                self._error(
                    f"Invalid calendar date '{lexeme}'", start_line, start_column
                )
            self.tokens.append(Token(kind, lexeme, start_line, start_column))
            return

        time_match = TIME_PATTERN.match(self.source, self.index)
        if time_match is not None:
            lexeme = time_match.group(0)
            self._advance_count(len(lexeme))
            hour, minute = (int(part) for part in lexeme.split(":"))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                kind = "TIME"
            else:
                kind = "INVALID_TIME"
                self._error(f"Invalid time '{lexeme}'", start_line, start_column)
            self.tokens.append(Token(kind, lexeme, start_line, start_column))
            return

        number_match = NUMBER_PATTERN.match(self.source, self.index)
        if number_match is None:
            return
        self._advance_count(len(number_match.group(0)))
        lexeme = self.source[start_index:self.index]
        self.tokens.append(Token("NUMBER", lexeme, start_line, start_column))

    def _scan_string(self) -> None:
        start_index, start_line, start_column = self.index, self.line, self.column
        self._advance()
        while not self._at_end() and self._current() not in {'"', "\n"}:
            self._advance()

        if self._at_end() or self._current() == "\n":
            lexeme = self.source[start_index:self.index]
            self.tokens.append(
                Token("INVALID_STRING", lexeme, start_line, start_column)
            )
            self._error("Unterminated string literal", start_line, start_column)
            return

        self._advance()
        lexeme = self.source[start_index:self.index]
        self.tokens.append(Token("STRING", lexeme, start_line, start_column))

    def _scan_operator_or_delimiter(self) -> bool:
        start_line, start_column = self.line, self.column
        pair = self.source[self.index : self.index + 2]
        if pair in TWO_CHARACTER_OPERATORS:
            self._advance_count(2)
            self.tokens.append(Token("OPERATOR", pair, start_line, start_column))
            return True
        if pair in INVALID_OPERATOR_PAIRS:
            self._advance_count(2)
            self.tokens.append(
                Token("INVALID_OPERATOR", pair, start_line, start_column)
            )
            self._error(f"Unknown operator '{pair}'", start_line, start_column)
            return True

        character = self._current()
        if character in ONE_CHARACTER_OPERATORS:
            self._advance()
            self.tokens.append(
                Token("OPERATOR", character, start_line, start_column)
            )
            return True
        if character in DELIMITERS:
            self._advance()
            self.tokens.append(
                Token(DELIMITERS[character], character, start_line, start_column)
            )
            return True
        return False

    def _skip_comment(self) -> None:
        while not self._at_end() and self._current() != "\n":
            self._advance()

    def _error(self, message: str, line: int, column: int) -> None:
        self.errors.append(LexicalError(message, line, column))

    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    def _current(self) -> str:
        return self.source[self.index]

    def _advance(self) -> str:
        character = self.source[self.index]
        self.index += 1
        self.column += 1
        return character

    def _advance_count(self, count: int) -> None:
        for _ in range(count):
            self._advance()

    def _advance_newline(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1
