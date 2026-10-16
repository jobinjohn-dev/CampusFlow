# CampusFlow Phase 3 Final Implementation Design

**Date:** 2026-10-16
**Status:** Approved in-chat design; written specification awaiting review

## 1. Purpose

Phase 3 turns the working CampusFlow Phase 2 compiler into a final,
independently demonstrable project. It preserves every Phase 2 capability,
adds a real compiler optimization stage, measures optimization and runtime
performance, broadens validation, and supplies the evidence and instructions
required by the final-project rubric.

The existing `phase1/` and `phase2/` directories remain unchanged. Phase 3 is
implemented in a new top-level `phase3/` directory so every assessed phase can
be run and reviewed independently.

## 2. Success Criteria

Phase 3 is successful when:

1. `phase3/` runs as a complete source-to-execution compiler using only
   Python 3.10+ and the standard library.
2. Valid Phase 2 programs retain identical observable runtime behaviour.
3. The new optimizer safely reduces conditional-control-flow instructions
   whenever their result is statically provable.
4. Users can display original IR, optimized IR, optimization statistics, and
   final runtime output from the command line.
5. Performance measurement reports instruction reduction, elapsed execution
   time, and peak traced memory without claiming guaranteed speedup.
6. Automated tests cover valid, invalid, boundary, complex, malformed-IR,
   optimization-equivalence, CLI, and performance-reporting behaviour.
7. User instructions and final-project evidence clearly map the implementation
   to the Phase 3 rubric.

## 3. Repository Layout

```text
CampusFlow/
├── phase1/                 # preserved lexical-analysis submission
├── phase2/                 # preserved core compiler implementation
├── phase3/                 # final implementation and testing
│   ├── campusflow/
│   ├── examples/
│   ├── tests/
│   ├── README.md
│   ├── PHASE3_PROGRESS.md
│   └── run.py
├── deliverables/
│   ├── phase2/
│   └── phase3/             # populated when final artifacts are generated
└── docs/
```

`phase3/` starts from the verified Phase 2 tree. Phase 3 changes are made only
inside `phase3/`, the root navigation documentation, and Phase 3 deliverable
or design documentation.

## 4. Compiler Architecture

The Phase 3 pipeline is:

```text
Source
  -> Lexer
  -> Tokens
  -> Recursive-descent parser
  -> Abstract syntax tree
  -> Semantic analysis and symbol table
  -> Original intermediate representation
  -> IR optimizer
  -> Optimized intermediate representation
  -> Interpreter
  -> Final runtime state
```

Each stage is gated. Lexical errors prevent parsing; syntax errors prevent
semantic analysis; semantic errors prevent IR generation; malformed optimizer
input prevents execution; runtime errors produce positioned diagnostics.

## 5. New Phase 3 Components

### 5.1 IR Optimizer

`campusflow/optimizer.py` defines:

- `OptimizerDiagnostic`: a positioned, controlled optimization error.
- `OptimizationStats`: instruction counts and transformation counts.
- `OptimizationResult`: original IR, optimized IR, statistics, and a stable
  textual transformation log.
- `IROptimizer`: a deterministic optimization pass over `IRProgram`.

The primary algorithm is forward constant propagation for the built-in
`capacity` value followed by conditional folding.

The optimizer scans instructions from left to right and tracks the most recent
statically known capacity:

1. `RESERVE_RESOURCE(resource, event, capacity)` makes `capacity` known.
2. `JUMP_IF_FALSE(operator, right, label)` is foldable only when the current
   capacity is known, the operator is supported, and the target is a valid
   later label.
3. If the comparison is always true, the jump and matching label are removed
   and the conditional body remains.
4. If the comparison is always false, the jump, conditional body, and matching
   label are removed.
5. If proof is impossible or the control-flow shape is not recognized, the
   original instructions are retained unchanged.

CampusFlow permits one non-nested statement in an `IF` body. Nevertheless,
the optimizer validates label structure instead of assuming it. It never
reorders events, reservations, assignments, or cancellations and never removes
an instruction with an unproven side effect.

Optimization statistics include:

- original instruction count;
- optimized instruction count;
- instructions removed;
- conditions folded true;
- conditions folded false; and
- percentage instruction reduction.

### 5.2 Optimizer Validation

Before optimization, label references are checked for missing, duplicate, or
backward targets. Unexpected shapes are preserved rather than aggressively
rewritten. Direct API use with malformed IR returns an optimizer diagnostic
instead of hanging or raising an uncontrolled exception.

For every optimized source-program test, the interpreter executes both the
original and optimized IR. Their event state, reservations, assignments,
cancellation state, last capacity, execution log, and diagnostics must match.

### 5.3 Performance Measurement

