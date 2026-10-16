# CampusFlow Phase 3 Submission

This folder contains the final Phase 3 submission artifacts for the CampusFlow
DSL compiler.

## Files

- `CampusFlow_Phase3_Project.zip` — clean runnable source, examples, tests,
  evidence, progress report, and user instructions.
- `CampusFlow_Phase3_Final_Project_Report.docx` — complete final report.
- `CampusFlow_Phase3_Presentation.pptx` — ten-slide review and demonstration
  presentation with editable tables and charts.

## Requirements

- Python 3.10 or newer
- A terminal, including the terminal in Visual Studio Code
- No third-party Python packages

## Extract and Run

Extract `CampusFlow_Phase3_Project.zip`, open a terminal, and enter the extracted
folder:

```bash
cd campusflow_phase3
```

Run the complete compiler demonstration:

```bash
python3 run.py examples/complex_schedule.cflow --stage all
```

Run the optimizer demonstration:

```bash
python3 run.py examples/optimization_demo.cflow --stage optimized
```

Run the performance and equivalence check:

```bash
python3 run.py examples/complex_schedule.cflow --benchmark 100
```

Run all automated tests:

```bash
python3 -m unittest discover -s tests -v
```

On Windows, use `py` instead of `python3` and use backslashes in file paths if
needed.

## Expected Successful Results

- The full compiler prints tokens, AST, semantic status, original IR,
  optimization details, optimized IR, and final runtime state.
- The optimizer demonstration reduces eight original instructions to three.
- The complex example reduces 29 instructions to 19 and reports an equivalent
  final state of `PASS`.
- The test command reports 71 tests and `OK`.

Detailed language syntax, module explanations, limitations, and additional
commands are provided in the `README.md` inside the ZIP.
