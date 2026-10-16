# CampusFlow Phase 3 Completion and Rubric Map

The Phase 3 software is complete and integrated. The map below distinguishes
verified software/evidence from final report and packaging artifacts that are
generated after this evidence baseline.

## Phase 3 Activities

| Required activity | Completed implementation and evidence |
|---|---|
| Complete remaining functionality | IR optimizer in `campusflow/optimizer.py`; benchmark support in `campusflow/metrics.py` and `cli.py` |
| Integrate all modules | `campusflow/pipeline.py` runs lexer → parser → semantic analysis → IR → optimizer → interpreter |
| Test valid inputs | `valid.cflow`, `optimization_demo.cflow`, and positive unit/integration tests |
| Test invalid inputs | `invalid.cflow`, `syntax_errors.cflow`, `semantic_errors.cflow`, `resource_conflict.cflow` |
| Test boundary cases | `boundary_cases.cflow`, lexer limits, capacity 1, equal/adjacent times, CLI iteration validation |
| Test error conditions | Positioned lexical/syntax/semantic/optimizer/runtime diagnostics and pipeline gating tests |
| Test complex inputs | Six-event `complex_schedule.cflow` with four optimized conditions, cancellation, and resource reuse |
| Meaningful errors | Diagnostics include stage, message, line, and column; CLI exits nonzero |
| Evaluate performance | `--benchmark N` records instruction reduction, median time, peak memory, and equivalence |
| Complete documentation | `README.md`, this rubric map, evidence files, final report, presentation, and user instructions |

## Phase 3 Deliverables

| Deliverable | Status and location |
|---|---|
| Complete working project | Verified — entire `phase3/` directory; entry point `run.py` |
| Complete source code | Verified — `phase3/campusflow/` |
| Test cases | Verified — `phase3/tests/` and `phase3/examples/` |
| Test results | Captured — `phase3/evidence/test_results.txt` |
| Output evidence | Captured — four files in `phase3/evidence/` |
| Final project report | Artifact-build target — `phase3/deliverables/CampusFlow_Phase3_Final_Report.docx` |
| Presentation | Artifact-build target — `phase3/deliverables/CampusFlow_Phase3_Presentation.pptx` |
| User instructions | Verified — `phase3/README.md` |
| Submission archive | Packaging target — `phase3/deliverables/CampusFlow_Phase3_Submission.zip` |

## Compiler Concepts Implemented

| Concept | Module | Main verification |
|---|---|---|
| Lexical analysis | `lexer.py`, `model.py` | `test_lexer.py`, token stage |
| Syntax analysis | `parser.py` | `test_parser.py`, AST stage |
| Abstract syntax tree | `ast_nodes.py` | `test_ast_nodes.py` |
| Semantic analysis | `semantic.py` | `test_semantic.py` |
| Symbol table | `symbols.py` | `test_symbols.py` |
| Intermediate code | `ir.py` | `test_ir.py`, IR stage |
| Code optimization | `optimizer.py` | `test_optimizer.py`, optimized stage |
| Interpreter/runtime | `interpreter.py` | `test_interpreter.py`, run stage |
| Error handling | All stages | pipeline, CLI, and invalid-example tests |
| Performance evaluation | `metrics.py` | `test_metrics.py`, benchmark evidence |

## Review 3 Criteria

| Review criterion | Evidence |
|---|---|
| Project Completion | All compiler stages, optimizer, execution, metrics, documentation, and packaging are delivered |
| Functional Correctness | Full automated suite plus execution-equivalence `PASS` in benchmark evidence |
| Technical Complexity | Recursive-descent parsing, scoped validation, IR lowering, forward data-flow optimization, interpreter, metrics |
| Compiler Integration | `compile_source` safely connects every compiler stage and executes optimized IR |
| Innovation | Campus scheduling DSL, conservative capacity folding, and correctness-aware benchmarking |
| Code Quality | Typed dataclasses, separated modules, deterministic formatters, standard-library-only implementation |
| Testing | Unit, integration, subprocess, regression, boundary, invalid, complex, and timing-noise tests |
| Demonstration | Three Phase 3 demo inputs and reproducible commands in `README.md` |
| Documentation | User guide, module explanation, evidence, report, presentation, and this rubric map |
| Viva | Architecture, algorithm, commands, limitations, and outputs are explicitly explained in the report and presentation |

## Reproduce the Evidence

From `phase3/`:

```bash
python3 -m unittest discover -s tests -v
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/complex_schedule.cflow --stage all
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

The captured versions of these outputs are stored in `evidence/` without
machine-specific absolute input paths.
