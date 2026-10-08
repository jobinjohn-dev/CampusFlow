import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT_ROOT / "run.py"


class CliTests(unittest.TestCase):
    def run_source(self, source):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "input.cflow"
            source_path.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(RUNNER), str(source_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_valid_input_prints_tokens_and_returns_zero(self):
        completed = self.run_source("CANCEL OldMeet;")

        self.assertEqual(completed.returncode, 0)
        self.assertIn("KEYWORD", completed.stdout)
        self.assertIn("CANCEL", completed.stdout)
        self.assertIn("No lexical errors.", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_invalid_input_prints_error_and_returns_one(self):
        completed = self.run_source("RESERVE @Hall;")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("LEXICAL ERRORS", completed.stdout)
        self.assertIn("Illegal character '@'", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
