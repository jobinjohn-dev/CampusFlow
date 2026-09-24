# CampusFlow Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-demonstrable CampusFlow compiler pipeline that parses, validates, lowers, and executes the five Phase 2 statement forms.

**Architecture:** Preserve the current lexer as the front end, then pass immutable records through a recursive-descent parser, AST, semantic analyzer and symbol table, readable linear IR, and an in-memory interpreter. A pipeline coordinator and staged CLI expose every compiler artifact while stopping safely at the first failing stage.

**Tech Stack:** Python 3.10+, standard library only (`argparse`, `dataclasses`, `datetime`, `pathlib`, `unittest`)

**Spec:** `docs/superpowers/specs/2026-09-24-campusflow-phase-2-design.md`

## Global Constraints

- Support Python 3.10 or newer.
- Use only the Python standard library.
- Keep execution entirely in memory with no calendar, network, database, or filesystem writes beyond reading the source file.
- Treat keywords case-insensitively and identifiers case-sensitively while preserving original lexemes and one-based source positions.
- Preserve the entry command `python3 run.py SOURCE_FILE`; add `--stage tokens|ast|ir|run|all`, defaulting to `all`.
- Return exit code `0` for a successful requested stage, `1` for compiler/runtime diagnostics, and retain `argparse` exit code `2` for argument or file errors.
- Develop every production behavior test-first and run the complete suite after each task.

## Review Focus

- A statement missing its final semicolon at EOF must produce one syntax diagnostic and must not hang; Task 2 adds this parser regression test.
- A false conditional branch must not reserve, assign, cancel, or change `capacity`; Task 5 adds an interpreter state test.
- Cancelling an event must release its resources so a later overlapping event can reuse them; Tasks 3 and 5 add semantic and runtime tests.
- Events that touch at an endpoint, such as `10:00 TO 11:00` and `11:00 TO 12:00`, must not conflict; Task 3 adds a boundary test.
- `--stage ast` with malformed syntax must print syntax diagnostics, omit IR/runtime sections, and exit `1`; Task 6 adds a CLI subprocess test.

---

### Task 1: Immutable AST and tree formatting

**Files:**
- Create: `campusflow_phase1/campusflow/ast_nodes.py`
- Create: `campusflow_phase1/tests/test_ast_nodes.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`

**Interfaces:**
- Consumes: no new Phase 2 interfaces; uses only `dataclasses` and `typing`.
- Produces: `Program`, `EventStatement`, `ReserveStatement`, `AssignStatement`, `CancelStatement`, `IfStatement`, `CapacityExpression`, `NumberLiteral`, `ComparisonExpression`, `Statement`, `ConditionalStatement`, and `format_ast(program: Program) -> str`.
- All concrete nodes are frozen dataclasses. Every statement and expression has integer `line` and `column` fields. Date/time values and identifier spellings remain strings; numeric literals are integers.

- [ ] **Step 1: Write the failing AST tests**

Create `tests/test_ast_nodes.py` with concrete construction, immutability, and formatting assertions:

```python
import unittest
from dataclasses import FrozenInstanceError

from campusflow.ast_nodes import (
    CapacityExpression,
    ComparisonExpression,
    EventStatement,
    IfStatement,
    NumberLiteral,
    Program,
    ReserveStatement,
    format_ast,
)


class AstNodeTests(unittest.TestCase):
    def test_formats_nested_program_deterministically(self):
        program = Program((
            EventStatement("TechFest", "2026-10-15", "10:00", "12:00", 1, 1),
            IfStatement(
                ComparisonExpression(
                    CapacityExpression(2, 4), ">=", NumberLiteral(100, 2, 16), 2, 4
                ),
                ReserveStatement("Hall_A", "TechFest", 120, 2, 25),
                2,
                1,
            ),
        ))

        self.assertEqual(
            format_ast(program),
            "\n".join([
                "Program",
                "  Event TechFest date=2026-10-15 start=10:00 end=12:00 @1:1",
                "  If @2:1",
                "    Compare >= @2:4",
                "      Capacity @2:4",
                "      Number 100 @2:16",
                "    Then",
                "      Reserve Hall_A for=TechFest capacity=120 @2:25",
            ]),
        )

    def test_nodes_are_immutable(self):
        event = EventStatement("TechFest", "2026-10-15", "10:00", "12:00", 1, 1)
        with self.assertRaises(FrozenInstanceError):
            event.name = "Changed"


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_ast_nodes -v`

Expected: import failure for `campusflow.ast_nodes` because the module does not exist.

- [ ] **Step 3: Implement the AST records and formatter**

Create `ast_nodes.py` with the exact field order used above and union aliases:

```python
@dataclass(frozen=True)
class Program:
    statements: tuple["Statement", ...]

@dataclass(frozen=True)
class EventStatement:
    name: str
    date: str
    start_time: str
    end_time: str
    line: int
    column: int
```

Define the remaining nodes using the same positional convention: payload fields first, then `line`, `column`. Define `ConditionalStatement = ReserveStatement | AssignStatement | CancelStatement` and `Statement = EventStatement | ReserveStatement | AssignStatement | CancelStatement | IfStatement`. Implement `format_ast()` as a small recursive visitor whose output exactly matches the test. Export the public nodes and formatter from `campusflow/__init__.py` without removing the Phase 1 exports.

