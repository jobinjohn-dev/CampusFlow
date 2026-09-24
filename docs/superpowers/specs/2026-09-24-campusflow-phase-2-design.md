# CampusFlow Phase 2 Design

## Purpose

Phase 2 turns the existing lexical-analyzer prototype into a small, working compiler pipeline for the CampusFlow domain-specific language. The finished system must be demonstrable from the terminal: it will tokenize a source file, parse it into an abstract syntax tree (AST), validate its meaning with a symbol table, generate readable intermediate instructions, execute those instructions in memory, and print the resulting campus schedule.

The implementation is intended for an academic compiler project and viva. Each compiler stage therefore has a distinct, understandable module and produces observable output. The project continues to use Python 3.10 or newer and the Python standard library only.

## Scope

Phase 2 includes:

- The existing lexical analysis, extended only where required by the grammar.
- Recursive-descent syntax analysis with recovery at statement boundaries.
- Typed AST construction and a readable tree formatter.
- Semantic analysis and symbol-table construction.
- Readable, linear intermediate code.
- An in-memory interpreter and runtime state.
- Stage-specific error handling and exit codes.
- Automated unit, integration, and end-to-end tests.
- Valid, invalid, and resource-conflict demonstration programs.
- Updated module documentation, grammar, commands, intermediate results, and an implementation-progress report.

Phase 2 does not include persistent storage, authentication, a GUI, calendar integration, networking, multi-day events, or a production scheduling service.

## Language

### Statements

CampusFlow supports five statement forms:

```text
EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;
RESERVE Auditorium_A FOR TechFest CAPACITY 150;
ASSIGN Projector TO TechFest;
IF capacity >= 100 THEN RESERVE Seminar_Hall FOR Workshop CAPACITY 120;
CANCEL OldMeet;
```

Keywords are case-insensitive. Identifiers preserve their spelling and are case-sensitive when looked up. Comments start with `#` and continue to the end of the line.

### Grammar

The grammar uses EBNF-like notation:

```text
program             = { statement } EOF ;
statement           = event_statement
                    | reserve_statement
                    | assign_statement
                    | cancel_statement
                    | if_statement ;

event_statement     = "EVENT" IDENTIFIER "ON" DATE
                      "AT" TIME "TO" TIME ";" ;
reserve_statement   = "RESERVE" IDENTIFIER "FOR" IDENTIFIER
                      "CAPACITY" NUMBER ";" ;
assign_statement    = "ASSIGN" IDENTIFIER "TO" IDENTIFIER ";" ;
cancel_statement    = "CANCEL" IDENTIFIER ";" ;
if_statement        = "IF" capacity_expression comparison NUMBER
                      "THEN" conditional_statement ;
capacity_expression = "CAPACITY" ;
comparison          = ">" | "<" | ">=" | "<=" | "==" | "!=" ;
conditional_statement = reserve_statement
                      | assign_statement
                      | cancel_statement ;
```

An `IF` body is limited to one non-`EVENT`, non-`IF` statement. This avoids nested declaration and control-flow complexity while still demonstrating expression evaluation and conditional jumps.

### Meaning

- `EVENT` declares a uniquely named event on one date. Its end time must be later than its start time.
- `RESERVE` books a named resource for an existing, active event. Capacity must be greater than zero. The interpreter stores the successful reservation capacity as the built-in `capacity` value.
- `ASSIGN` attaches a named item to an existing, active event. The same item cannot be assigned twice to one event or to overlapping active events.
- `CANCEL` marks an existing active event as cancelled and releases its reservations and assignments for subsequent conflict checks.
- `IF capacity <operator> NUMBER THEN ...` compares the most recently executed successful reservation capacity with the integer literal. It executes its body only when the comparison is true. Semantic analysis rejects a condition that appears before any preceding reservation can define `capacity`.

Two active events overlap when they occur on the same date and their half-open time intervals `[start, end)` intersect. A resource reservation or assigned item cannot be shared by overlapping active events. Adjacent events, where one starts exactly when another ends, do not conflict.

The valid demonstration will declare `Workshop` and `OldMeet` before they are referenced. Execution is local and in memory; it does not affect any external calendar or booking system.

## Architecture

The compiler pipeline is:

```text
source file
  -> Lexer
  -> token stream
  -> Parser
  -> AST
  -> SemanticAnalyzer + SymbolTable
  -> validated AST
  -> IRGenerator
  -> instruction sequence
  -> Interpreter
  -> RuntimeState
```

Each stage consumes the previous stage's public records and returns its own immutable result records where practical. A stage with errors prevents later stages from running.

### Lexical model

The existing `Lexer`, `Token`, `LexicalError`, and `ScanResult` remain the lexical boundary. Existing token kinds are retained. Keywords are compared case-insensitively, while token lexemes retain their original spelling and source positions.

### AST

`ast_nodes.py` defines small immutable dataclasses:

- `Program`
- `EventStatement`
- `ReserveStatement`
- `AssignStatement`
- `CancelStatement`
- `IfStatement`
- `CapacityExpression`
- `NumberLiteral`
- `ComparisonExpression`

Every statement and expression carries its source line and column. A separate formatter traverses the nodes and produces an indented, deterministic AST representation for the CLI and tests.

### Parser

`parser.py` implements a recursive-descent parser over the token stream. It matches keyword lexemes instead of treating all keywords as interchangeable. It produces a `ParseResult` containing a `Program` and zero or more `SyntaxDiagnostic` records.

