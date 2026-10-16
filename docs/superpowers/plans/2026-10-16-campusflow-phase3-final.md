# CampusFlow Phase 3 Final Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independently runnable Phase 3 CampusFlow compiler with safe IR optimization, optimized execution, performance measurement, comprehensive validation, and all final-submission artifacts.

**Architecture:** Copy the verified Phase 2 tree into `phase3/`, then insert a deterministic optimizer between IR generation and interpretation. Preserve original IR for comparison, execute optimized IR, add an isolated benchmark module, and generate final evidence only after the implementation passes regression and equivalence tests.

**Tech Stack:** Python 3.10+ standard library, `unittest`, `dataclasses`, `operator`, `time.perf_counter_ns`, `tracemalloc`, Word `.docx`, PowerPoint `.pptx`, ZIP.

**Spec:** `docs/superpowers/specs/2026-10-16-campusflow-phase3-final-design.md`

## Global Constraints

- Python 3.10 or newer.
- The runnable compiler uses only the Python standard library.
- `phase1/` and `phase2/` remain independently runnable and unchanged.
- Existing valid Phase 2 source files remain valid in Phase 3.
- Phase 3 changes live in `phase3/`, root navigation documentation, Phase 3 design documentation, or `deliverables/phase3/`.
- Output ordering is deterministic except for measured timing and memory values.
- Optimization must preserve observable runtime state, execution log, and diagnostics.
- No variables, arithmetic expressions, loops, functions, nested scopes, LLVM, native machine code, database, or GUI.

## Review Focus

- Malformed IR with missing, duplicate, or backward label targets must return positioned optimizer diagnostics, never hang or crash; covered in Task 2.
- A condition whose capacity cannot be proven must remain unchanged and invalidate subsequent static capacity knowledge when its body may reserve; covered in Task 2.
- Benchmark iteration values of zero or below must be rejected as command-line usage errors; covered in Task 6.
- Timing noise must never make tests require a speedup or exact duration; covered in Task 5.
- Lexical, syntax, or semantic failure combined with `--benchmark` must stop before optimization and benchmarking; covered in Task 6.

---

### Task 1: Establish the Independent Phase 3 Baseline