- [ ] **Step 4: Run the AST tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_ast_nodes -v`

Expected: 2 tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all old and new tests pass.

- [ ] **Step 5: Commit Task 1**

```bash
git add campusflow_phase1/campusflow/ast_nodes.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_ast_nodes.py
git commit -m "feat: add CampusFlow abstract syntax tree"
```

---

### Task 2: Recursive-descent parser and syntax recovery

**Files:**
- Create: `campusflow_phase1/campusflow/parser.py`
- Create: `campusflow_phase1/tests/test_parser.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`

**Interfaces:**
- Consumes: `tuple[Token, ...]` from `Lexer(source).scan().tokens` and all Task 1 AST classes.
- Produces: frozen `SyntaxDiagnostic(message: str, line: int, column: int)`, frozen `ParseResult(program: Program, errors: tuple[SyntaxDiagnostic, ...])`, and `Parser(tokens: tuple[Token, ...]).parse() -> ParseResult`.
- Parser keyword matching uses `token.kind == "KEYWORD" and token.lexeme.upper() == expected`; it never accepts the wrong keyword merely because the token kind is `KEYWORD`.

- [ ] **Step 1: Write failing tests for every statement and keyword matching**

Create `tests/test_parser.py` with a helper that lexes before parsing:

```python
import unittest

from campusflow.ast_nodes import (
    AssignStatement,
    CancelStatement,
    EventStatement,
    IfStatement,
    ReserveStatement,
)
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def parse(source):
    scan = Lexer(source).scan()
    assert not scan.errors
    return Parser(scan.tokens).parse()


class ParserTests(unittest.TestCase):
    def test_parses_all_statement_forms(self):
        result = parse("\n".join([
            "EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;",
            "RESERVE Auditorium_A FOR TechFest CAPACITY 150;",
            "ASSIGN Projector TO TechFest;",
            "IF capacity >= 100 THEN RESERVE Hall_A FOR TechFest CAPACITY 120;",
            "CANCEL TechFest;",
        ]))

        self.assertEqual(result.errors, ())
        self.assertEqual(
            [type(statement) for statement in result.program.statements],
            [EventStatement, ReserveStatement, AssignStatement, IfStatement, CancelStatement],
        )
        conditional = result.program.statements[3]
        self.assertEqual(conditional.condition.operator, ">=")
        self.assertEqual(conditional.condition.right.value, 100)

    def test_keywords_are_case_insensitive(self):
        result = parse("event MixedCase on 2026-12-01 at 09:05 to 10:00;")
        self.assertEqual(result.errors, ())
        self.assertEqual(result.program.statements[0].name, "MixedCase")

    def test_wrong_keyword_reports_position(self):
        result = parse("EVENT TechFest FOR 2026-10-15 AT 10:00 TO 12:00;")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Expected ON", result.errors[0].message)
        self.assertEqual((result.errors[0].line, result.errors[0].column), (1, 16))
```

- [ ] **Step 2: Run the focused parser tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_parser -v`

Expected: import failure for `campusflow.parser`.

- [ ] **Step 3: Implement the parser core and statement productions**

Implement `Parser` with `_current()`, `_at_end()`, `_advance()`, `_check_kind()`, `_match_keyword()`, `_consume_kind()`, `_consume_keyword()`, and a private `_ParseFailure` exception that carries one `SyntaxDiagnostic`. `parse()` repeatedly dispatches on the current keyword, appends complete statements only, catches `_ParseFailure`, records its diagnostic, and calls `_synchronize()`.

Implement the five productions exactly as specified. Convert `NUMBER` lexemes with `int()`. Reject `EVENT` and nested `IF` after `THEN` by expecting only `RESERVE`, `ASSIGN`, or `CANCEL`. Use the first keyword's position for a statement node and the operand token's position for literal/expression nodes.

- [ ] **Step 4: Add failing recovery and EOF-semicolon tests**

Append these tests before changing recovery code:

```python
    def test_recovers_at_semicolon_and_parses_later_statement(self):
        result = parse("EVENT Broken ON 2026-10-15 AT ; CANCEL Missing;")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.program.statements), 1)
        self.assertIsInstance(result.program.statements[0], CancelStatement)

    def test_missing_semicolon_at_eof_reports_once_without_hanging(self):
        result = parse("CANCEL OldMeet")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Expected ';'", result.errors[0].message)
        self.assertEqual(result.program.statements, ())

    def test_if_rejects_nested_event_declaration(self):
        result = parse(
            "IF capacity >= 100 THEN EVENT Extra ON 2026-10-15 AT 13:00 TO 14:00;"
        )
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Expected RESERVE, ASSIGN, or CANCEL after THEN", result.errors[0].message)
```

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_parser.ParserTests.test_recovers_at_semicolon_and_parses_later_statement tests.test_parser.ParserTests.test_missing_semicolon_at_eof_reports_once_without_hanging tests.test_parser.ParserTests.test_if_rejects_nested_event_declaration -v`

Expected: at least the recovery test fails because `_synchronize()` has not been completed.

- [ ] **Step 5: Implement synchronization and finish parser behavior**

Implement `_synchronize()` so it always advances unless already at EOF, stops immediately after consuming `SEMICOLON`, and never reuses a token from the malformed statement. If the failure occurs at EOF, return without advancing. Ensure the main parse loop either appends a statement or changes `self.index` during every iteration.

- [ ] **Step 6: Run parser tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_parser -v`

