import unittest
from unittest.mock import patch

from campusflow.ir import IRProgram, Instruction
from campusflow.metrics import benchmark_ir, format_benchmark
from campusflow.optimizer import IROptimizer


def instruction(opcode, operands=(), line=1, column=1):
    return Instruction(opcode, operands, line, column)


def optimizable_program():
    return IRProgram((
        instruction("CREATE_EVENT", ("Demo", "2026-10-15", "10:00", "11:00")),
        instruction("RESERVE_RESOURCE", ("Hall", "Demo", 100)),
        instruction("JUMP_IF_FALSE", (">=", 50, "end")),
        instruction("ASSIGN_ITEM", ("Mic", "Demo")),
        instruction("LABEL", ("end",)),
    ))


class MetricsTests(unittest.TestCase):
    def test_rejects_nonpositive_iteration_count(self):
        program = IRProgram(())
        for iterations in (0, -1):
            with self.subTest(iterations=iterations):
                with self.assertRaisesRegex(
                    ValueError, "Benchmark iterations must be greater than zero"
                ):
                    benchmark_ir(program, program, iterations=iterations)

    def test_measures_equivalent_original_and_optimized_programs(self):
        original = optimizable_program()
        optimized = IROptimizer().optimize(original).optimized

        result = benchmark_ir(original, optimized, iterations=5)

        self.assertEqual(result.iterations, 5)
        self.assertTrue(result.equivalent)
        self.assertGreaterEqual(
            result.original_instruction_count,
            result.optimized_instruction_count,
        )
        self.assertGreaterEqual(result.original_median_ns, 0)
        self.assertGreaterEqual(result.optimized_median_ns, 0)
        self.assertGreaterEqual(result.original_peak_bytes, 0)
        self.assertGreaterEqual(result.optimized_peak_bytes, 0)

    def test_detects_non_equivalent_programs(self):
        original = IRProgram((instruction(
            "CREATE_EVENT", ("Demo", "2026-10-15", "10:00", "11:00")
        ),))
        different = IRProgram(())

        result = benchmark_ir(original, different, iterations=1)

        self.assertFalse(result.equivalent)

    def test_equal_or_decreasing_timer_values_do_not_require_speedup(self):
        program = IRProgram(())
        timer_values = [10, 10, 9, 8, 7, 7, 6, 5]

        with patch("campusflow.metrics.perf_counter_ns", side_effect=timer_values):
            result = benchmark_ir(program, program, iterations=2)

        self.assertEqual(result.original_median_ns, 0)
        self.assertEqual(result.optimized_median_ns, 0)
        self.assertTrue(result.equivalent)

    def test_formats_stable_correctness_aware_report(self):
        original = optimizable_program()
        optimized = IROptimizer().optimize(original).optimized
        result = benchmark_ir(original, optimized, iterations=1)

        text = format_benchmark(result)

        for expected in (
            "Benchmark iterations: 1",
            "Original instruction count: 5",
            "Optimized instruction count: 3",
            "Instruction reduction: 40.00%",
            "Original median execution time (ns):",
            "Optimized median execution time (ns):",
            "Measured time ratio (original/optimized):",
            "Original peak memory (bytes):",
            "Optimized peak memory (bytes):",
            "Execution equivalence: PASS",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("always faster", text.lower())


if __name__ == "__main__":
    unittest.main()
