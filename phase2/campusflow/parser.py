"""Recursive-descent parser for CampusFlow source tokens."""

from dataclasses import dataclass

from .ast_nodes import (
    AssignStatement,
    CancelStatement,
    CapacityExpression,
    ComparisonExpression,
    EventStatement,
    IfStatement,
    NumberLiteral,
    Program,
    ReserveStatement,
    Statement,
)
from .model import Token


@dataclass(frozen=True)
class SyntaxDiagnostic:
    message: str
    line: int
    column: int


@dataclass(frozen=True)
class ParseResult:
    program: Program
    errors: tuple[SyntaxDiagnostic, ...]


class _ParseFailure(Exception):
    def __init__(self, diagnostic: SyntaxDiagnostic):
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


class Parser:
    """Parse a CampusFlow token stream into an abstract syntax tree."""

    def __init__(self, tokens: tuple[Token, ...]):
        self.tokens = tokens
        self.index = 0
        self.errors: list[SyntaxDiagnostic] = []

    def parse(self) -> ParseResult:
        statements: list[Statement] = []
        while not self._at_end():
            try:
                statements.append(self._parse_statement())
            except _ParseFailure as failure:
                self.errors.append(failure.diagnostic)
                self._synchronize()
        return ParseResult(Program(tuple(statements)), tuple(self.errors))

    def _parse_statement(self) -> Statement:
        token = self._current()
        if self._is_keyword(token, "EVENT"):
            return self._parse_event()
        if self._is_keyword(token, "RESERVE"):
            return self._parse_reserve()
        if self._is_keyword(token, "ASSIGN"):
            return self._parse_assign()
        if self._is_keyword(token, "CANCEL"):
            return self._parse_cancel()
        if self._is_keyword(token, "IF"):
            return self._parse_if()
        self._fail("Expected a CampusFlow statement", token)

    def _parse_event(self) -> EventStatement:
        keyword = self._consume_keyword("EVENT", "Expected EVENT")
        name = self._consume_kind("IDENTIFIER", "Expected event name after EVENT")
        self._consume_keyword("ON", "Expected ON after event name")
        date = self._consume_kind("DATE", "Expected date after ON")
        self._consume_keyword("AT", "Expected AT after event date")
        start = self._consume_kind("TIME", "Expected start time after AT")
        self._consume_keyword("TO", "Expected TO after start time")
        end = self._consume_kind("TIME", "Expected end time after TO")
        self._consume_kind("SEMICOLON", "Expected ';' after EVENT statement")
        return EventStatement(
            name.lexeme,
            date.lexeme,
            start.lexeme,
            end.lexeme,
            keyword.line,
            keyword.column,
        )

    def _parse_reserve(self) -> ReserveStatement:
        keyword = self._consume_keyword("RESERVE", "Expected RESERVE")
        resource = self._consume_kind(
            "IDENTIFIER", "Expected resource name after RESERVE"
        )
        self._consume_keyword("FOR", "Expected FOR after resource name")
        event = self._consume_kind("IDENTIFIER", "Expected event name after FOR")
        self._consume_keyword("CAPACITY", "Expected CAPACITY after event name")
        capacity = self._consume_kind("NUMBER", "Expected number after CAPACITY")
        self._consume_kind("SEMICOLON", "Expected ';' after RESERVE statement")
        return ReserveStatement(
            resource.lexeme,
            event.lexeme,
            int(capacity.lexeme),
            keyword.line,
            keyword.column,
        )

    def _parse_assign(self) -> AssignStatement:
        keyword = self._consume_keyword("ASSIGN", "Expected ASSIGN")
        item = self._consume_kind("IDENTIFIER", "Expected item name after ASSIGN")
        self._consume_keyword("TO", "Expected TO after item name")
        event = self._consume_kind("IDENTIFIER", "Expected event name after TO")
        self._consume_kind("SEMICOLON", "Expected ';' after ASSIGN statement")
        return AssignStatement(
            item.lexeme, event.lexeme, keyword.line, keyword.column
        )

    def _parse_cancel(self) -> CancelStatement:
        keyword = self._consume_keyword("CANCEL", "Expected CANCEL")
        event = self._consume_kind(
            "IDENTIFIER", "Expected event name after CANCEL"
        )
        self._consume_kind("SEMICOLON", "Expected ';' after CANCEL statement")
        return CancelStatement(event.lexeme, keyword.line, keyword.column)

    def _parse_if(self) -> IfStatement:
        keyword = self._consume_keyword("IF", "Expected IF")
        capacity = self._consume_keyword(
            "CAPACITY", "Expected capacity after IF"
        )
        operator = self._consume_kind(
            "OPERATOR", "Expected comparison operator after capacity"
        )
        number = self._consume_kind(
            "NUMBER", "Expected number after comparison operator"
        )
        self._consume_keyword("THEN", "Expected THEN after condition")
        if self._is_keyword(self._current(), "RESERVE"):
            body = self._parse_reserve()
        elif self._is_keyword(self._current(), "ASSIGN"):
            body = self._parse_assign()
        elif self._is_keyword(self._current(), "CANCEL"):
            body = self._parse_cancel()
        else:
            self._fail(
                "Expected RESERVE, ASSIGN, or CANCEL after THEN",
                self._current(),
            )
        condition = ComparisonExpression(
            CapacityExpression(capacity.line, capacity.column),
            operator.lexeme,
            NumberLiteral(int(number.lexeme), number.line, number.column),
            capacity.line,
            capacity.column,
        )
        return IfStatement(condition, body, keyword.line, keyword.column)

    def _current(self) -> Token:
        return self.tokens[self.index]

    def _at_end(self) -> bool:
        return self._current().kind == "EOF"

    def _advance(self) -> Token:
        token = self._current()
        if not self._at_end():
            self.index += 1
        return token

    def _check_kind(self, kind: str) -> bool:
        return self._current().kind == kind

    @staticmethod
    def _is_keyword(token: Token, keyword: str) -> bool:
        return token.kind == "KEYWORD" and token.lexeme.upper() == keyword

    def _match_keyword(self, keyword: str) -> bool:
        if self._is_keyword(self._current(), keyword):
            self._advance()
            return True
        return False

    def _consume_kind(self, kind: str, message: str) -> Token:
        if self._check_kind(kind):
            return self._advance()
        self._fail(message, self._current())

    def _consume_keyword(self, keyword: str, message: str) -> Token:
        token = self._current()
        if self._match_keyword(keyword):
            return token
        self._fail(message, token)

    @staticmethod
    def _fail(message: str, token: Token) -> None:
        raise _ParseFailure(
            SyntaxDiagnostic(message, token.line, token.column)
        )

    def _synchronize(self) -> None:
        while not self._at_end():
            if self._advance().kind == "SEMICOLON":
                return
