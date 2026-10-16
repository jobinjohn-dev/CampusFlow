# CampusFlow DSL Compiler — Phase 3 Final Implementation

CampusFlow is a small compiler and interpreter for describing campus events,
venue reservations, equipment assignments, capacity-based actions, and event
cancellation. Phase 3 is the complete project: it performs lexical, syntax,
and semantic analysis; produces intermediate code; safely optimizes that code;
executes it; and measures original-versus-optimized behavior.

```text
source -> lexer -> parser/AST -> semantic analysis -> original IR
       -> optimizer -> optimized IR -> interpreter -> runtime state
```

The implementation uses only the Python standard library.

## Requirements

- Python 3.10 or newer
- A terminal (the Visual Studio Code terminal works)
- No package installation

## Quick Start

macOS or Linux, from the repository root:

```bash
cd phase3
python3 run.py examples/complex_schedule.cflow
```

Windows PowerShell, from the repository root:

```powershell
cd phase3
py run.py examples\complex_schedule.cflow
```

The full command prints tokens, AST, semantic results, original IR,
optimization results, optimized IR, final runtime state, and an execution log.

## Language Grammar

```text
program               = { statement } EOF ;
statement             = event_statement
                      | reserve_statement
                      | assign_statement
                      | cancel_statement
                      | if_statement ;
event_statement       = "EVENT" IDENTIFIER "ON" DATE
                        "AT" TIME "TO" TIME ";" ;
reserve_statement     = "RESERVE" IDENTIFIER "FOR" IDENTIFIER
                        "CAPACITY" NUMBER ";" ;
assign_statement      = "ASSIGN" IDENTIFIER "TO" IDENTIFIER ";" ;
cancel_statement      = "CANCEL" IDENTIFIER ";" ;
if_statement          = "IF" "CAPACITY" comparison NUMBER
                        "THEN" conditional_statement ;
comparison            = ">" | "<" | ">=" | "<=" | "==" | "!=" ;
conditional_statement = reserve_statement
                      | assign_statement
                      | cancel_statement ;
```

Keywords are case-insensitive, identifiers are case-sensitive, and `#`
starts a comment. Dates use `YYYY-MM-DD`; times use 24-hour `HH:MM`.

## Meaning of Statements

- `EVENT` declares a unique, single-day event with an end after its start.
- `RESERVE` books a resource for an active event with positive capacity.
- `ASSIGN` attaches an item to an active event.
- `CANCEL` cancels an event and releases its reservations and assignments.
- `IF capacity ... THEN ...` compares the most recent successful reservation's
  capacity and conditionally executes one reservation, assignment, or cancel.

Resources and items cannot be shared by overlapping active events. Intervals
are half-open, so an event ending at `11:00` does not conflict with one starting
at `11:00`.

## Compiler Architecture

1. `lexer.py` recognizes positioned tokens and reports recoverable lexical
   errors.
2. `parser.py` uses recursive descent to validate grammar and build immutable
   nodes from `ast_nodes.py`.
3. `semantic.py` and `symbols.py` validate declarations, capacities, times,
   cancellation, and scheduling conflicts.
4. `ir.py` lowers the AST to linear instructions and forward conditional
   jumps.
5. `optimizer.py` validates IR control flow and applies safe constant-condition
   folding.
6. `interpreter.py` executes optimized IR in an in-memory runtime.
7. `metrics.py` compares execution results and records instruction count,
   median execution time, and peak traced memory.
8. `pipeline.py` gates every stage so an error prevents unsafe later work;
   `cli.py` exposes the pipeline in the terminal.

## Optimization Algorithm

The optimizer performs a forward data-flow pass over the linear IR. It tracks
the last statically known reservation capacity. For each forward
`JUMP_IF_FALSE`:

- a condition known to be true loses its jump and label but keeps its body;
- a condition known to be false loses its jump, body, and label;
- a condition without a provable capacity is preserved unchanged;
- a preserved or nested control-flow region invalidates capacity knowledge;
- malformed, duplicate, missing, backward, or unknown control flow produces a
  positioned diagnostic and leaves the original program unchanged.

