# How to Initialize a New KiCad Project

There's a script, `kicad_init_v2.py`, that sets up a new KiCad 10 project
from a shared seed/template. It handles renaming the project files and
generating a fresh sheet UUID, and it links to (or creates, if missing)
the shared symbol/footprint/3D-model libraries.

## Requirements

- The script: `kicad_init_v2.py`
- The seed archive: `kicad-template.tgz`, normally sitting in the same
  directory as the script

## Basic usage

From inside the directory where you keep your KiCad designs (e.g.
`repo/kicad/`):

```bash
python3 kicad_init_v2.py my_new_design
```

This creates `my_new_design.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, and
`.kicad_prl` in the current directory, and creates `sym-lib-table`,
`fp-lib-table`, and the `libraries/` folder if they don't already exist.

## Adding another design to the same directory

Run it again with a different name, in the same directory:

```bash
python3 kicad_init_v2.py another_design
```

The shared libraries are left untouched; only the new project's four
identity files are added.

## Options

```bash
python3 kicad_init_v2.py PROJECT_NAME [--target-dir DIR] [--seed-archive PATH]
```

- `--target-dir DIR` — initialize somewhere other than the current
  directory (created if it doesn't exist).
- `--seed-archive PATH` — use a seed archive other than the default
  `kicad-template.tgz` next to the script.

## If something goes wrong

- **"Project already appears to exist"** — a project with that name is
  already in the target directory. Pick a different name, or delete the
  existing files first if that was a mistake. Nothing is touched when
  this error fires.
- Any other error names the specific problem (missing archive, bad
  project name, unexpected archive contents) and stops before writing
  anything.