`campusflow/metrics.py` provides a repeatable benchmark runner using
`time.perf_counter_ns` and `tracemalloc` from the standard library.

After a warm-up run, it executes original and optimized IR for a configurable
number of iterations. The report contains:

- iteration count;
- original and optimized instruction counts;
- instruction reduction percentage;
- median original and optimized execution time;
- measured time ratio;
- original and optimized peak traced memory; and
- correctness-equivalence status.

Timing results are observations, not guaranteed improvements. Tests assert
structure, non-negative measurements, and equivalence rather than exact time
or a mandatory speedup.

## 6. Pipeline and Data Model Changes

`PipelineResult` gains:

- `optimized_ir: IRProgram | None`;
- `optimization: OptimizationResult | None`; and
- `optimizer_errors: tuple[OptimizerDiagnostic, ...]`.

The stage set becomes:

```text
tokens, ast, ir, optimized, run, all
```

- `ir` stops after original IR generation.
- `optimized` displays original IR, optimized IR, and optimization statistics.
- `run` executes optimized IR and displays final runtime output.
- `all` displays all compiler artifacts and executes optimized IR.

The original IR remains available for comparison and benchmarking.

## 7. Command-Line Interface

The standard demonstration remains:

```bash
python3 run.py examples/valid.cflow
```

New commands include:

```bash
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

`--benchmark N` requires a positive integer and runs only after successful
compilation. Benchmark output is appended to the requested successful stage.
Invalid arguments remain command-line errors; compiler and runtime diagnostics
retain their positioned messages and non-zero exit status.

## 8. Examples and Demonstration Evidence

Phase 3 includes:

- `valid.cflow`: complete successful pipeline;
- `optimization_demo.cflow`: both true and false conditional folding;
- `boundary_cases.cflow`: capacity one, equality comparisons, adjacent event
  intervals, and boundary-safe resource reuse;
- `complex_schedule.cflow`: multiple events, resources, assignments,
  conditions, cancellations, and reuse after cancellation;
- lexical, syntax, semantic, conflict, and runtime/IR error demonstrations.

Stable text outputs from these programs provide reproducible evidence for the
final report. Timing values are recorded separately because they vary by
machine and run.

## 9. Testing Strategy

All copied Phase 2 tests remain regression tests. New tests cover:

### Unit tests

- known-capacity propagation;
- true-condition folding;
- false-condition elimination;
- capacity updates from a retained conditional body;
- preservation when a condition cannot be proven;
- missing, duplicate, and backward-label diagnostics;
- deterministic optimization statistics and formatting;
- benchmark validation and report formatting.

### Integration tests

- complete pipeline includes optimized IR;
- every CLI stage displays only the requested artifacts;
- optimized and original runtime results are equivalent;
- invalid earlier stages block optimization and benchmarking;
- complex and boundary examples complete successfully;
- malformed IR produces controlled diagnostics;
- benchmark mode validates iterations and produces all required metrics.

### Final verification

```bash
cd phase3
python3 -m unittest discover -s tests -v
python3 -m compileall -q campusflow run.py
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

## 10. Documentation and Final Deliverables

Phase 3 will provide:

- complete working source in `phase3/`;
- comprehensive automated tests and captured test results;
- demonstration inputs and stable output evidence;
- `README.md` with installation-free user instructions;
- `PHASE3_PROGRESS.md` mapping modules and tests to the rubric;
- performance and optimization evidence;
- a final Word project report;
- a presentation; and
- a runnable Phase 3 submission ZIP.

The Word report and presentation are generated only after the implementation
and tests are final, so screenshots and measurements reflect the delivered
code rather than an intermediate build.

## 11. Compatibility and Constraints

- Python 3.10 or newer.
- Standard library only.
- Phase 1 and Phase 2 remain independently runnable and unchanged.
- Existing valid Phase 2 source files remain valid in Phase 3.
- Existing Phase 2 diagnostics and command defaults remain compatible unless
  a new optimizer-specific diagnostic is required.
- Output ordering is deterministic except for measured timing and memory
  values.

## 12. Non-Goals

Phase 3 does not add user-defined variables, arithmetic expressions, loops,
functions, nested scopes, LLVM generation, native machine code, a database,
or a graphical interface. These would expand the language substantially
without being required to demonstrate final compiler integration, testing,
optimization, and performance evaluation.

## 13. Delivery Sequence

1. Copy the verified Phase 2 tree into `phase3/` and establish regression
   tests.
2. Implement optimizer data types, validation, folding, and formatting using
   test-driven development.
3. Integrate optimization into the pipeline and CLI.
4. Add benchmarking and performance formatting.
5. Add complex and boundary examples with end-to-end tests.
6. Complete user documentation, rubric mapping, evidence, final report,
   presentation, and submission ZIP.