This is conservative: it optimizes only when the result is provable. Execution
equivalence is independently checked by benchmark mode.

## CLI Stages

```bash
python3 run.py examples/valid.cflow --stage tokens
python3 run.py examples/valid.cflow --stage ast
python3 run.py examples/valid.cflow --stage ir
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/valid.cflow --stage run
python3 run.py examples/valid.cflow --stage all
```

| Stage | Output |
|---|---|
| `tokens` | Token table and lexical status |
| `ast` | Abstract syntax tree |
| `ir` | Semantically validated original intermediate code |
| `optimized` | Original IR, optimization summary, and optimized IR |
| `run` | Final runtime state and execution log |
| `all` | Every compiler artifact in order (default) |

Windows uses the same options with `py` and backslashes in paths.

## Benchmark Mode

Append a positive iteration count to a successful `optimized` or `all` run:

```bash
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

```powershell
py run.py examples\complex_schedule.cflow --benchmark 100
```

The report includes original and optimized instruction counts, reduction,
median execution time, measured ratio, peak memory, and `PASS`/`FAIL` execution
equivalence. Timing varies by machine and is reported as a measurement, not a
promise that every optimized run is faster.

## Demonstration Files

| File | Purpose |
|---|---|
| `valid.cflow` | All core statement types and successful execution |
| `optimization_demo.cflow` | One provably true and one false condition |
| `boundary_cases.cflow` | Capacity 1, equality operators, adjacent intervals |
| `complex_schedule.cflow` | Six events, conditions, cancellation, and reuse |
| `invalid.cflow` | Lexical errors |
| `syntax_errors.cflow` | Parser errors and recovery |
| `semantic_errors.cflow` | Declaration and value errors |
| `resource_conflict.cflow` | Overlapping resource rejection |

Useful live-demonstration commands:

```bash
python3 run.py examples/optimization_demo.cflow --stage optimized
python3 run.py examples/boundary_cases.cflow
python3 run.py examples/complex_schedule.cflow
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

## Exit Statuses and Errors

- `0`: requested compilation, execution, and optional benchmark succeeded.
- `1`: lexical, syntax, semantic, optimizer, or runtime diagnostics occurred.
- `2`: invalid command-line argument or unreadable input file.

Every compiler diagnostic includes a one-based line and column. The pipeline
stops at the failing stage; benchmark output is never produced for invalid
input.

## Module Guide

| Module | Responsibility |
|---|---|
| `model.py` | Tokens and lexical diagnostics |
| `lexer.py` | Lexical analysis and recovery |
| `ast_nodes.py` | Immutable AST and tree formatter |
| `parser.py` | Recursive-descent parsing and recovery |
| `symbols.py` | Event, reservation, and assignment symbols |
| `semantic.py` | Source-ordered semantic checks |
| `ir.py` | IR instructions, generation, and formatting |
| `optimizer.py` | IR validation, folding, and statistics |
| `interpreter.py` | Runtime validation, state, and execution |
| `metrics.py` | Equivalence-aware time and memory measurement |
| `pipeline.py` | Compiler stage coordination |
| `cli.py` | Terminal arguments and output formatting |
| `run.py` | Executable entry point |

## Testing

macOS or Linux:

```bash
cd phase3
python3 -m unittest discover -s tests -v
python3 -m compileall -q campusflow tests run.py
```

Windows PowerShell:

```powershell
cd phase3
py -m unittest discover -s tests -v
py -m compileall -q campusflow tests run.py
```

The tests cover units, pipeline gating, CLI subprocesses, valid/invalid input,
boundaries, malformed IR, optimizer safety, timing noise, equivalence, and
complex end-to-end execution. Recorded outputs are in `evidence/`.

## Limitations

- State is in memory; there is no external database or calendar integration.
- Events are single-day and cannot cross midnight.
- `capacity` is the only built-in conditional value.
- An `IF` body contains one non-`EVENT` statement; nesting is not in the source
  grammar.
- There are no user variables, functions, loops, or generated machine code.
- Benchmark values are environment-dependent and should be interpreted with
  the recorded platform information.