Expected: all parser tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 7: Commit Task 2**

```bash
git add campusflow_phase1/campusflow/parser.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_parser.py
git commit -m "feat: parse CampusFlow statements into AST"
```

---

### Task 3: Symbol table and semantic analysis

**Files:**
- Create: `campusflow_phase1/campusflow/symbols.py`
- Create: `campusflow_phase1/campusflow/semantic.py`
- Create: `campusflow_phase1/tests/test_symbols.py`
- Create: `campusflow_phase1/tests/test_semantic.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`

**Interfaces:**
- Consumes: a parsed `Program` from Task 2.
- Produces from `symbols.py`: mutable `EventSymbol`, frozen `ReservationSymbol`, frozen `AssignmentSymbol`, `SymbolTable`, and `intervals_overlap(left_date: str, left_start: str, left_end: str, right_date: str, right_start: str, right_end: str) -> bool`.
- `SymbolTable` exposes `events: dict[str, EventSymbol]`, `reservations: list[ReservationSymbol]`, `assignments: list[AssignmentSymbol]`, `lookup_event(name)`, `add_event(symbol)`, `add_reservation(symbol)`, `add_assignment(symbol)`, and `cancel_event(name)`.
- Produces from `semantic.py`: frozen `SemanticDiagnostic(message, line, column)`, frozen `SemanticResult(symbols: SymbolTable, errors: tuple[SemanticDiagnostic, ...])`, and `SemanticAnalyzer().analyze(program: Program) -> SemanticResult`.

- [ ] **Step 1: Write failing symbol-table and overlap tests**

Create `tests/test_symbols.py`:

```python
import unittest

from campusflow.symbols import EventSymbol, SymbolTable, intervals_overlap


class SymbolTableTests(unittest.TestCase):
    def test_inserts_looks_up_and_cancels_event(self):
        table = SymbolTable()
        event = EventSymbol("TechFest", "2026-10-15", "10:00", "12:00")
        table.add_event(event)
        self.assertIs(table.lookup_event("TechFest"), event)
        table.cancel_event("TechFest")
        self.assertTrue(event.cancelled)

    def test_overlap_excludes_adjacent_intervals_and_other_dates(self):
        self.assertTrue(intervals_overlap(
            "2026-10-15", "10:00", "12:00", "2026-10-15", "11:00", "13:00"
        ))
        self.assertFalse(intervals_overlap(
            "2026-10-15", "10:00", "11:00", "2026-10-15", "11:00", "12:00"
        ))
        self.assertFalse(intervals_overlap(
            "2026-10-15", "10:00", "12:00", "2026-10-16", "10:30", "11:30"
        ))
```

- [ ] **Step 2: Run symbol tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_symbols -v`

Expected: import failure for `campusflow.symbols`.

- [ ] **Step 3: Implement symbol records, lookup, cancellation, and overlap**

Use `datetime.strptime(value, "%H:%M").time()` inside `intervals_overlap`. Return false for different dates; otherwise use half-open comparison `left_start < right_end and right_start < left_end`. `cancel_event()` marks the event cancelled and removes its reservation and assignment records so later statements can reuse those names.

- [ ] **Step 4: Run symbol tests and verify GREEN**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_symbols -v`

Expected: all symbol tests pass.

- [ ] **Step 5: Write failing semantic tests for declarations, references, values, and conflicts**

Create `tests/test_semantic.py` with a parse helper and these concrete cases:

