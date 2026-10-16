"""Immutable result records produced by the CampusFlow lexer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """A classified lexeme and its one-based source position."""

    kind: str
    lexeme: str
    line: int
    column: int


@dataclass(frozen=True)
class LexicalError:
    """A recoverable lexical error and its one-based source position."""

    message: str
    line: int
    column: int


@dataclass(frozen=True)
class ScanResult:
    """The complete token stream and all lexical errors."""

    tokens: tuple[Token, ...]
    errors: tuple[LexicalError, ...]
