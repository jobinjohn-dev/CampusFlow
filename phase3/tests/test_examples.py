import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run.py"
EXAMPLES = ROOT / "examples"


class ExampleTests(unittest.TestCase):
    def run_example(self, name, stage="all"):
        return subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                str(EXAMPLES / name),
                "--stage",
                stage,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_example_executes_every_statement_form(self):
        completed = self.run_example("valid.cflow")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("FINAL RUNTIME STATE", completed.stdout)
        self.assertIn("TechFest", completed.stdout)
        self.assertIn("Workshop", completed.stdout)
        self.assertIn("OldMeet", completed.stdout)
        self.assertIn("CANCELLED", completed.stdout)
        self.assertIn("Seminar_Hall", completed.stdout)

    def test_each_invalid_example_fails_at_its_intended_stage(self):
        cases = {
            "invalid.cflow": "LEXICAL ERRORS",
            "syntax_errors.cflow": "SYNTAX ERRORS",
            "semantic_errors.cflow": "SEMANTIC ERRORS",
            "resource_conflict.cflow": "SEMANTIC ERRORS",
        }
        for filename, heading in cases.items():
            with self.subTest(filename=filename):
                completed = self.run_example(filename)
                self.assertEqual(completed.returncode, 1)
                self.assertIn(heading, completed.stdout)


if __name__ == "__main__":
    unittest.main()
