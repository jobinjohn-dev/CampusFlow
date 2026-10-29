# Try CampusFlow Phase 3

This short guide shows how to create a CampusFlow file, save it, and run it.

## What you need

- Python 3.10 or newer
- A text editor, such as Visual Studio Code
- A terminal

You do not need to install any Python packages.

## 1. Create a CampusFlow file with Nano

Open a terminal in the `phase3` folder. Move into the `examples` folder:

```bash
cd examples
```

Create an empty CampusFlow file:

```bash
touch my_techfest.cflow
```

Open the file in Nano:

```bash
nano my_techfest.cflow
```

You can also create and open the file with one command. Nano creates the file
when you save it:

```bash
nano my_techfest.cflow
```

When Nano opens, copy and paste this code into it:

```text
EVENT TechFest ON 2026-11-20 AT 09:00 TO 12:00;
RESERVE MainHall FOR TechFest CAPACITY 200;
ASSIGN Projector TO TechFest;
IF capacity >= 100 THEN ASSIGN Microphone TO TechFest;
```

### Save and close the file in Nano

1. Press `Ctrl+O` to save. Nano calls this **Write Out**.
2. Nano shows the file name at the bottom. Press `Enter` to keep the name.
3. Press `Ctrl+X` to close Nano and return to the terminal.

The `^` symbol in Nano means `Ctrl`. For example, `^O` means press `Ctrl+O`.

The file name must end with `.cflow`, not `.txt`.

## 2. Run the file

You are now inside the `examples` folder. Return to the `phase3` folder:

```bash
cd ..
```

On macOS or Linux, run:

```bash
python3 run.py examples/my_techfest.cflow
```

On Windows PowerShell, run:

```powershell
py run.py examples\my_techfest.cflow
```

The program will check the code, optimize it, and run it. The output will show
the event, the hall reservation, and the assigned items.

## 3. Show only the final result

The normal command shows every compiler step. For shorter output, use:

macOS or Linux:

```bash
python3 run.py examples/my_techfest.cflow --stage run
```

Windows PowerShell:

```powershell
py run.py examples\my_techfest.cflow --stage run
```

The final result should contain:

```text
FINAL RUNTIME STATE
-------------------
TechFest [ACTIVE] 2026-11-20 09:00-12:00
  RESERVATION MainHall capacity=200
  ASSIGNMENT Projector
  ASSIGNMENT Microphone
```

`Microphone` is assigned because the latest reservation has a capacity of
`200`, and `200 >= 100` is true.

## What each line means

- `EVENT` creates an event with a date, start time, and end time.
- `RESERVE` books a place for the event and sets its capacity.
- `ASSIGN` adds an item to the event.
- `IF capacity >= 100 THEN ...` runs the action only when the latest successful
  reservation has a capacity of at least 100.
- Every statement ends with a semicolon (`;`).
- Dates use `YYYY-MM-DD`.
- Times use the 24-hour `HH:MM` format.

## Try changing the code

Change `CAPACITY 200` to `CAPACITY 50`, save the file, and run it again.
`Microphone` will not be assigned because `50 >= 100` is false.

If there is a mistake, CampusFlow prints an error with a line number and a
column number. Use that location to find and fix the problem, save the file,
and run the command again.
