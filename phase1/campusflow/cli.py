"""Command-line interface for the CampusFlow Phase 1 lexer."""

import argparse
from pathlib import Path

from .lexer import Lexer


def format_result(source_name: str, source: str) -> tuple[str, int]:
    """Return formatted lexer output and its process exit code."""
    result = Lexer(source).scan()
    lines = [
        f"CampusFlow lexical analysis: {source_name}",
        "",
        f"{'LINE:COL':<10} {'TOKEN':<18} LEXEME",
        f"{'-' * 8:<10} {'-' * 16:<18} {'-' * 24}",
    ]
    for token in result.tokens:
        display_lexeme = token.lexeme if token.kind != "EOF" else "<end>"
        lines.append(
            f"{token.line}:{token.column:<8} {token.kind:<18} {display_lexeme}"
        )

    lines.append("")
    if result.errors:
        lines.append("LEXICAL ERRORS")
        lines.append("--------------")
        for error in result.errors:
            lines.append(f"{error.line}:{error.column}  {error.message}")
        lines.append(f"Total lexical errors: {len(result.errors)}")
        return "\n".join(lines), 1

    lines.append("No lexical errors.")
    lines.append(f"Total tokens: {len(result.tokens)}")
    return "\n".join(lines), 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tokenize a CampusFlow DSL source file."
    )
    parser.add_argument("source_file", type=Path, help="Path to a .cflow file")
    arguments = parser.parse_args(argv)

    try:
        source = arguments.source_file.read_text(encoding="utf-8")
    except OSError as error:
        parser.error(str(error))

    output, exit_code = format_result(str(arguments.source_file), source)
    print(output)
    return exit_code
