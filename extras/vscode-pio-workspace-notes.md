# VSCode + PlatformIO Workspace Notes

* ***project.code-workspace*** file notes

## The core problem

PlatformIO's VSCode extension activates by looking for a `platformio.ini` file
in the **explicit folder roots** listed in the workspace. It does not recurse
down from a parent directory. If you open the repo root alone and the PlatformIO
project is in a subdirectory, the PlatformIO toolbar icons will not appear.

## Example repo layout

```
~/project_name/                   <- repo root, contains .git/
├── .git/
├── extras/                       <- notes, reference docs
├── mech/                         <- FreeCAD files
├── elec/                         <- KiCad files
├── sketches/
│   ├── read_diodes/              <- active PlatformIO project
│   │   ├── platformio.ini
│   │   └── src/main.cpp
│   └── clear/                    <- "null" sketch for resetting the board
│       ├── platformio.ini
│       └── src/main.cpp
└── proj.code-workspace           <- VSCode workspace file (tracked by git)
```

## The workspace file (proj.code-workspace)

The workspace file is **tracked by git**. If PlatformIO stops showing its
toolbar icons, the first thing to check is whether the affected sketch
directory is listed as an explicit folder root in this file.

Every PlatformIO project (i.e. every directory containing a `platformio.ini`)
that you want to work on inside VSCode **must have its own entry** in the
`folders` list. The repo root entry alone is not enough.

When you add a new sketch under `sketches/`, add a corresponding entry:

```json
{
    "name": "my-new-sketch (firmware)",
    "path": "sketches/my-new-sketch"
}
```

## Correct way to open the project

Always open VSCode via the workspace file, not via a raw folder:

```bash
code ~/project_name/proj.code-workspace
```

Or double-click `proj.code-workspace` in the GNOME file manager.

Do **not** use `File → Open Folder` pointed at the repo root — that bypasses
the workspace file and PlatformIO will not activate.

## Uploading the "clear" sketch without opening it in VSCode

The `clear` sketch is used to reset the board. You do not need to open it
in VSCode. Upload it directly from the terminal:

```bash
pio run --target upload --project-dir ~/project_name/sketches/clear
```

Or use the desktop shell script shortcut if one has been set up.

## If PlatformIO toolbar icons are missing

1. Check that the affected sketch is listed as a folder root in
   `proj.code-workspace`.
2. Open `src/main.cpp` in the editor — PlatformIO activates lazily when a
   relevant source file is opened.
3. Wait a few seconds after opening for the extension to initialize.
4. As a sanity check, open the sketch folder directly:
   `File → Open Folder → ~/project_name/sketches/read_diodes`
   If icons appear, the problem is the workspace file, not the project.
5. Use the CLI as a fallback at any time:
   `pio run --target upload --project-dir ~/project_name/sketches/read_diodes`

## Serial monitor baud rate

Set in each project's `platformio.ini`:

```ini
monitor_speed = 115200
```

