"""Correctness-aware performance measurements for CampusFlow IR."""

from dataclasses import dataclass
from statistics import median
from time import perf_counter_ns
import tracemalloc

from .interpreter import Interpreter
from .ir import IRProgram


@dataclass(frozen=True)
class BenchmarkResult:
    iterations: int
    original_instruction_count: int
    optimized_instruction_count: int
    original_median_ns: int
    optimized_median_ns: int
    original_peak_bytes: int
    optimized_peak_bytes: int
    equivalent: bool


def benchmark_ir(
    original: IRProgram,
    optimized: IRProgram,
    *,
    iterations: int,
) -> BenchmarkResult:
    """Measure both programs independently and verify equivalent results."""
    if iterations <= 0:
        raise ValueError("Benchmark iterations must be greater than zero")

    # The warm-up also provides the complete results used for the semantic
    # equivalence check. Each later measurement uses a fresh interpreter.
    original_result = Interpreter().execute(original)
    optimized_result = Interpreter().execute(optimized)

    original_times: list[int] = []
    optimized_times: list[int] = []
    for _ in range(iterations):
        original_times.append(_time_execution(original))
        optimized_times.append(_time_execution(optimized))

    return BenchmarkResult(
        iterations=iterations,
        original_instruction_count=len(original.instructions),
        optimized_instruction_count=len(optimized.instructions),
        original_median_ns=int(median(original_times)),
        optimized_median_ns=int(median(optimized_times)),
        original_peak_bytes=_peak_execution_bytes(original),
        optimized_peak_bytes=_peak_execution_bytes(optimized),
        equivalent=original_result == optimized_result,
    )


def _time_execution(program: IRProgram) -> int:
    started = perf_counter_ns()
    Interpreter().execute(program)
    elapsed = perf_counter_ns() - started
    # A mocked timer or coarse platform clock can appear to move backwards.
    # Clamping avoids turning measurement noise into a false performance claim.
    return max(0, elapsed)


def _peak_execution_bytes(program: IRProgram) -> int:
    tracemalloc.start()
    try:
        Interpreter().execute(program)
        _current, peak = tracemalloc.get_traced_memory()
        return peak
    finally:
        tracemalloc.stop()


def format_benchmark(result: BenchmarkResult) -> str:
    """Return a deterministic benchmark report without speedup promises."""
    original_count = result.original_instruction_count
    removed = original_count - result.optimized_instruction_count
    reduction = 0.0 if original_count == 0 else removed * 100.0 / original_count
    if result.optimized_median_ns == 0:
        ratio = "n/a"
    else:
        ratio = f"{result.original_median_ns / result.optimized_median_ns:.3f}x"
    status = "PASS" if result.equivalent else "FAIL"
    return "\n".join((
        f"Benchmark iterations: {result.iterations}",
        f"Original instruction count: {original_count}",
        f"Optimized instruction count: {result.optimized_instruction_count}",
        f"Instruction reduction: {reduction:.2f}%",
        f"Original median execution time (ns): {result.original_median_ns}",
        f"Optimized median execution time (ns): {result.optimized_median_ns}",
        f"Measured time ratio (original/optimized): {ratio}",
        f"Original peak memory (bytes): {result.original_peak_bytes}",
        f"Optimized peak memory (bytes): {result.optimized_peak_bytes}",
        f"Execution equivalence: {status}",
    ))
