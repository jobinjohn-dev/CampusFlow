"""Command-line interface for the CampusFlow compiler pipeline."""

import argparse
from pathlib import Path

from .ast_nodes import format_ast
from .interpreter import format_runtime
from .ir import format_ir
from .model import ScanResult
from .pipeline import STAGES, compile_source


def format_tokens(scan: ScanResult) -> str:
    """Format the Phase 1 token table and its lexical status."""
    lines = [
        "TOKENS",
        "------",
        f"{'LINE:COL':<10} {'TOKEN':<18} LEXEME",
        f"{'-' * 8:<10} {'-' * 16:<18} {'-' * 24}",
    ]
    for token in scan.tokens:
        display_lexeme = token.lexeme if token.kind != "EOF" else "<end>"
        lines.append(
            f"{token.line}:{token.column:<8} "
            f"{token.kind:<18} {display_lexeme}"
        )
    lines.append("")
    if scan.errors:
        lines.extend(_format_diagnostics("LEXICAL ERRORS", scan.errors))
        lines.append(f"Total lexical errors: {len(scan.errors)}")
    else:
        lines.append("No lexical errors.")
        lines.append(f"Total tokens: {len(scan.tokens)}")
    return "\n".join(lines)


def format_result(
    source_name: str, source: str, stage: str = "all"
) -> tuple[str, int]:
    """Compile source and return requested formatted output and exit code."""
    result = compile_source(source, stage=stage)
    sections = [f"CampusFlow compilation: {source_name}"]

    if stage in {"tokens", "all"} or result.scan.errors:
        sections.append(format_tokens(result.scan))
    if result.scan.errors:
        return "\n\n".join(sections), 1

    if result.parse is not None and result.parse.errors:
        sections.append("\n".join(_format_diagnostics(
            "SYNTAX ERRORS", result.parse.errors
        )))
        return "\n\n".join(sections), 1
    if stage in {"ast", "all"} and result.parse is not None:
        sections.append(
            "ABSTRACT SYNTAX TREE\n"
            "--------------------\n"
            f"{format_ast(result.parse.program)}"
        )

    if result.semantic is not None and result.semantic.errors:
        sections.append("\n".join(_format_diagnostics(
            "SEMANTIC ERRORS", result.semantic.errors
        )))
        return "\n\n".join(sections), 1
    if stage == "all" and result.semantic is not None:
        symbols = result.semantic.symbols
        sections.append(
            "SEMANTIC ANALYSIS\n"
            "-----------------\n"
            "Semantic analysis: passed.\n"
            f"Events: {len(symbols.events)}, "
            f"reservations: {len(symbols.reservations)}, "
            f"assignments: {len(symbols.assignments)}"
        )

    if stage in {"ir", "all"} and result.ir is not None:
        sections.append(
            "INTERMEDIATE CODE\n"
            "-----------------\n"
            f"{format_ir(result.ir)}"
        )

    if result.execution is not None and result.execution.errors:
        sections.append("\n".join(_format_diagnostics(
            "RUNTIME ERRORS", result.execution.errors
        )))
        return "\n\n".join(sections), 1
    if stage in {"run", "all"} and result.execution is not None:
        sections.append(format_runtime(result.execution.state))

    return "\n\n".join(sections), 0


def _format_diagnostics(title: str, diagnostics: tuple[object, ...]) -> list[str]:
    lines = [title, "-" * len(title)]
    for diagnostic in diagnostics:
        lines.append(
            f"{diagnostic.line}:{diagnostic.column}  {diagnostic.message}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile and execute a CampusFlow DSL source file."
    )
    parser.add_argument("source_file", type=Path, help="Path to a .cflow file")
    parser.add_argument(
        "--stage",
        choices=sorted(STAGES),
        default="all",
        help="Last compiler artifact to display (default: all)",
    )
    arguments = parser.parse_args(argv)

    try:
        source = arguments.source_file.read_text(encoding="utf-8")
    except OSError as error:
        parser.error(str(error))

    output, exit_code = format_result(
        str(arguments.source_file), source, arguments.stage
    )
    print(output)
    return exit_code
