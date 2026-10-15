#!/usr/bin/env python3
"""
init_kicad_project.py

Initialize a KiCad 10 project directory with project-specific symbol,
footprint, and 3D-model library linkages, creating those libraries if
they don't already exist.

Design goals:
  * No dependency on pcbnew (SWIG) or kicad-python (IPC). This just
    writes/edits the plain-text project files, so it keeps working
    unchanged after you upgrade to KiCad 11.
  * Reuses "seed" files you generate once from the real KiCad 10 GUI,
    instead of hand-guessing internal JSON/S-expression schemas. This
    is also how your grid spacing / other project settings ride along
    for free -- set them once in the seed project, done.

SETUP (one-time):
  1. In KiCad 10, File > New Project, create a throwaway project
     (e.g. "seed") somewhere. Set your preferred grid spacing, units,
     etc. Save it.
  2. Point SEED_PRO / SEED_SCH / SEED_PCB below at that project's
     .kicad_pro / .kicad_sch / .kicad_pcb files.
  3. In the Symbol Editor, File > New Library (KiCad format), save an
     empty library somewhere. Point SEED_SYM at that .kicad_sym file.
  4. Footprint libraries need no seed -- they're just folders.

Then run:
  python3 init_kicad_project.py MyProject /path/to/projects --lib-name MyProject
"""

import argparse
import shutil
from pathlib import Path

# ---- Point these at your one-time seed files -----------------------------
SEED_DIR = Path("~/kicad-seed").expanduser()
SEED_PRO = SEED_DIR / "seed.kicad_pro"
SEED_SCH = SEED_DIR / "seed.kicad_sch"
SEED_PCB = SEED_DIR / "seed.kicad_pcb"
SEED_SYM = SEED_DIR / "seed.kicad_sym"   # empty symbol library, KiCad format
# ---------------------------------------------------------------------------

SYM_LIB_TABLE_TMPL = """(sym_lib_table
  (version 7)
  (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/libraries/{name}.kicad_sym")(options "")(descr "Project symbols"))
)
"""

FP_LIB_TABLE_TMPL = """(fp_lib_table
  (version 7)
  (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/libraries/{name}.pretty")(options "")(descr "Project footprints"))
)
"""


def merge_lib_table(path: Path, new_entry_block: str, lib_name: str, header: str):
    """
    Create the lib table if missing, or append the new lib entry if the
    file exists but doesn't already reference this library name.
    """
    if not path.exists():
        path.write_text(new_entry_block)
        print(f"created {path}")
        return

    text = path.read_text()
    if f'(name "{lib_name}")' in text or f"(name {lib_name})" in text:
        print(f"{path} already references '{lib_name}', leaving as-is")
        return

    # crude but reliable: insert the new (lib ...) line before the final ')'
    entry_line = new_entry_block.strip().splitlines()[2]  # the "(lib ...)" line
    idx = text.rstrip().rfind(")")
    merged = text.rstrip()[:idx].rstrip() + "\n  " + entry_line + "\n)\n"
    path.write_text(merged)
    print(f"appended '{lib_name}' entry to existing {path}")


def init_project(project_name: str, dest_parent: Path, lib_name: str, make_edge_cuts: bool):
    project_dir = dest_parent / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    libraries_dir = project_dir / "libraries"
    libraries_dir.mkdir(exist_ok=True)
    (project_dir / "3dshapes").mkdir(exist_ok=True)

    # --- core project files, from your seed ---
    pro = project_dir / f"{project_name}.kicad_pro"
    sch = project_dir / f"{project_name}.kicad_sch"
    pcb = project_dir / f"{project_name}.kicad_pcb"

    if not pro.exists():
        shutil.copyfile(SEED_PRO, pro)
        print(f"created {pro} (from seed)")
    if not sch.exists():
        shutil.copyfile(SEED_SCH, sch)
        print(f"created {sch} (from seed)")
    if not pcb.exists():
        shutil.copyfile(SEED_PCB, pcb)
        print(f"created {pcb} (from seed)")

    # --- symbol library: create if missing, then link it ---
    sym_lib_path = libraries_dir / f"{lib_name}.kicad_sym"
    if not sym_lib_path.exists():
        shutil.copyfile(SEED_SYM, sym_lib_path)
        print(f"created empty symbol library {sym_lib_path} (from seed)")
    merge_lib_table(
        project_dir / "sym-lib-table",
        SYM_LIB_TABLE_TMPL.format(name=lib_name),
        lib_name,
        "sym_lib_table",
    )

    # --- footprint library: just a folder, create if missing, then link ---
    fp_lib_path = libraries_dir / f"{lib_name}.pretty"
    fp_lib_path.mkdir(exist_ok=True)
    merge_lib_table(
        project_dir / "fp-lib-table",
        FP_LIB_TABLE_TMPL.format(name=lib_name),
        lib_name,
        "fp_lib_table",
    )

    # --- 3D models: no lib table, just the folder. Reference it in
    # footprints as ${KIPRJMOD}/3dshapes/<file>.step ---
    print(f"3D model folder ready at {project_dir / '3dshapes'} "
          f"(reference as ${{KIPRJMOD}}/3dshapes/<file> in footprints)")

    if make_edge_cuts:
        add_edge_cuts(pcb, width_mm=100.0, height_mm=80.0)

    print(f"\nProject initialized at {project_dir}")


def add_edge_cuts(pcb_path: Path, width_mm: float, height_mm: float):
    """
    Append a simple rectangular Edge.Cuts outline to an existing
    (already-seeded) .kicad_pcb file, if one isn't already present.
    """
    text = pcb_path.read_text()
    if '"Edge.Cuts"' in text and "(gr_rect" in text:
        print("Edge.Cuts rectangle already present, skipping")
        return

    rect = (
        f'  (gr_rect (start 0 0) (end {width_mm} {height_mm}) '
        f'(stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts"))\n'
    )
    idx = text.rstrip().rfind(")")
    merged = text.rstrip()[:idx].rstrip() + "\n" + rect + ")\n"
    pcb_path.write_text(merged)
    print(f"added {width_mm}x{height_mm} mm Edge.Cuts rectangle to {pcb_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project_name")
    ap.add_argument("dest_parent", type=Path)
    ap.add_argument("--lib-name", default=None,
                     help="Base name for the project's symbol/footprint libs (default: project name)")
    ap.add_argument("--edge-cuts", action="store_true", help="Add a default rectangular board outline")
    args = ap.parse_args()

    init_project(
        args.project_name,
        args.dest_parent,
        args.lib_name or args.project_name,
        args.edge_cuts,
    )