```python
import unittest

from campusflow.lexer import Lexer
from campusflow.parser import Parser
from campusflow.semantic import SemanticAnalyzer


def analyze(source):
    scan = Lexer(source).scan()
    assert not scan.errors
    parsed = Parser(scan.tokens).parse()
    assert not parsed.errors
    return SemanticAnalyzer().analyze(parsed.program)


class SemanticTests(unittest.TestCase):
    def test_builds_symbols_for_valid_program(self):
        result = analyze("\n".join([
            "EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;",
            "RESERVE Auditorium_A FOR TechFest CAPACITY 150;",
            "ASSIGN Projector TO TechFest;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertIn("TechFest", result.symbols.events)
        self.assertEqual(result.symbols.reservations[0].capacity, 150)

    def test_reports_duplicate_event_invalid_time_and_nonpositive_capacity(self):
        result = analyze("\n".join([
            "EVENT BadTime ON 2026-10-15 AT 12:00 TO 10:00;",
            "EVENT Dup ON 2026-10-15 AT 13:00 TO 14:00;",
            "EVENT Dup ON 2026-10-16 AT 13:00 TO 14:00;",
            "RESERVE Hall FOR Dup CAPACITY 0;",
        ]))
        messages = [error.message for error in result.errors]
        self.assertTrue(any("end time" in message for message in messages))
        self.assertTrue(any("Duplicate event 'Dup'" in message for message in messages))
        self.assertTrue(any("Capacity must be greater than zero" in message for message in messages))

    def test_reports_undeclared_cancelled_duplicate_and_capacity_use(self):
        result = analyze("\n".join([
            "ASSIGN Projector TO Missing;",
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "ASSIGN Projector TO Demo;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
            "RESERVE Hall FOR Demo CAPACITY 10;",
            "IF capacity >= 5 THEN CANCEL Demo;",
        ]))
        messages = [error.message for error in result.errors]
        self.assertTrue(any("Undeclared event 'Missing'" in message for message in messages))
        self.assertTrue(any("already assigned" in message for message in messages))
        self.assertTrue(any("cancelled event 'Demo'" in message for message in messages))
        self.assertTrue(any("capacity is not available" in message for message in messages))

    def test_detects_overlap_but_allows_boundary_and_reuse_after_cancel(self):
        result = analyze("\n".join([
            "EVENT First ON 2026-10-15 AT 10:00 TO 11:00;",
            "EVENT Adjacent ON 2026-10-15 AT 11:00 TO 12:00;",
            "EVENT Overlap ON 2026-10-15 AT 10:15 TO 10:45;",
            "RESERVE Hall FOR First CAPACITY 100;",
            "RESERVE Hall FOR Adjacent CAPACITY 100;",
            "RESERVE Hall FOR Overlap CAPACITY 100;",
            "CANCEL First;",
            "RESERVE Hall FOR Overlap CAPACITY 100;",
        ]))
        conflicts = [error for error in result.errors if "conflicts" in error.message]
        self.assertEqual(len(conflicts), 1)

    def test_conditional_body_is_validated_without_committing_effects(self):
        result = analyze("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 50;",
            "IF capacity >= 100 THEN ASSIGN Projector TO Demo;",
            "ASSIGN Projector TO Demo;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual(len(result.symbols.assignments), 1)
```

- [ ] **Step 6: Run semantic tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_semantic -v`

Expected: import failure for `campusflow.semantic`.

- [ ] **Step 7: Implement source-ordered semantic analysis**

Implement one visitor method per AST statement. Add an error helper that records the statement's position. Only mutate the symbol table after a statement passes its local checks. Set `capacity_defined = True` after a successful top-level reservation. For `IfStatement`, require `capacity_defined`, validate its body against current symbols with `commit=False`, and do not change symbols or `capacity_defined` from the conditional body. Use active event intervals for reservation and assignment conflicts. Check duplicate names before overlap conflicts so each bad statement yields the most actionable error.

- [ ] **Step 8: Run semantic tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_symbols tests.test_semantic -v`

Expected: all symbol and semantic tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 9: Commit Task 3**

```bash
git add campusflow_phase1/campusflow/symbols.py campusflow_phase1/campusflow/semantic.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_symbols.py campusflow_phase1/tests/test_semantic.py
git commit -m "feat: add CampusFlow semantic analysis"
```

---

### Task 4: Intermediate representation and conditional lowering

**Files:**
- Create: `campusflow_phase1/campusflow/ir.py`
- Create: `campusflow_phase1/tests/test_ir.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`

**Interfaces:**
- Consumes: a semantically valid `Program` from Task 1/3.
- Produces: frozen `Instruction(opcode: str, operands: tuple[object, ...], line: int, column: int)`, frozen `IRProgram(instructions: tuple[Instruction, ...])`, `IRGenerator().generate(program: Program) -> IRProgram`, and `format_ir(program: IRProgram) -> str`.
- Opcodes and operands are exact: `CREATE_EVENT(name, date, start, end)`, `RESERVE_RESOURCE(resource, event, capacity)`, `ASSIGN_ITEM(item, event)`, `CANCEL_EVENT(event)`, `JUMP_IF_FALSE(operator, right_value, label)`, and `LABEL(label)`.

- [ ] **Step 1: Write failing straight-line and conditional IR tests**

Create `tests/test_ir.py`:

```python
import unittest

from campusflow.ir import IRGenerator, format_ir
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def generate(source):
    parsed = Parser(Lexer(source).scan().tokens).parse()
    assert not parsed.errors
    return IRGenerator().generate(parsed.program)


class IrTests(unittest.TestCase):
    def test_lowers_straight_line_statements(self):
        program = generate("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Hall FOR Demo CAPACITY 50;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
        ]))
        self.assertEqual(
            [instruction.opcode for instruction in program.instructions],
            ["CREATE_EVENT", "RESERVE_RESOURCE", "ASSIGN_ITEM", "CANCEL_EVENT"],
        )
        self.assertEqual(program.instructions[1].operands, ("Hall", "Demo", 50))

    def test_lowers_if_to_jump_body_and_label(self):
        program = generate(
            "IF capacity >= 100 THEN RESERVE Hall FOR Demo CAPACITY 120;"
        )
        self.assertEqual(
            [instruction.opcode for instruction in program.instructions],
            ["JUMP_IF_FALSE", "RESERVE_RESOURCE", "LABEL"],
        )
        jump, _, label = program.instructions
        self.assertEqual(jump.operands[:2], (">=", 100))
        self.assertEqual(jump.operands[2], label.operands[0])

    def test_format_numbers_instructions_and_source_positions(self):
        formatted = format_ir(generate("CANCEL Demo;"))
        self.assertEqual(formatted, "0000  CANCEL_EVENT 'Demo'  @1:1")
```