**Files:**
- Create: `phase3/` by copying the tracked contents of `phase2/`
- Modify: `phase3/README.md`
- Create: `phase3/PHASE3_PROGRESS.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the verified Phase 2 compiler and its 46-test suite.
- Produces: an independently runnable `phase3/` baseline with unchanged Phase 2 behaviour and a documented Phase 3 identity.

- [ ] **Step 1: Copy the tracked Phase 2 tree into `phase3/`**

Copy source, tests, examples, `run.py`, and documentation without copying
`__pycache__`, `.pyc`, or other generated files.

- [ ] **Step 2: Rename Phase-specific documentation**

Change the Phase 3 README title and overview, replace
`PHASE2_PROGRESS.md` with `PHASE3_PROGRESS.md`, and state that optimization,
benchmarking, expanded tests, and final evidence are the planned additions.

- [ ] **Step 3: Add Phase 3 to the root navigation README**

Document `phase3/` and the baseline run command:

```bash
cd phase3
python3 run.py examples/valid.cflow
```

- [ ] **Step 4: Run the inherited suite and verify independence**

Run:

```bash
cd phase3
python3 -m unittest discover -s tests -v
python3 -m compileall -q campusflow run.py
```

Expected: 46 tests pass; `phase1/` and `phase2/` have no modified files.

- [ ] **Step 5: Commit**

```bash
git add README.md phase3
git commit -m "feat: establish CampusFlow phase 3 baseline"
```

---

### Task 2: Implement Safe IR Optimization

**Files:**
- Create: `phase3/campusflow/optimizer.py`
- Create: `phase3/tests/test_optimizer.py`
- Modify: `phase3/campusflow/__init__.py`

**Interfaces:**
- Consumes: `IRProgram` and `Instruction` from `campusflow.ir`.
- Produces: `OptimizerDiagnostic`, `OptimizationStats`, `OptimizationResult`, `IROptimizer.optimize(program: IRProgram) -> OptimizationResult`, and `format_optimization(result: OptimizationResult) -> str`.

- [ ] **Step 1: Write failing optimizer-model and true-fold tests**

Add tests asserting:

```python
result = IROptimizer().optimize(program_with_capacity_100_and_if_ge_50)
assert [item.opcode for item in result.optimized.instructions] == [
    "RESERVE_RESOURCE", "ASSIGN_ITEM"
]
assert result.stats.original_count == 4
assert result.stats.optimized_count == 2
assert result.stats.folded_true == 1
assert result.errors == ()
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_optimizer -v`

Expected: import failure for `campusflow.optimizer`.

- [ ] **Step 3: Implement optimizer records and true-condition folding**

Define frozen dataclasses with these fields:

```python
OptimizerDiagnostic(message: str, line: int, column: int)
OptimizationStats(
    original_count: int,
    optimized_count: int,
    folded_true: int,
    folded_false: int,
)
OptimizationResult(
    original: IRProgram,
    optimized: IRProgram,
    stats: OptimizationStats,
    log: tuple[str, ...],
    errors: tuple[OptimizerDiagnostic, ...],
)
```

`OptimizationStats` exposes computed `removed_count: int` and
`reduction_percent: float` properties. Use a local comparison-operator map
and a forward `known_capacity: int | None` state.

- [ ] **Step 4: Add failing false-fold and capacity-update tests**

Assert that an always-false condition removes its body, jump, and label, and
that a retained true conditional `RESERVE_RESOURCE` updates the known capacity
used by the following condition.

- [ ] **Step 5: Implement false folding and forward capacity updates**

Match each `JUMP_IF_FALSE` to its unique later `LABEL`; fold only a recognized,
non-nested region. Preserve source positions on retained instructions and add
stable log messages for every true or false fold.

- [ ] **Step 6: Add malformed and unprovable-control-flow tests**

Cover:

- missing target label;
- duplicate label;
- backward target;
- unknown operator;
- unknown current capacity; and
- an unproven branch whose body contains `RESERVE_RESOURCE`.

Assert malformed control flow produces positioned diagnostics. Assert
unprovable valid control flow is preserved and later capacity becomes unknown
when either branch could change it.

- [ ] **Step 7: Implement validation and conservative preservation**

Build a label table before folding. On structural errors, return the original
program as `optimized`, zero folds, and all diagnostics. When proof is
unavailable without a structural error, retain the region unchanged.

- [ ] **Step 8: Implement deterministic optimization formatting**

`format_optimization` prints original count, optimized count, removed count,
reduction percentage with two decimals, true/false fold counts, diagnostics,
and transformation log in a stable order.

- [ ] **Step 9: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_optimizer -v
python3 -m unittest discover -s tests -v
```

Expected: all optimizer tests and all inherited tests pass.

- [ ] **Step 10: Commit**

```bash
git add phase3/campusflow/optimizer.py phase3/campusflow/__init__.py phase3/tests/test_optimizer.py
git commit -m "feat: optimize CampusFlow intermediate code"
```

---

### Task 3: Integrate Optimization into the Compiler Pipeline

**Files:**
- Modify: `phase3/campusflow/pipeline.py`
- Modify: `phase3/tests/test_pipeline.py`

**Interfaces:**
- Consumes: `IROptimizer.optimize(IRProgram) -> OptimizationResult` from Task 2.
- Produces: `PipelineResult.optimization`, `PipelineResult.optimized_ir`, `PipelineResult.optimizer_errors`, and the new `optimized` compiler stage.

- [ ] **Step 1: Write failing pipeline-stage tests**

Assert:

