# CampusFlow Phase 2 Implementation Progress

Phase 2 implements and demonstrates the major functional compiler components
listed in the project rubric. All modules use Python's standard library.

| Rubric component | Implementation | Test evidence | Demonstration |
|---|---|---|---|
| Lexical Analysis | `campusflow/lexer.py`, `model.py` | `tests/test_lexer.py` | `--stage tokens`, `invalid.cflow` |
| Syntax Analysis | `campusflow/parser.py` recursive-descent parser | `tests/test_parser.py` | `--stage ast`, `syntax_errors.cflow` |
| Abstract Syntax Tree | `campusflow/ast_nodes.py` records and formatter | `tests/test_ast_nodes.py` | AST section of `valid.cflow` |
| Semantic Analysis | `campusflow/semantic.py` | `tests/test_semantic.py` | `semantic_errors.cflow` |
| Symbol Table | `campusflow/symbols.py` | `tests/test_symbols.py` | Semantic success and symbol counts |
| Intermediate Code | `campusflow/ir.py` linear IR | `tests/test_ir.py` | `--stage ir` |
| Interpreter | `campusflow/interpreter.py` | `tests/test_interpreter.py` | `--stage run` |
| Error Handling | Stage diagnostics and pipeline short-circuiting | `tests/test_pipeline.py`, `test_cli.py` | Four invalid demonstration files |
| Test Cases | Unit, integration, CLI, and example tests | `tests/` | Full `unittest` command |
| Intermediate Results | Tokens, AST, semantic result, and IR | Formatter tests and CLI tests | Default `all` stage |
| Module-wise Explanation | Module Guide in `README.md` | Manual review | `README.md` |
| Functional Demonstration | `run.py` staged CLI | `tests/test_examples.py` | `examples/valid.cflow` |

## Implemented Language Features

- Event declaration with date and start/end times
- Resource reservation with capacity
- Equipment/item assignment
- Event cancellation with resource release
- Capacity comparisons with all six comparison operators
- Conditional execution through IR jumps and labels
- Duplicate, declaration, value, cancellation, and overlap validation
- Lexical, syntax, semantic, and defensive runtime diagnostics

## Intermediate Results

The default command prints each compiler artifact in order:

1. Positioned token table
2. Indented abstract syntax tree
3. Semantic-analysis status and symbol counts
4. Numbered intermediate instructions
5. Final runtime schedule and execution log

## Functional Demonstration

```bash
cd campusflow_phase1
python3 run.py examples/valid.cflow
python3 run.py examples/valid.cflow --stage tokens
python3 run.py examples/valid.cflow --stage ast
python3 run.py examples/valid.cflow --stage ir
python3 run.py examples/valid.cflow --stage run
```

## Error Demonstration

```bash
python3 run.py examples/invalid.cflow
python3 run.py examples/syntax_errors.cflow
python3 run.py examples/semantic_errors.cflow
python3 run.py examples/resource_conflict.cflow
```

Each invalid command is expected to exit with status `1` at its intended
compiler stage.

## Verification Commands

```bash
cd campusflow_phase1
python3 -m unittest discover -s tests -v
python3 -m compileall -q campusflow run.py
python3 run.py examples/valid.cflow --stage all
```