- [ ] **Step 2: Run IR tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_ir -v`

Expected: import failure for `campusflow.ir`.

- [ ] **Step 3: Implement IR records, generator, and formatter**

Generate monotonically increasing labels named `if_end_1`, `if_end_2`, and so on. Lower a conditional into a jump, its body instruction, and its matching label. Preserve the statement position on ordinary instructions, the condition position on the jump, and the `IfStatement` position on the label. Format operands with `repr()` and number instructions from zero with four digits.

- [ ] **Step 4: Run IR tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_ir -v`

Expected: all IR tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 5: Commit Task 4**

```bash
git add campusflow_phase1/campusflow/ir.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_ir.py
git commit -m "feat: generate CampusFlow intermediate code"
```

---

### Task 5: In-memory interpreter and runtime diagnostics

**Files:**
- Create: `campusflow_phase1/campusflow/interpreter.py`
- Create: `campusflow_phase1/tests/test_interpreter.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`

**Interfaces:**
- Consumes: `IRProgram` and `Instruction` from Task 4 plus `intervals_overlap` from Task 3.
- Produces: mutable `RuntimeEvent`, frozen `RuntimeReservation`, frozen `RuntimeAssignment`, mutable `RuntimeState`, frozen `RuntimeDiagnostic(message, line, column)`, frozen `ExecutionResult(state: RuntimeState, errors: tuple[RuntimeDiagnostic, ...])`, `Interpreter().execute(program: IRProgram) -> ExecutionResult`, and `format_runtime(state: RuntimeState) -> str`.
- `RuntimeState` fields are `events: dict[str, RuntimeEvent]`, `reservations: list[RuntimeReservation]`, `assignments: list[RuntimeAssignment]`, `last_capacity: int | None`, and `execution_log: list[str]`.

- [ ] **Step 1: Write failing successful-execution and branch tests**

Create `tests/test_interpreter.py` with a helper that parses and generates IR:

```python
import unittest

from campusflow.interpreter import Interpreter, format_runtime
from campusflow.ir import IRGenerator
from campusflow.lexer import Lexer
from campusflow.parser import Parser


def execute(source):
    parsed = Parser(Lexer(source).scan().tokens).parse()
    assert not parsed.errors
    return Interpreter().execute(IRGenerator().generate(parsed.program))


class InterpreterTests(unittest.TestCase):
    def test_executes_event_reservation_assignment_and_cancel(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Hall FOR Demo CAPACITY 50;",
            "ASSIGN Projector TO Demo;",
            "CANCEL Demo;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertTrue(result.state.events["Demo"].cancelled)
        self.assertEqual(result.state.reservations, [])
        self.assertEqual(result.state.assignments, [])
        self.assertEqual(result.state.last_capacity, 50)

    def test_true_condition_executes_body(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 150;",
            "IF capacity >= 100 THEN ASSIGN Projector TO Demo;",
        ]))
        self.assertEqual([item.item for item in result.state.assignments], ["Projector"])

    def test_false_condition_skips_body_without_mutating_state(self):
        result = execute("\n".join([
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
            "RESERVE Seed FOR Demo CAPACITY 50;",
            "IF capacity >= 100 THEN RESERVE Hall FOR Demo CAPACITY 120;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual([item.resource for item in result.state.reservations], ["Seed"])
        self.assertEqual(result.state.last_capacity, 50)

    def test_cancel_releases_resource_for_later_overlapping_event(self):
        result = execute("\n".join([
            "EVENT First ON 2026-10-15 AT 10:00 TO 12:00;",
            "EVENT Second ON 2026-10-15 AT 11:00 TO 13:00;",
            "RESERVE Hall FOR First CAPACITY 100;",
            "CANCEL First;",
            "RESERVE Hall FOR Second CAPACITY 80;",
        ]))
        self.assertEqual(result.errors, ())
        self.assertEqual(result.state.reservations[0].event, "Second")
```

- [ ] **Step 2: Run interpreter tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_interpreter -v`

Expected: import failure for `campusflow.interpreter`.

- [ ] **Step 3: Implement the instruction loop, conditions, and state formatting**

Pre-index every `LABEL` before execution. Use an instruction pointer and comparison dispatch for all six operators. A false `JUMP_IF_FALSE` sets the pointer to the instruction after its label; a true comparison advances normally. Ordinary instructions validate event existence/activity, duplicate names, capacity, and overlaps before mutation. On the first failure, return the current state with one `RuntimeDiagnostic`.

Cancellation marks the event cancelled, removes its reservations and assignments, and retains `last_capacity` as historical expression state. `format_runtime()` emits a deterministic `FINAL RUNTIME STATE` section, one event in declaration order with `ACTIVE` or `CANCELLED`, nested reservations/assignments, then an `EXECUTION LOG` section.

- [ ] **Step 4: Add failing defensive-runtime tests**

Append tests that construct IR directly:

```python
    def test_unknown_opcode_is_runtime_error(self):
        from campusflow.ir import IRProgram, Instruction
        result = Interpreter().execute(IRProgram((Instruction("BROKEN", (), 4, 2),)))
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Unknown opcode 'BROKEN'", result.errors[0].message)
        self.assertEqual((result.errors[0].line, result.errors[0].column), (4, 2))

    def test_condition_without_capacity_is_runtime_error(self):
        from campusflow.ir import IRProgram, Instruction
        instructions = (
            Instruction("JUMP_IF_FALSE", (">=", 10, "end"), 1, 1),
            Instruction("LABEL", ("end",), 1, 1),
        )
        result = Interpreter().execute(IRProgram(instructions))
        self.assertIn("capacity is not available", result.errors[0].message)
