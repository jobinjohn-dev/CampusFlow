import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT_ROOT / "run.py"


class CliTests(unittest.TestCase):
    def run_source(self, source, *arguments):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "input.cflow"
            source_path.write_text(source, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    str(source_path),
                    *arguments,
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_default_all_prints_every_stage_and_runtime(self):
        completed = self.run_source(
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;"
        )

        self.assertEqual(completed.returncode, 0)
        for heading in (
            "TOKENS",
            "ABSTRACT SYNTAX TREE",
            "INTERMEDIATE CODE",
            "FINAL RUNTIME STATE",
        ):
            self.assertIn(heading, completed.stdout)

    def test_tokens_stage_preserves_phase_one_output(self):
        completed = self.run_source(
            "CANCEL OldMeet;", "--stage", "tokens"
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("KEYWORD", completed.stdout)
        self.assertIn("No lexical errors.", completed.stdout)
        self.assertNotIn("ABSTRACT SYNTAX TREE", completed.stdout)

    def test_ast_stage_reports_syntax_error_and_omits_later_sections(self):
        completed = self.run_source("CANCEL ;", "--stage", "ast")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("SYNTAX ERRORS", completed.stdout)
        self.assertNotIn("INTERMEDIATE CODE", completed.stdout)
        self.assertNotIn("FINAL RUNTIME STATE", completed.stdout)

    def test_run_stage_reports_semantic_error(self):
        completed = self.run_source(
            "CANCEL Missing;", "--stage", "run"
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("SEMANTIC ERRORS", completed.stdout)
        self.assertIn("Undeclared event 'Missing'", completed.stdout)

    def test_invalid_input_prints_error_and_returns_one(self):
        completed = self.run_source("RESERVE @Hall;")

        self.assertEqual(completed.returncode, 1)
        self.assertIn("LEXICAL ERRORS", completed.stdout)
        self.assertIn("Illegal character '@'", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
