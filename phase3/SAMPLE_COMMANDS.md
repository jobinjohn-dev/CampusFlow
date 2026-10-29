# CampusFlow Sample Commands

This file shows every syntax supported by CampusFlow Phase 3. You can copy the
examples into a `.cflow` file and run them.

## Quick rules

- End every statement with a semicolon (`;`).
- Write dates as `YYYY-MM-DD`.
- Write times in 24-hour `HH:MM` format.
- The end time must be later than the start time.
- Create an event before reserving, assigning, or cancelling it.
- Capacity must be a whole number greater than `0`.
- A line beginning with `#` is a comment.
- Keywords such as `EVENT` and `RESERVE` are not case-sensitive.
- Names are case-sensitive. `TechFest` and `techfest` are different names.

## Name syntax

Event, resource, and item names:

- May use letters, numbers, and underscores (`_`).
- Must start with a letter or underscore.
- Cannot contain spaces, hyphens, or quotation marks.
- Cannot be a CampusFlow keyword.

Valid names:

```text
TechFest
MainHall
Auditorium_A
Projector2
_BackupRoom
```

Invalid names:

```text
Tech Fest
Main-Hall
2ndProjector
"Guest Lecture"
```

## 1. Comment

Syntax:

```text
# Write a comment here
```

Anything after `#` on the same line is ignored.

Example:

```text
# Create the main event
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00; # This is also a comment
```

## 2. Create an event

Syntax:

```text
EVENT <event_name> ON <YYYY-MM-DD> AT <start_time> TO <end_time>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
```

Lowercase keywords also work:

```text
event Workshop on 2026-11-20 at 13:00 to 15:00;
```

Each event name must be unique. Events are single-day events and cannot cross
midnight.

## 3. Reserve a resource

Syntax:

```text
RESERVE <resource_name> FOR <event_name> CAPACITY <number>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
RESERVE MainHall FOR TechFest CAPACITY 200;
```

The event must already exist. A resource cannot be used by two events whose
times overlap.

## 4. Assign an item

Syntax:

```text
ASSIGN <item_name> TO <event_name>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
ASSIGN Projector TO TechFest;
```

The event must already exist. An item cannot be used by two events whose times
overlap.

## 5. Cancel an event

Syntax:

```text
CANCEL <event_name>;
```

Example:

```text
EVENT OldMeet ON 2026-11-21 AT 09:00 TO 10:00;
CANCEL OldMeet;
```

Cancelling an event releases its reservations and assignments. A cancelled
event cannot be used again.

## 6. Run an action only when a capacity condition is true

General syntax:

```text
IF capacity <operator> <number> THEN <action>;
```

You must make a successful reservation before using `IF capacity`. The
condition checks the capacity of the latest successful reservation.

Only these three actions are allowed after `THEN`:

### Conditional assignment

Syntax:

```text
IF capacity <operator> <number> THEN ASSIGN <item_name> TO <event_name>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
RESERVE MainHall FOR TechFest CAPACITY 200;
IF capacity >= 100 THEN ASSIGN Microphone TO TechFest;
```

### Conditional reservation

Syntax:

```text
IF capacity <operator> <number> THEN RESERVE <resource_name> FOR <event_name> CAPACITY <number>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
EVENT Workshop ON 2026-11-20 AT 13:00 TO 15:00;
RESERVE MainHall FOR TechFest CAPACITY 200;
IF capacity >= 100 THEN RESERVE Lab_A FOR Workshop CAPACITY 80;
```

### Conditional cancellation

Syntax:

```text
IF capacity <operator> <number> THEN CANCEL <event_name>;
```

Example:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
EVENT BackupEvent ON 2026-11-21 AT 09:00 TO 10:00;
RESERVE MainHall FOR TechFest CAPACITY 200;
IF capacity >= 150 THEN CANCEL BackupEvent;
```

An `IF` action cannot create an `EVENT`, contain another `IF`, or contain more
than one statement.

## All comparison operators

| Operator | Meaning | Example condition |
|---|---|---|
| `>` | Greater than | `capacity > 100` |
| `<` | Less than | `capacity < 300` |
| `>=` | Greater than or equal to | `capacity >= 200` |
| `<=` | Less than or equal to | `capacity <= 200` |
| `==` | Equal to | `capacity == 200` |
| `!=` | Not equal to | `capacity != 100` |

This runnable program uses all six operators:

```text
EVENT OperatorDemo ON 2026-11-22 AT 09:00 TO 11:00;
RESERVE DemoHall FOR OperatorDemo CAPACITY 200;

