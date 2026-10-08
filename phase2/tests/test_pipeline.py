import unittest

from campusflow.pipeline import compile_source


VALID = "\n".join([
    "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
    "RESERVE Hall FOR Demo CAPACITY 50;",
])


class PipelineTests(unittest.TestCase):
    def test_all_stage_returns_every_artifact(self):
        result = compile_source(VALID, stage="all")
        self.assertIsNotNone(result.parse)
        self.assertIsNotNone(result.semantic)
        self.assertIsNotNone(result.ir)
        self.assertIsNotNone(result.execution)

    def test_tokens_stage_stops_after_lexer(self):
        result = compile_source(VALID, stage="tokens")
        self.assertIsNone(result.parse)
        self.assertIsNone(result.semantic)
        self.assertIsNone(result.ir)
        self.assertIsNone(result.execution)

    def test_each_error_stage_prevents_later_artifacts(self):
        lexical = compile_source("RESERVE @Hall;", stage="all")
        syntax = compile_source("CANCEL ;", stage="all")
        semantic = compile_source("CANCEL Missing;", stage="all")
        self.assertIsNone(lexical.parse)
        self.assertIsNone(syntax.semantic)
        self.assertIsNone(semantic.ir)

    def test_invalid_programmatic_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown stage"):
            compile_source(VALID, stage="unknown")


if __name__ == "__main__":
    unittest.main()