```python
result = compile_source(valid_source, stage="optimized")
assert result.ir is not None
assert result.optimization is not None
assert result.optimized_ir == result.optimization.optimized
assert result.execution is None
```

Also assert `stage="all"` executes `optimized_ir`, not `ir`.

- [ ] **Step 2: Run pipeline tests and confirm RED**

Run: `python3 -m unittest tests.test_pipeline -v`

Expected: `optimized` is rejected as an unknown stage or fields are missing.

- [ ] **Step 3: Extend the pipeline data model**

Add `optimized` to `STAGES`. Keep `PipelineResult.ir` as original IR and add:

```python
optimization: OptimizationResult | None = None
optimized_ir: IRProgram | None = None
optimizer_errors: tuple[OptimizerDiagnostic, ...] = ()
```

- [ ] **Step 4: Gate optimization and optimized execution**

Run the optimizer after semantic success. Return after optimization for
`stage="optimized"`; stop on optimizer errors; otherwise execute optimized IR
for `run` and `all`.

- [ ] **Step 5: Add regression tests for earlier-stage gating**

For lexical, syntax, and semantic errors, assert optimization, optimized IR,
and execution remain absent. Retain the invalid-stage test.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_pipeline -v
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add phase3/campusflow/pipeline.py phase3/tests/test_pipeline.py
git commit -m "feat: integrate optimized CampusFlow pipeline"
```

---

### Task 4: Expose Optimized IR in the CLI

**Files:**
- Modify: `phase3/campusflow/cli.py`
- Modify: `phase3/tests/test_cli.py`
- Modify: `phase3/tests/test_examples.py`

**Interfaces:**
- Consumes: original IR, `OptimizationResult`, optimized IR, and optimizer diagnostics from Task 3.
- Produces: `--stage optimized` output and optimizer diagnostic formatting.

- [ ] **Step 1: Write failing CLI tests for the optimized stage**

Assert `--stage optimized` output contains these sections in order:

```text
ORIGINAL INTERMEDIATE CODE
OPTIMIZATION SUMMARY
OPTIMIZED INTERMEDIATE CODE
```

Assert it omits tokens, AST, semantic summary, and final runtime state.

- [ ] **Step 2: Run CLI tests and confirm RED**

Run: `python3 -m unittest tests.test_cli -v`

Expected: argparse rejects `optimized` or required sections are absent.

- [ ] **Step 3: Implement optimized-stage formatting**

Use `format_ir` for both programs and `format_optimization` for the summary.
For `all`, display original IR, the optimization summary, optimized IR, and
then the runtime state. For optimizer errors, print `OPTIMIZER ERRORS` with
line and column positions and return exit status `1`.

- [ ] **Step 4: Update CLI regression assertions**

Adjust inherited `all`-stage tests to require optimization sections while
preserving existing token, AST, semantic, and runtime assertions.

- [ ] **Step 5: Run CLI, example, and full tests**

Run:

```bash
python3 -m unittest tests.test_cli tests.test_examples -v
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add phase3/campusflow/cli.py phase3/tests/test_cli.py phase3/tests/test_examples.py
git commit -m "feat: display optimized CampusFlow IR"
```

---

### Task 5: Add Correctness-Aware Performance Measurement

**Files:**
- Create: `phase3/campusflow/metrics.py`
- Create: `phase3/tests/test_metrics.py`
- Modify: `phase3/campusflow/__init__.py`

**Interfaces:**
- Consumes: original and optimized `IRProgram` values and `Interpreter.execute`.
- Produces: `BenchmarkResult`, `benchmark_ir(original: IRProgram, optimized: IRProgram, *, iterations: int) -> BenchmarkResult`, and `format_benchmark(result: BenchmarkResult) -> str`.

- [ ] **Step 1: Write failing benchmark validation and equivalence tests**

Assert `iterations <= 0` raises `ValueError("Benchmark iterations must be greater than zero")`. For equivalent programs, assert:

```python
assert result.iterations == 5
assert result.equivalent is True
assert result.original_instruction_count >= result.optimized_instruction_count
assert result.original_median_ns >= 0
assert result.optimized_median_ns >= 0
assert result.original_peak_bytes >= 0
assert result.optimized_peak_bytes >= 0
```

- [ ] **Step 2: Run metrics tests and confirm RED**

Run: `python3 -m unittest tests.test_metrics -v`

Expected: import failure for `campusflow.metrics`.

- [ ] **Step 3: Implement `BenchmarkResult` and benchmark execution**

Define a frozen dataclass with:

```python
iterations: int
original_instruction_count: int
optimized_instruction_count: int
original_median_ns: int
optimized_median_ns: int
original_peak_bytes: int
optimized_peak_bytes: int
equivalent: bool
```

Warm up both programs once. Time fresh `Interpreter` executions with
`perf_counter_ns`, calculate integer medians with `statistics.median`, and
measure peak memory separately with `tracemalloc`. Equivalence compares complete
`ExecutionResult` values.

- [ ] **Step 4: Add non-equivalence and timing-noise tests**

Use deliberately different original and optimized programs and assert
`equivalent is False`. Patch the timer with repeated equal and decreasing
values and assert no test or implementation requires positive speedup.

- [ ] **Step 5: Implement stable benchmark formatting**

Print iterations, instruction counts, reduction percentage, median times,
measured time ratio (or `n/a` for zero optimized time), peak bytes, and
`PASS`/`FAIL` equivalence. Do not print a claim that optimized execution is
always faster.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_metrics -v
python3 -m unittest discover -s tests -v
```

