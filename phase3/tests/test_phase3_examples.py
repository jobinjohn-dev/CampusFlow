import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run.py"
EXAMPLES = ROOT / "examples"


class Phase3ExampleTests(unittest.TestCase):
    def run_example(self, name, *arguments):
        return subprocess.run(
            [sys.executable, str(RUNNER), str(EXAMPLES / name), *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_optimization_demo_folds_true_and_false_conditions(self):
        completed = self.run_example(
            "optimization_demo.cflow", "--stage", "optimized"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Conditions folded true: 1", completed.stdout)
        self.assertIn("Conditions folded false: 1", completed.stdout)
        self.assertIn("ASSIGN_ITEM 'Projector', 'Demo'", completed.stdout)

    def test_boundary_demo_accepts_minimum_capacity_and_adjacent_events(self):
        completed = self.run_example("boundary_cases.cflow")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Conditions folded true: 1", completed.stdout)
        self.assertIn("Conditions folded false: 1", completed.stdout)
        self.assertIn("Reserved SharedRoom for First with capacity 1", completed.stdout)
        self.assertIn("Reserved SharedRoom for Second with capacity 1", completed.stdout)

    def test_complex_demo_exercises_complete_runtime_workflow(self):
        completed = self.run_example("complex_schedule.cflow")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        for expected in (
            "Opening [CANCELLED]",
            "Workshop [ACTIVE]",
            "Closing [ACTIVE]",
            "Reserved MainHall for Workshop with capacity 100",
            "Assigned Projector to Workshop",
            "Conditions folded true:",
            "Conditions folded false:",
        ):
            self.assertIn(expected, completed.stdout)

    def test_complex_demo_benchmark_confirms_equivalence(self):
        completed = self.run_example(
            "complex_schedule.cflow", "--benchmark", "2"
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PERFORMANCE MEASUREMENT", completed.stdout)
        self.assertIn("Execution equivalence: PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
