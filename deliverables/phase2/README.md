# CampusFlow Phase 2 Submission

This folder contains the Phase 2 submission artifacts:

- `CampusFlow_Phase2_Project.zip` — runnable compiler source, demonstrations,
  automated tests, and the implementation progress summary.
- `CampusFlow_DSL_Phase_2_Progress_Report.docx` — the Phase 2 report covering
  the implemented compiler modules, demonstrations, test evidence,
  intermediate results, and core source listings.

## Run the packaged project

Extract `CampusFlow_Phase2_Project.zip`, open a terminal in the extracted
`campusflow_phase2` folder, and run:

```bash
python3 run.py examples/phase2_valid.cflow
python3 -m unittest discover -s tests -v
```

The implementation requires Python 3.10 or newer and uses only the standard
library.