```

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_interpreter.InterpreterTests.test_unknown_opcode_is_runtime_error tests.test_interpreter.InterpreterTests.test_condition_without_capacity_is_runtime_error -v`

Expected: both tests fail until defensive checks are added.

- [ ] **Step 5: Add defensive opcode, label, operand, and runtime-state checks**

Validate opcode names, required operand counts/types, label existence, and `last_capacity` availability. Convert unexpected `ValueError`, `TypeError`, or missing-label conditions into a `RuntimeDiagnostic` at the current instruction instead of exposing a traceback.

- [ ] **Step 6: Run interpreter tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_interpreter -v`

Expected: all interpreter tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 7: Commit Task 5**

```bash
git add campusflow_phase1/campusflow/interpreter.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_interpreter.py
git commit -m "feat: execute CampusFlow intermediate code"
```

---

### Task 6: Pipeline coordinator and staged CLI

**Files:**
- Create: `campusflow_phase1/campusflow/pipeline.py`
- Create: `campusflow_phase1/tests/test_pipeline.py`
- Modify: `campusflow_phase1/campusflow/cli.py`
- Modify: `campusflow_phase1/campusflow/__init__.py`
- Modify: `campusflow_phase1/tests/test_cli.py`

**Interfaces:**
- Consumes: all previous stages and their formatters.
- Produces: frozen `PipelineResult(scan: ScanResult, parse: ParseResult | None, semantic: SemanticResult | None, ir: IRProgram | None, execution: ExecutionResult | None)` and `compile_source(source: str, *, stage: str = "all") -> PipelineResult`.
- `compile_source` accepts exactly `tokens`, `ast`, `ir`, `run`, or `all`; invalid programmatic stage values raise `ValueError`.
- `cli.format_result(source_name: str, source: str, stage: str = "all") -> tuple[str, int]` remains directly testable. `main()` adds the argparse `--stage` choice.

- [ ] **Step 1: Write failing pipeline short-circuit tests**

Create `tests/test_pipeline.py`:

```python
import unittest

from campusflow.pipeline import compile_source


VALID = "\n".join([
    "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;",
    "RESERVE Hall FOR Demo CAPACITY 50;",
])


class PipelineTests(unittest.TestCase):
    def test_all_stage_returns_every_artifact(self):
        result = compile_source(VALID, stage="all")
        self.assertIsNotNone(result.parse)
        self.assertIsNotNone(result.semantic)
        self.assertIsNotNone(result.ir)
        self.assertIsNotNone(result.execution)

    def test_tokens_stage_stops_after_lexer(self):
        result = compile_source(VALID, stage="tokens")
        self.assertIsNone(result.parse)
        self.assertIsNone(result.semantic)
        self.assertIsNone(result.ir)
        self.assertIsNone(result.execution)

    def test_each_error_stage_prevents_later_artifacts(self):
        lexical = compile_source("RESERVE @Hall;", stage="all")
        syntax = compile_source("CANCEL ;", stage="all")
        semantic = compile_source("CANCEL Missing;", stage="all")
        self.assertIsNone(lexical.parse)
        self.assertIsNone(syntax.semantic)
        self.assertIsNone(semantic.ir)

    def test_invalid_programmatic_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown stage"):
            compile_source(VALID, stage="unknown")
```

- [ ] **Step 2: Run pipeline tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_pipeline -v`

Expected: import failure for `campusflow.pipeline`.

- [ ] **Step 3: Implement pipeline orchestration and safe short-circuiting**

Implement stages in dependency order. `ast` stops after a clean parse; `ir` stops after IR generation; `run` and `all` execute. A diagnostic at any stage returns a result with all later fields set to `None`. The `run` stage still retains earlier artifacts internally so the CLI can diagnose them, but its formatter prints only errors or runtime state.

- [ ] **Step 4: Replace Phase 1 CLI expectations with staged Phase 2 tests**

Modify `tests/test_cli.py` so its subprocess helper accepts extra arguments and add these assertions:

