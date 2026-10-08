# CampusFlow DSL Phase 1

This package contains the Phase 1 lexical-analyzer prototype for the
CampusFlow DSL Compiler and Virtual Machine project. It uses only the Python
standard library.

## Requirements

- Python 3.10 or newer
- A terminal or the terminal included in Visual Studio Code

## Run the valid example

From this folder, run:

```bash
python3 run.py examples/valid.cflow
```

On Windows, if `python3` is not available, use:

```powershell
py run.py examples\valid.cflow
```

The command prints a token table followed by `No lexical errors.` and exits
with status code 0.

## Run the invalid example

```bash
python3 run.py examples/invalid.cflow
```

The lexer prints every safely recoverable token, lists the lexical errors with
line and column positions, and exits with status code 1.

## Run all automated tests

```bash
python3 -m unittest discover -s tests -v
```

All tests should report `ok`, followed by an `OK` summary.

## Test your own program

Create a text file ending in `.cflow`, for example `examples/my_test.cflow`:

```text
EVENT Workshop ON 2026-11-20 AT 09:30 TO 11:00;
RESERVE Lab_201 FOR Workshop CAPACITY 60;
ASSIGN Projector TO Workshop;
```

Then run:

```bash
python3 run.py examples/my_test.cflow
```

Phase 1 checks only lexical structure. Parsing, semantic checks, scheduling,
intermediate instructions, optimization, and virtual-machine execution are
planned for Phases 2 and 3.
