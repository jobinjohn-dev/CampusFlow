# CampusFlow DSL Compiler — Phase 2

## Overview

CampusFlow is a small domain-specific language for declaring campus events,
reserving venues, assigning equipment, applying capacity conditions, and
cancelling events. Phase 2 implements a complete educational compiler
pipeline:

```text
source -> tokens -> AST -> semantic analysis -> IR -> execution
```

The compiler reports source positions at every error stage and executes valid
programs in a deterministic in-memory runtime. It uses only the Python
standard library.

## Requirements

- Python 3.10 or newer
- A terminal, including the terminal built into Visual Studio Code

No package installation is required.

## Quick Start

From the `campusflow_phase1` directory, run the complete demonstration:

```bash
python3 run.py examples/valid.cflow
```

On Windows, use `py` when `python3` is unavailable:

```powershell
py run.py examples\valid.cflow
```

The valid demonstration exits with status `0`. Compiler or runtime
diagnostics exit with status `1`; command-line or file errors exit with
status `2`.

## CLI Stages

The default stage is `all`:

```bash
python3 run.py examples/valid.cflow
python3 run.py examples/valid.cflow --stage tokens
python3 run.py examples/valid.cflow --stage ast
python3 run.py examples/valid.cflow --stage ir
python3 run.py examples/valid.cflow --stage run
```

| Stage | Result |
|---|---|
| `tokens` | Token table and lexical diagnostics |
| `ast` | Parsed abstract syntax tree |
| `ir` | Semantically validated intermediate instructions |
| `run` | Final runtime state and execution log |
| `all` | Tokens, AST, semantic result, IR, and execution |

The pipeline stops before an unsafe later stage whenever it finds errors.

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

Keywords are case-insensitive. Identifiers are case-sensitive. A `#` begins
a comment that continues to the end of its line.

## Statement Semantics

- `EVENT` declares a uniquely named, single-day event whose end time is later
  than its start time.
- `RESERVE` books a resource for an active declared event with a positive
  capacity.
- `ASSIGN` attaches an item to an active declared event.
- `CANCEL` marks an event cancelled and releases its current reservations and
  assignments.
- `IF capacity ... THEN ...` compares the capacity from the most recent
  successful reservation and conditionally executes one `RESERVE`, `ASSIGN`,
  or `CANCEL` statement.

The same resource or item cannot be used by overlapping active events.
Intervals are half-open, so `10:00 TO 11:00` and `11:00 TO 12:00` do not
conflict.

## Compiler Pipeline

1. The lexer classifies source characters into positioned tokens.
2. The recursive-descent parser validates grammar and constructs an AST.
3. Semantic analysis builds a symbol table and checks declarations, time
   ranges, capacities, cancellations, and schedule conflicts.
4. The IR generator emits readable linear instructions and conditional jumps.
5. The interpreter executes those instructions in an in-memory runtime.

## Module Guide

| Module | Responsibility |
|---|---|
| `model.py` | Token and lexical diagnostic records |
| `lexer.py` | Lexical analysis and recovery |
| `ast_nodes.py` | Immutable AST records and tree formatting |
| `parser.py` | Grammar validation and syntax recovery |
| `symbols.py` | Event, reservation, and assignment symbols |
| `semantic.py` | Source-ordered semantic validation |
| `ir.py` | Intermediate instructions and lowering |
| `interpreter.py` | Runtime state and instruction execution |
| `pipeline.py` | Safe compiler-stage coordination |
| `cli.py` | Stage selection and terminal formatting |

## Error Stages

- **Lexical:** illegal characters, invalid dates/times, unknown operators, and
  unterminated strings.
- **Syntax:** missing or unexpected grammar elements. Recovery resumes after
  the next semicolon.
- **Semantic:** duplicate or undeclared events, invalid capacities/time ranges,
  cancelled references, and scheduling conflicts.
- **Runtime:** defensive checks for malformed IR or invalid state transitions.

Every diagnostic includes a one-based line and column.

## Demonstration Files

```bash
python3 run.py examples/valid.cflow
python3 run.py examples/invalid.cflow
python3 run.py examples/syntax_errors.cflow
python3 run.py examples/semantic_errors.cflow
python3 run.py examples/resource_conflict.cflow
```

| File | Demonstrates |
|---|---|
| `valid.cflow` | Complete successful pipeline and all statement forms |
| `invalid.cflow` | Lexical diagnostics |
| `syntax_errors.cflow` | Parser diagnostics and recovery |
| `semantic_errors.cflow` | Declaration and value validation |
| `resource_conflict.cflow` | Overlapping resource rejection |

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite includes unit tests for every compiler stage plus subprocess-based
CLI and end-to-end example tests.

## Example Output

The full output includes a token table. The following is an abbreviated
literal excerpt from the valid demonstration:

```text
ABSTRACT SYNTAX TREE
--------------------
Program
  Event TechFest date=2026-10-15 start=10:00 end=12:00 @2:1

SEMANTIC ANALYSIS
-----------------
Semantic analysis: passed.

INTERMEDIATE CODE
-----------------
0000  CREATE_EVENT 'TechFest', '2026-10-15', '10:00', '12:00'  @2:1
0001  CREATE_EVENT 'Workshop', '2026-10-15', '13:00', '15:00'  @3:1
0002  CREATE_EVENT 'OldMeet', '2026-10-16', '09:00', '10:00'  @4:1

FINAL RUNTIME STATE
-------------------
TechFest [ACTIVE] 2026-10-15 10:00-12:00
  RESERVATION Auditorium_A capacity=150
  ASSIGNMENT Projector
Workshop [ACTIVE] 2026-10-15 13:00-15:00
  RESERVATION Seminar_Hall capacity=120
OldMeet [CANCELLED] 2026-10-16 09:00-10:00
```

## Current Limitations

- Execution is in memory and is not connected to a real calendar or database.
- Events are single-day and times do not cross midnight.
- Conditions use only the built-in most-recent `capacity` value and an integer.
- An `IF` body contains exactly one reservation, assignment, or cancellation.
- The language has no user-defined variables, functions, or nested scopes.