```python
    def test_default_all_prints_every_stage_and_runtime(self):
        completed = self.run_source(
            "EVENT Demo ON 2026-10-15 AT 10:00 TO 11:00;"
        )
        self.assertEqual(completed.returncode, 0)
        for heading in ("TOKENS", "ABSTRACT SYNTAX TREE", "INTERMEDIATE CODE", "FINAL RUNTIME STATE"):
            self.assertIn(heading, completed.stdout)

    def test_tokens_stage_preserves_phase_one_output(self):
        completed = self.run_source("CANCEL OldMeet;", "--stage", "tokens")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("KEYWORD", completed.stdout)
        self.assertIn("No lexical errors.", completed.stdout)
        self.assertNotIn("ABSTRACT SYNTAX TREE", completed.stdout)

    def test_ast_stage_reports_syntax_error_and_omits_later_sections(self):
        completed = self.run_source("CANCEL ;", "--stage", "ast")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("SYNTAX ERRORS", completed.stdout)
        self.assertNotIn("INTERMEDIATE CODE", completed.stdout)
        self.assertNotIn("FINAL RUNTIME STATE", completed.stdout)

    def test_run_stage_reports_semantic_error(self):
        completed = self.run_source("CANCEL Missing;", "--stage", "run")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("SEMANTIC ERRORS", completed.stdout)
        self.assertIn("Undeclared event 'Missing'", completed.stdout)
```

Update `run_source(self, source, *arguments)` to append `arguments` after the temporary source path.

- [ ] **Step 5: Run CLI tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_cli -v`

Expected: failures because `--stage` and Phase 2 output sections are not implemented.

- [ ] **Step 6: Implement CLI formatting and `--stage`**

Retain the existing token table in a `format_tokens()` helper. Add section helpers for diagnostics, AST, semantic success (`Semantic analysis: passed.` plus symbol counts), IR, and runtime. `format_result()` calls `compile_source()` once and prints only the sections requested by the stage: `all` prints all successful artifacts; `tokens`, `ast`, `ir`, and `run` print their named artifact plus any diagnostic needed to explain failure. Add `--stage` with argparse choices and default `all`.

- [ ] **Step 7: Run pipeline/CLI tests and full suite**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_pipeline tests.test_cli -v`

Expected: all pipeline and CLI tests pass.

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 8: Commit Task 6**

```bash
git add campusflow_phase1/campusflow/pipeline.py campusflow_phase1/campusflow/cli.py campusflow_phase1/campusflow/__init__.py campusflow_phase1/tests/test_pipeline.py campusflow_phase1/tests/test_cli.py
git commit -m "feat: expose staged CampusFlow compiler CLI"
```

---

### Task 7: Demonstration programs, end-to-end tests, and Phase 2 documentation

**Files:**
- Modify: `campusflow_phase1/examples/valid.cflow`
- Modify: `campusflow_phase1/examples/invalid.cflow`
- Create: `campusflow_phase1/examples/syntax_errors.cflow`
- Create: `campusflow_phase1/examples/semantic_errors.cflow`
- Create: `campusflow_phase1/examples/resource_conflict.cflow`
- Create: `campusflow_phase1/tests/test_examples.py`
- Modify: `campusflow_phase1/README.md`
- Create: `campusflow_phase1/PHASE2_PROGRESS.md`

**Interfaces:**
- Consumes: the completed CLI from Task 6.
- Produces: five runnable demonstration files, end-to-end regression coverage, user-facing commands/grammar/module descriptions, and a rubric-mapped progress report.

- [ ] **Step 1: Write failing end-to-end tests against the planned examples**

Create `tests/test_examples.py`:

```python
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run.py"
EXAMPLES = ROOT / "examples"


class ExampleTests(unittest.TestCase):
    def run_example(self, name, stage="all"):
        return subprocess.run(
            [sys.executable, str(RUNNER), str(EXAMPLES / name), "--stage", stage],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_example_executes_every_statement_form(self):
        completed = self.run_example("valid.cflow")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("FINAL RUNTIME STATE", completed.stdout)
        self.assertIn("TechFest", completed.stdout)
        self.assertIn("Workshop", completed.stdout)
        self.assertIn("OldMeet", completed.stdout)
        self.assertIn("CANCELLED", completed.stdout)
        self.assertIn("Seminar_Hall", completed.stdout)

    def test_each_invalid_example_fails_at_its_intended_stage(self):
        cases = {
            "invalid.cflow": "LEXICAL ERRORS",
            "syntax_errors.cflow": "SYNTAX ERRORS",
            "semantic_errors.cflow": "SEMANTIC ERRORS",
            "resource_conflict.cflow": "SEMANTIC ERRORS",
        }
        for filename, heading in cases.items():
            with self.subTest(filename=filename):
                completed = self.run_example(filename)
                self.assertEqual(completed.returncode, 1)
                self.assertIn(heading, completed.stdout)
```

