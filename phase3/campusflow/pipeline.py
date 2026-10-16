"""Coordinator for the CampusFlow compiler stages."""

from dataclasses import dataclass

from .interpreter import ExecutionResult, Interpreter
from .ir import IRGenerator, IRProgram
from .lexer import Lexer
from .model import ScanResult
from .optimizer import IROptimizer, OptimizationResult, OptimizerDiagnostic
from .parser import ParseResult, Parser
from .semantic import SemanticAnalyzer, SemanticResult


STAGES = {"tokens", "ast", "ir", "optimized", "run", "all"}


@dataclass(frozen=True)
class PipelineResult:
    scan: ScanResult
    parse: ParseResult | None = None
    semantic: SemanticResult | None = None
    ir: IRProgram | None = None
    optimization: OptimizationResult | None = None
    optimized_ir: IRProgram | None = None
    optimizer_errors: tuple[OptimizerDiagnostic, ...] = ()
    execution: ExecutionResult | None = None


def compile_source(source: str, *, stage: str = "all") -> PipelineResult:
    """Run the requested compiler stages, stopping after any diagnostic."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage '{stage}'")

    scan = Lexer(source).scan()
    if scan.errors or stage == "tokens":
        return PipelineResult(scan=scan)

    parsed = Parser(scan.tokens).parse()
    if parsed.errors or stage == "ast":
        return PipelineResult(scan=scan, parse=parsed)

    semantic = SemanticAnalyzer().analyze(parsed.program)
    if semantic.errors:
        return PipelineResult(scan=scan, parse=parsed, semantic=semantic)

    intermediate = IRGenerator().generate(parsed.program)
    if stage == "ir":
        return PipelineResult(
            scan=scan,
            parse=parsed,
            semantic=semantic,
            ir=intermediate,
        )

    optimization = IROptimizer().optimize(intermediate)
    if optimization.errors:
        return PipelineResult(
            scan=scan,
            parse=parsed,
            semantic=semantic,
            ir=intermediate,
            optimization=optimization,
            optimizer_errors=optimization.errors,
        )

    optimized = optimization.optimized
    if stage == "optimized":
        return PipelineResult(
            scan=scan,
            parse=parsed,
            semantic=semantic,
            ir=intermediate,
            optimization=optimization,
            optimized_ir=optimized,
        )

    execution = Interpreter().execute(optimized)
    return PipelineResult(
        scan=scan,
        parse=parsed,
        semantic=semantic,
        ir=intermediate,
        optimization=optimization,
        optimized_ir=optimized,
        execution=execution,
    )
