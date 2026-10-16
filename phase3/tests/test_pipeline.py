import unittest
from unittest.mock import patch

from campusflow.interpreter import ExecutionResult, RuntimeState
from campusflow.pipeline import compile_source


VALID = "\n".join([
    "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
    "RESERVE Hall FOR Demo CAPACITY 50;",
])

OPTIMIZABLE = "\n".join([
    "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
    "RESERVE Hall FOR Demo CAPACITY 50;",
    "IF capacity >= 20 THEN ASSIGN Projector TO Demo;",
])


class PipelineTests(unittest.TestCase):
    def test_all_stage_returns_every_artifact(self):
        result = compile_source(VALID, stage="all")
        self.assertIsNotNone(result.parse)
        self.assertIsNotNone(result.semantic)
        self.assertIsNotNone(result.ir)
        self.assertIsNotNone(result.optimization)
        self.assertIsNotNone(result.optimized_ir)
        self.assertEqual(result.optimizer_errors, ())
        self.assertIsNotNone(result.execution)

    def test_optimized_stage_returns_original_and_optimized_ir_without_execution(self):
        result = compile_source(OPTIMIZABLE, stage="optimized")

        self.assertIsNotNone(result.ir)
        self.assertIsNotNone(result.optimization)
        self.assertEqual(result.optimized_ir, result.optimization.optimized)
        self.assertLess(
            len(result.optimized_ir.instructions), len(result.ir.instructions)
        )
        self.assertIsNone(result.execution)

    def test_all_stage_executes_optimized_ir(self):
        executed = ExecutionResult(RuntimeState(), ())
        with patch("campusflow.pipeline.Interpreter.execute", return_value=executed) as run:
            result = compile_source(OPTIMIZABLE, stage="all")

        run.assert_called_once_with(result.optimized_ir)
        self.assertIs(result.execution, executed)

    def test_tokens_stage_stops_after_lexer(self):
        result = compile_source(VALID, stage="tokens")
        self.assertIsNone(result.parse)
        self.assertIsNone(result.semantic)
        self.assertIsNone(result.ir)
        self.assertIsNone(result.optimization)
        self.assertIsNone(result.optimized_ir)
        self.assertEqual(result.optimizer_errors, ())
        self.assertIsNone(result.execution)

    def test_each_error_stage_prevents_later_artifacts(self):
        lexical = compile_source("RESERVE @Hall;", stage="all")
        syntax = compile_source("CANCEL ;", stage="all")
        semantic = compile_source("CANCEL Missing;", stage="all")
        self.assertIsNone(lexical.parse)
        self.assertIsNone(syntax.semantic)
        self.assertIsNone(semantic.ir)
        for result in (lexical, syntax, semantic):
            self.assertIsNone(result.optimization)
            self.assertIsNone(result.optimized_ir)
            self.assertEqual(result.optimizer_errors, ())
            self.assertIsNone(result.execution)

    def test_invalid_programmatic_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown stage"):
            compile_source(VALID, stage="unknown")


if __name__ == "__main__":
    unittest.main()