Expected: all tests pass without timing-dependent flakes.

- [ ] **Step 7: Commit**

```bash
git add phase3/campusflow/metrics.py phase3/campusflow/__init__.py phase3/tests/test_metrics.py
git commit -m "feat: measure CampusFlow execution performance"
```

---

### Task 6: Add CLI Benchmark Mode

**Files:**
- Modify: `phase3/campusflow/cli.py`
- Modify: `phase3/tests/test_cli.py`

**Interfaces:**
- Consumes: `benchmark_ir` and `format_benchmark` from Task 5 plus successful pipeline output.
- Produces: `--benchmark N` with positive-integer validation and appended performance output.

- [ ] **Step 1: Write failing benchmark CLI tests**

Test that:

- `--benchmark 3` appends `PERFORMANCE MEASUREMENT` and equivalence `PASS`;
- `--benchmark 0` and `--benchmark -1` return argparse status `2`;
- a lexical, syntax, or semantic failure with `--benchmark 3` contains no
  performance section; and
- benchmarking does not change the requested successful stage sections.

- [ ] **Step 2: Run CLI tests and confirm RED**

Run: `python3 -m unittest tests.test_cli -v`

Expected: argparse does not recognize `--benchmark`.

- [ ] **Step 3: Implement positive iteration parsing**

Add `_positive_int(value: str) -> int`; raise
`argparse.ArgumentTypeError("must be greater than zero")` when invalid. Add
optional `--benchmark N` to `main`.

- [ ] **Step 4: Append benchmarks only after successful compilation**

Refactor CLI formatting so it can return the successful `PipelineResult` or
otherwise make original and optimized IR available without recompiling.
Benchmark only when both IR programs exist and no diagnostic occurred.