- [ ] **Step 2: Run example tests and verify RED**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_examples -v`

Expected: missing-file failures and a semantic failure in the old `valid.cflow`, which references undeclared `Workshop` and `OldMeet`.

- [ ] **Step 3: Create the exact demonstration programs**

Use this successful `valid.cflow` sequence:

```text
# Complete CampusFlow Phase 2 demonstration
EVENT TechFest ON 2026-10-15 AT 10:00 TO 12:00;
EVENT Workshop ON 2026-10-15 AT 13:00 TO 15:00;
EVENT OldMeet ON 2026-10-16 AT 09:00 TO 10:00;
RESERVE Auditorium_A FOR TechFest CAPACITY 150;
ASSIGN Projector TO TechFest;
IF capacity >= 100 THEN RESERVE Seminar_Hall FOR Workshop CAPACITY 120;
CANCEL OldMeet;
```

Keep `invalid.cflow` focused on its existing invalid date, invalid time, illegal character, invalid operator, and unterminated string. Create `syntax_errors.cflow` with `EVENT MissingDate ON AT 10:00 TO 11:00;` and `CANCEL ;`. Create `semantic_errors.cflow` with a duplicate event, an undeclared event reference, zero capacity, and cancellation of a missing event. Create `resource_conflict.cflow` with two overlapping events both reserving `Auditorium_A`.

- [ ] **Step 4: Run example tests and verify GREEN**

Run: `cd campusflow_phase1 && python3 -m unittest tests.test_examples -v`

Expected: both end-to-end tests pass, including all subtests.

- [ ] **Step 5: Expand the README with executable Phase 2 guidance**

Replace the Phase 1-only framing with these sections: Overview, Requirements, Quick Start, CLI Stages, Language Grammar, Statement Semantics, Compiler Pipeline, Module Guide, Error Stages, Demonstration Files, Running Tests, Example Output, and Current Limitations. Include every command from the spec and explain that `capacity` refers to the most recent successful reservation. Include one abbreviated but literal output sample showing the AST heading, at least three IR instructions, semantic success, and final event state.

- [ ] **Step 6: Add the implementation-progress report**

Create `PHASE2_PROGRESS.md` with a table mapping the rubric components to modules, tests, and demonstration commands. Include Lexical Analysis, Syntax Analysis, AST, Semantic Analysis, Symbol Table, Intermediate Code, Interpreter, Error Handling, Test Cases, Intermediate Results, Module-wise Explanation, and Functional Demonstration. End with the exact full-suite and demo commands used for verification.

- [ ] **Step 7: Run documentation commands exactly as written**

Run:

```bash
cd campusflow_phase1
python3 run.py examples/valid.cflow
python3 run.py examples/valid.cflow --stage tokens
python3 run.py examples/valid.cflow --stage ast
python3 run.py examples/valid.cflow --stage ir
python3 run.py examples/valid.cflow --stage run
python3 run.py examples/invalid.cflow
python3 run.py examples/syntax_errors.cflow
python3 run.py examples/semantic_errors.cflow
python3 run.py examples/resource_conflict.cflow
```

Expected: the valid commands exit `0`; each invalid demonstration exits `1` with its documented diagnostic stage. Run invalid examples separately or append `; true` during batch verification so their expected non-zero exit does not skip later commands.

- [ ] **Step 8: Run the complete automated suite and static checks**

Run: `cd campusflow_phase1 && python3 -m unittest discover -s tests -v`

Expected: every test passes with an `OK` summary.

Run: `cd campusflow_phase1 && python3 -m compileall -q campusflow run.py`

Expected: exit code `0` and no output.

Run: `git diff --check`

Expected: exit code `0` and no whitespace errors.

- [ ] **Step 9: Commit Task 7**

```bash
git add campusflow_phase1/examples campusflow_phase1/tests/test_examples.py campusflow_phase1/README.md campusflow_phase1/PHASE2_PROGRESS.md
git commit -m "docs: add CampusFlow phase 2 demonstrations"
```

---

### Task 8: Final requirements audit and branch verification

**Files:**
- Review: `docs/superpowers/specs/2026-09-24-campusflow-phase-2-design.md`
- Review: all files changed by Tasks 1-7
- Modify only if verification exposes a tested defect or a documentation mismatch.

**Interfaces:**
- Consumes: the complete implementation and specification.
- Produces: fresh evidence that every success criterion is satisfied and a clean, reviewable branch.

- [ ] **Step 1: Map every specification success criterion to evidence**

Record in the implementation handoff:

1. The `valid.cflow` command and its tokens/AST/IR/runtime headings.
2. Final state lines proving creation, reservation, assignment, conditional execution, and cancellation.
3. Each invalid example command, diagnostic heading, and exit code.
4. The conflict example diagnostic proving execution was blocked.
5. The test count, Python version, and standard-library-only dependency status.
6. The README and `PHASE2_PROGRESS.md` paths.

- [ ] **Step 2: Run fresh final verification**

Run:

```bash
cd campusflow_phase1
python3 --version
python3 -m unittest discover -s tests -v
python3 -m compileall -q campusflow run.py
python3 run.py examples/valid.cflow --stage all
```

Expected: Python is at least 3.10, all tests pass, compileall exits `0`, and the valid example exits `0` with every compiler stage and final state.

- [ ] **Step 3: Verify expected failures and their exit codes**

Run each command separately and inspect `$?` immediately:

```bash
cd campusflow_phase1
python3 run.py examples/invalid.cflow --stage all
python3 run.py examples/syntax_errors.cflow --stage all
python3 run.py examples/semantic_errors.cflow --stage all
python3 run.py examples/resource_conflict.cflow --stage all
```

Expected: each command exits `1`; headings are respectively lexical, syntax, semantic, and semantic errors.

- [ ] **Step 4: Inspect repository scope and whitespace**

Run: `git status --short && git diff --check && git log --oneline -10`

Expected: no accidental cache/build artifacts are staged, no whitespace errors are reported, and the task commits appear in order.