IF capacity > 100 THEN ASSIGN ItemGreater TO OperatorDemo;
IF capacity < 300 THEN ASSIGN ItemLess TO OperatorDemo;
IF capacity >= 200 THEN ASSIGN ItemGreaterEqual TO OperatorDemo;
IF capacity <= 200 THEN ASSIGN ItemLessEqual TO OperatorDemo;
IF capacity == 200 THEN ASSIGN ItemEqual TO OperatorDemo;
IF capacity != 100 THEN ASSIGN ItemNotEqual TO OperatorDemo;
```

All six conditions above are true because the latest reservation capacity is
`200`.

Do not write `=>` or `=<`. The correct operators are `>=` and `<=`.

## Complete sample program

This program uses every CampusFlow statement type:

```text
# Create events
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
EVENT Workshop ON 2026-11-20 AT 13:00 TO 15:00;
EVENT OldMeet ON 2026-11-21 AT 09:00 TO 10:00;

# Direct reservation and assignment
RESERVE MainHall FOR TechFest CAPACITY 200;
ASSIGN Projector TO TechFest;

# Conditional assignment
IF capacity >= 100 THEN ASSIGN Microphone TO TechFest;

# Conditional reservation
IF capacity == 200 THEN RESERVE Lab_A FOR Workshop CAPACITY 80;

# The latest successful reservation now has capacity 80
IF capacity >= 80 THEN ASSIGN Whiteboard TO Workshop;

# Direct cancellation
CANCEL OldMeet;
```

## Create a file with Nano

Open a terminal in the `phase3` folder, then run:

```bash
cd examples
touch my_program.cflow
nano my_program.cflow
```

Paste one of the sample programs into Nano. Then:

1. Press `Ctrl+O` to save.
2. Press `Enter` to keep the file name.
3. Press `Ctrl+X` to close Nano.
4. Return to the `phase3` folder:

```bash
cd ..
```

You can skip `touch` and use `nano my_program.cflow` directly. Nano creates
the file when you save it.

## Run commands

### Run all compiler stages

macOS or Linux:

```bash
python3 run.py examples/my_program.cflow
```

Windows PowerShell:

```powershell
py run.py examples\my_program.cflow
```

### Run one stage

```bash
python3 run.py examples/my_program.cflow --stage tokens
python3 run.py examples/my_program.cflow --stage ast
python3 run.py examples/my_program.cflow --stage ir
python3 run.py examples/my_program.cflow --stage optimized
python3 run.py examples/my_program.cflow --stage run
python3 run.py examples/my_program.cflow --stage all
```

The stages mean:

| Stage | What it shows |
|---|---|
| `tokens` | Words and symbols found by the lexer |
| `ast` | The parsed program structure |
| `ir` | Original intermediate code |
| `optimized` | Original and optimized intermediate code |
| `run` | Final runtime state and execution log |
| `all` | Every stage; this is the default |

On Windows, replace `python3` with `py` and `/` with `\` in the file path.

### Run a benchmark

```bash
python3 run.py examples/my_program.cflow --benchmark 100
```

The benchmark number must be greater than `0`.

### Show command help

```bash
python3 run.py --help
```

## Common mistakes

- Missing the semicolon at the end of a statement.
- Using a name with a space, such as `Main Hall`.
- Using an end time that is earlier than or equal to the start time.
- Using capacity `0` or a negative capacity.
- Reserving, assigning, or cancelling an event before creating it.
- Writing an `IF capacity` statement before a successful reservation.
- Writing `=` instead of `==` for an equality check.
- Writing `=>` instead of `>=`.
- Using `EVENT` or another `IF` after `THEN`.
- Trying to use a resource or item for events with overlapping times.