- [ ] **Step 5: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_cli -v
python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add phase3/campusflow/cli.py phase3/tests/test_cli.py
git commit -m "feat: add CampusFlow benchmark CLI"
```

---

### Task 7: Add Boundary and Complex Demonstrations

**Files:**
- Create: `phase3/examples/optimization_demo.cflow`
- Create: `phase3/examples/boundary_cases.cflow`
- Create: `phase3/examples/complex_schedule.cflow`
- Create: `phase3/tests/test_phase3_examples.py`

**Interfaces:**
- Consumes: complete optimized CLI and benchmark mode from Tasks 4–6.
- Produces: stable end-to-end demonstrations for optimization, boundaries, complex input, and benchmark output.

- [ ] **Step 1: Write failing example tests before the files exist**

Assert subprocess runs for each file exit `0`. Require:

- optimization demo folds at least one true and one false condition;
- boundary demo accepts capacity `1`, equality comparisons, and adjacent
  intervals;
- complex demo creates, reserves, assigns, conditionally acts, cancels, and
  reuses a resource; and
- complex benchmark reports equivalence `PASS`.

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `python3 -m unittest tests.test_phase3_examples -v`

Expected: files are missing.

- [ ] **Step 3: Add `optimization_demo.cflow`**

Use known capacities and two conditions whose results are provably true and
false. Include state-changing bodies so equivalence is meaningful.

- [ ] **Step 4: Add `boundary_cases.cflow`**

Include capacity `1`, `==` and `!=`, events whose intervals meet exactly at a
boundary, and legal reuse of the same resource across those events.

- [ ] **Step 5: Add `complex_schedule.cflow`**

Include at least six events, multiple resources and assignments, true and
false conditions, cancellation, and legal reuse after cancellation while
remaining readable during a live demonstration.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_phase3_examples -v
python3 -m unittest discover -s tests -v
```

Expected: all examples and tests pass.

- [ ] **Step 7: Commit**

```bash
git add phase3/examples phase3/tests/test_phase3_examples.py
git commit -m "test: add CampusFlow phase 3 demonstrations"
```

---

### Task 8: Complete User Documentation and Evidence

**Files:**
- Modify: `phase3/README.md`
- Modify: `phase3/PHASE3_PROGRESS.md`
- Create: `phase3/evidence/test_results.txt`
- Create: `phase3/evidence/optimization_output.txt`
- Create: `phase3/evidence/complex_output.txt`
- Create: `phase3/evidence/benchmark_output.txt`
- Modify: `README.md`

**Interfaces:**
- Consumes: final commands, examples, passing tests, and measured output from Tasks 1–7.
- Produces: complete user instructions, rubric mapping, reproducible command evidence, and accurate project navigation.

- [ ] **Step 1: Rewrite the Phase 3 README around the delivered system**

Document requirements, grammar, compiler architecture, optimizer algorithm,
all CLI stages, benchmarking, examples, exit statuses, module guide, testing,
limitations, and copy-paste commands for macOS/Linux and Windows.

- [ ] **Step 2: Complete `PHASE3_PROGRESS.md`**

Map every rubric activity, deliverable, and review criterion to concrete
modules, tests, evidence files, or final artifacts. Do not describe incomplete
future work as completed.

- [ ] **Step 3: Capture final reproducible evidence**

Run commands from `phase3/` and save complete outputs:

