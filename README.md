# CampusFlow

CampusFlow is an educational domain-specific language compiler for campus
event scheduling. The repository keeps each assessed submission in its own
folder so that Phase 1 and Phase 2 can be demonstrated independently.

## Repository structure

- `phase1/` — the original lexical-analysis submission.
- `phase2/` — the working compiler pipeline with parsing, AST construction,
  semantic analysis, symbol tables, intermediate code, and execution.
- `deliverables/phase2/` — the Phase 2 project ZIP, Word report, and submission
  notes.

## Run Phase 1

```bash
cd phase1
python3 run.py examples/valid.cflow
python3 -m unittest discover -s tests -v
```

## Run Phase 2

```bash
cd phase2
python3 run.py examples/valid.cflow
python3 -m unittest discover -s tests -v
```

On Windows, use `py` instead of `python3` when necessary. Both phases require
Python 3.10 or newer and use only the standard library.