When a statement fails to parse, the parser advances to the next semicolon or EOF and resumes. This permits multiple independent syntax diagnostics without risking an infinite loop. The parser never fabricates executable statements from malformed input.

### Symbol table and semantic analysis

`symbols.py` owns symbol records and lookup operations. The primary symbols are events, reservations, and assignments. Event symbols contain date/time information and cancellation state needed for conflict checks.

`semantic.py` traverses the AST without executing it and reports:

- Duplicate event declarations.
- Event end times that are not later than start times.
- References to undeclared events.
- Reservations or assignments for cancelled events.
- Non-positive capacities.
- Duplicate reservations and assignments.
- Resource or item conflicts between overlapping events.
- Cancellation of an undeclared or already cancelled event.
- Use of the built-in `capacity` before a preceding reservation can define it.

The analyzer processes statements in source order so cancellation can release resources for later statements. For an `IF` body, it checks references and values against the state before the condition, but it does not commit conditional reservations, assignments, or cancellations to the static symbol table. The interpreter enforces those conditional effects and conflicts when the branch actually runs.

### Intermediate representation

`ir.py` defines immutable instructions with an opcode, operands, and source position. The instruction set is intentionally readable:

- `CREATE_EVENT`
- `RESERVE_RESOURCE`
- `ASSIGN_ITEM`
- `CANCEL_EVENT`
- `JUMP_IF_FALSE`
- `LABEL`

Conditional compilation emits a `JUMP_IF_FALSE` targeting a generated label, followed by the body instructions and the label. The CLI numbers instructions so intermediate results can be demonstrated clearly.

### Interpreter

`interpreter.py` executes the instruction list in order. `RuntimeState` contains events, active reservations, assignments, the most recent capacity, and an execution log. Conditional jumps alter the instruction pointer. Runtime checks protect the engine even if an instruction sequence is constructed without semantic analysis.

The final formatter prints each event with its status, date, times, reservations, and assigned items, followed by a concise execution log. Output ordering follows source declaration order so demonstrations and tests are deterministic.

## Command-Line Interface

The existing entry command remains:

```bash
python3 run.py SOURCE_FILE
```

The CLI adds `--stage` with these values:

- `tokens`: print only lexical tokens.
- `ast`: tokenize, parse, and print the AST.
- `ir`: tokenize, parse, validate, and print intermediate instructions.
- `run`: run the complete pipeline and print final runtime state.
- `all`: print tokens, AST, IR, and runtime state. This is the default.

Examples:

```bash
python3 run.py examples/valid.cflow
python3 run.py examples/valid.cflow --stage ast
python3 run.py examples/valid.cflow --stage ir
python3 run.py examples/valid.cflow --stage run
python3 run.py examples/invalid.cflow
```

A successful requested stage exits with status `0`. Any compiler or runtime diagnostic exits with status `1`. File/argument errors continue to use `argparse` behavior and exit with status `2`.

## Error Handling

Diagnostics are stage-specific immutable records with a message, line, and column:

- `LexicalError`
- `SyntaxDiagnostic`
- `SemanticDiagnostic`
- `RuntimeDiagnostic`

The CLI labels each group, prints all safely recoverable errors from that stage, and stops before the next unsafe stage. Diagnostics use one-based positions and actionable wording, such as `Expected event name after EVENT` or `Resource 'Auditorium_A' conflicts with event 'TechFest'`.

The parser synchronizes at semicolons. Semantic analysis accumulates independent errors where continuing cannot corrupt its internal state. The interpreter reports the first runtime failure because subsequent state may depend on the failed instruction.

## Testing

The project continues to use `unittest` and real compiler objects rather than mocks.

Test groups cover:

- Existing lexical behavior and lexical regressions.
- Every grammar production and AST node shape.
- Keyword matching, missing tokens, unexpected tokens, and syntax recovery.
- Symbol insertion, lookup, duplicate detection, and state transitions.
- Every semantic validation rule, including boundary-touching versus overlapping times.
- Each intermediate instruction and conditional label generation.
- Interpreter state changes, true and false branches, cancellation, released resources, and defensive runtime errors.
- CLI stage selection, formatted output, and exit codes.
- End-to-end valid, lexically invalid, syntactically invalid, semantically invalid, and conflict demonstration files.

Every production behavior is developed test-first. The full suite is run after each component and before completion.

## Demonstration Artifacts

The repository will contain:

- `examples/valid.cflow`: a complete successful execution.
- `examples/invalid.cflow`: lexical-error demonstration.
- `examples/syntax_errors.cflow`: parser-error and recovery demonstration.
- `examples/semantic_errors.cflow`: declaration and validation errors.
- `examples/resource_conflict.cflow`: overlap/conflict detection.
- An expanded `README.md` with the grammar, architecture, module-wise explanation, commands, and expected stage output.
- `PHASE2_PROGRESS.md` mapping implemented components and tests to the Phase 2 rubric.

## Success Criteria

Phase 2 is complete when:

1. A valid example visibly passes through tokens, AST, semantic analysis, IR, and execution.
2. Final runtime output accurately reflects event creation, reservation, assignment, conditional execution, and cancellation.
3. Invalid examples produce correctly categorized diagnostics with source positions and non-zero exit codes.
4. Resource conflicts and other semantic mistakes are rejected before unsafe execution.
5. All automated tests pass on Python 3.10 or newer using only the standard library.
6. The README and progress report are sufficient to run and explain each module during a functional demonstration or viva.