```bash
python3 -m unittest discover -s tests -v
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/complex_schedule.cflow --stage all
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

Timing evidence records the date, Python version, platform, and iteration
count. Output files must not contain absolute local paths.

- [ ] **Step 4: Update root navigation**

Make Phase 3 the clearly identified final implementation while preserving
links and commands for Phase 1 and Phase 2.

- [ ] **Step 5: Verify documentation commands**

Execute every documented command at least once and scan:

```bash
rg -n "TODO|TBD|campusflow_phase1|phase 2 directory" README.md phase3
```

Expected: no stale path, placeholder, or contradictory Phase reference.

- [ ] **Step 6: Commit**

```bash
git add README.md phase3/README.md phase3/PHASE3_PROGRESS.md phase3/evidence
git commit -m "docs: complete CampusFlow phase 3 evidence"
```

---

### Task 9: Generate and Verify the Final Word Report

**Files:**
- Create: `deliverables/phase3/CampusFlow_Phase3_Final_Project_Report.docx`
- Create: `docs/phase3/build_final_report.py`

**Interfaces:**
- Consumes: final implementation, module explanations, tests, evidence, and measured results from Tasks 1–8.
- Produces: a visually verified final Word report matching the Phase 3 rubric.

- [ ] **Step 1: Read and follow the documents artifact skill**

Use the required `.docx` creation, rendering, and visual-verification workflow.
The report-generation source remains reproducible in `docs/phase3/`.

- [ ] **Step 2: Generate the complete report**

Include objective, problem definition, grammar, architecture, algorithms,
module-wise implementation, optimizer before/after example, performance
method and results, test matrix, test results, error demonstrations, complex
output evidence, user instructions, review-criteria mapping, limitations,
conclusion, and selected core source listings.

- [ ] **Step 3: Validate report facts against the final tree**

Automatically confirm test counts, module names, commands, example names,
instruction counts, and captured metrics before embedding them. Do not type
measured values manually.

- [ ] **Step 4: Render and inspect every report page**

Render to page images and PDF, inspect every page for clipping, blank pages,
split headings, unreadable code, inconsistent tables, and incorrect page
numbers. Iterate until the visual QA pass is clean.

- [ ] **Step 5: Verify DOCX archive integrity**

Run: `unzip -t deliverables/phase3/CampusFlow_Phase3_Final_Project_Report.docx`

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add docs/phase3 deliverables/phase3/CampusFlow_Phase3_Final_Project_Report.docx
git commit -m "docs: add CampusFlow final project report"
```

---

### Task 10: Generate Presentation and Submission ZIP

**Files:**
- Create: `deliverables/phase3/CampusFlow_Phase3_Presentation.pptx`
- Create: `deliverables/phase3/CampusFlow_Phase3_Project.zip`
- Create: `deliverables/phase3/README.md`
- Create: `docs/phase3/build_presentation.py`

**Interfaces:**
- Consumes: final code, report, evidence, user instructions, and review mapping.
- Produces: verified final presentation and clean runnable submission archive.

- [ ] **Step 1: Read and follow the presentation artifact skill**

Create a concise presentation covering the problem, language examples,
pipeline, algorithms, Phase 1-to-3 progression, optimizer demonstration,
testing, performance, outputs, conclusion, and live-demo commands.

- [ ] **Step 2: Render and visually inspect every slide**

Check readability, clipping, consistency, source/output accuracy, and live-demo
commands. Iterate until the presentation QA pass is clean.

- [ ] **Step 3: Build the clean Phase 3 ZIP**

Package `phase3/` under a top-level `campusflow_phase3/` directory. Exclude
`__pycache__`, `.pyc`, `.DS_Store`, local benchmark scratch files, and Git
metadata. Include source, examples, tests, evidence, README, progress report,
and `run.py`.

- [ ] **Step 4: Test the ZIP from a clean extraction**

Verify archive integrity, extract to a temporary directory, then run:

```bash
python3 -m unittest discover -s tests -v
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/complex_schedule.cflow --benchmark 10
```

Expected: all tests pass, compilation succeeds, and benchmark equivalence is
`PASS`.

- [ ] **Step 5: Write the deliverables README**

List the ZIP, Word report, presentation, requirements, extraction steps,
demonstration command, test command, and expected successful outcomes.

- [ ] **Step 6: Run final repository verification**

Run Phase 1, Phase 2, and Phase 3 test suites independently; compile Phase 3;
verify both Office archives and the ZIP; scan for cache files, placeholders,
stale paths, and future-work claims presented as complete.

- [ ] **Step 7: Commit**

```bash
git add docs/phase3 deliverables/phase3
git commit -m "docs: package CampusFlow phase 3 submission"
```

- [ ] **Step 8: Request final code review and prepare integration**

Review the complete branch against the approved spec and this plan. Resolve
findings, rerun all verification commands, and only then use the branch-
finishing workflow chosen by the user.
