#!/usr/bin/env python3
"""
kicad_init_v1.py

Initialize a new KiCad 10 project from a seed archive (kicad-template.tgz).

WHAT THIS DOES
---------------
The seed archive contains a fully-formed KiCad project ("kicad-template")
plus a shared library folder. This script:

  1. Extracts the four "identity" files (.kicad_pro, .kicad_sch, .kicad_pcb,
     .kicad_prl) to a scratch directory, renames them to the new project
     name, and rewrites two things inside them:
       - every occurrence of the seed's project-name token (e.g.
         "kicad-template") -> the new project name
       - every occurrence of the seed's root-sheet UUID -> a freshly
         generated UUID (unique per project)
     Only after this succeeds are the finished files moved into the real
     target directory. This means a crash or interrupted run never leaves
     half-renamed "kicad-template.*" files sitting in your project folder.

  2. Extracts the shared library files (sym-lib-table, fp-lib-table,
     libraries/) directly into the target directory, but SKIPS any of them
     that already exist there. This is what lets multiple sibling designs
     in the same directory share one set of libraries: the first design
     you initialize creates the libraries, every later sibling design just
     reuses them untouched.

WHAT THIS DOES NOT DO
----------------------
It does not check the CONTENTS of the identity files beyond simple text
substitution. It does not talk to KiCad or use pcbnew/kicad-python. It
never overwrites an existing project's .kicad_pro/.kicad_sch/.kicad_pcb.

USAGE
-----
    python3 kicad_init_v1.py NEW_PROJECT_NAME [--target-dir DIR] [--seed-archive PATH]

    NEW_PROJECT_NAME   Required. Must not already exist in the target
                        directory (as a .kicad_pro/.kicad_sch/.kicad_pcb).
    --target-dir        Directory to initialize into. Defaults to the
                        current working directory. Created if missing.
    --seed-archive      Path to the seed .tgz. Defaults to a file named
                        "kicad-template.tgz" sitting next to this script.

CHANGELOG
---------
v2: Fixed a bug where tar archives created with a leading "./" on every
    member name (e.g. via `tar czf archive.tgz .` from inside the seed
    directory) caused a KeyError on extraction. Member lookups now go
    through a normalized index built with pathlib, instead of comparing
    hand-built strings against tar's raw, unnormalized member names.
v1: Initial version.
"""

import argparse
import re
import shutil
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Version banner. Bump this (and the filename) whenever the logic changes,
# so it's always unambiguous which version of the script produced a given
# project or is being discussed.
# ---------------------------------------------------------------------------
SCRIPT_VERSION = "2"

# The four files that make up a project's "identity" and must be renamed
# and content-substituted. Order doesn't matter for correctness, but this
# order is used when printing progress messages.
IDENTITY_SUFFIXES = [".kicad_pro", ".kicad_sch", ".kicad_pcb", ".kicad_prl"]

# Of those four, only these three are checked in the pre-flight
# "does this project already exist" guard. .kicad_prl is intentionally
# excluded, per project decision: it's a local-settings file and its
# absence/presence shouldn't block or trigger the safety check.
PREFLIGHT_CHECK_SUFFIXES = [".kicad_pro", ".kicad_sch", ".kicad_pcb"]

# A regex that matches a standard RFC 4122 UUID string, e.g.
# "fd588964-f1d9-4f53-9002-e647c3faac14". Used to find the seed's own
# UUID inside kicad-template.kicad_sch, rather than hardcoding it here.
# This means the script keeps working correctly even if the seed archive
# is regenerated later with a different UUID.
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# A conservative allow-list for project names: letters, digits, underscore,
# and hyphen. This avoids accidentally creating filenames with spaces,
# slashes, or other characters that could confuse KiCad or the filesystem.
VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def fail(message: str) -> None:
    """Print a clear, unambiguous error message and exit with failure."""
    print(f"[kicad_init v{SCRIPT_VERSION}] ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def info(message: str) -> None:
    """Print a normal progress/status message."""
    print(f"[kicad_init v{SCRIPT_VERSION}] {message}")


def validate_project_name(name: str) -> None:
    """
    Sanity-check the requested new project name before doing anything else.
    A bad name here could otherwise turn into a confusing filesystem error
    much later in the script, so we catch it up front with a clear message.
    """
    if not name:
        fail("Project name must not be empty.")
    if not VALID_NAME_PATTERN.match(name):
        fail(
            f"Project name '{name}' contains characters other than letters, "
            "digits, underscore, and hyphen. KiCad project names should "
            "stick to these to avoid filesystem or tooling surprises."
        )
    if name.startswith("-"):
        fail(f"Project name '{name}' must not start with a hyphen.")


def open_seed_archive(seed_path: Path) -> tarfile.TarFile:
    """
    Open and sanity-check the seed archive. Returns an open TarFile handle
    on success; calls fail() and exits on any problem.
    """
    if not seed_path.exists():
        fail(f"Seed archive not found at '{seed_path}'.")
    if not seed_path.is_file():
        fail(f"Seed archive path '{seed_path}' exists but is not a file.")
    try:
        archive = tarfile.open(seed_path, mode="r:gz")
    except tarfile.ReadError as exc:
        fail(f"'{seed_path}' does not look like a valid .tgz/.tar.gz file: {exc}")
    return archive


def detect_root_prefix(archive: tarfile.TarFile) -> str:
    """
    Figure out the single top-level directory name inside the archive
    (e.g. "kicad-template"), rather than hardcoding it. This is also used
    later as the "seed token" string that gets replaced with the new
    project name, so the script and the archive can never disagree about
    what that token is.

    Fails loudly if the archive doesn't have exactly one top-level
    directory, since that would mean our assumptions about its layout
    don't hold.
    """
    top_level_names = set()
    for member in archive.getmembers():
        # Guard against unsafe paths (absolute paths or ".." components)
        # before we ever consider extracting anything from this archive.
        if member.name.startswith("/") or ".." in Path(member.name).parts:
            fail(
                f"Seed archive contains an unsafe path ('{member.name}'). "
                "Refusing to process this archive."
            )
        first_part = Path(member.name).parts[0] if member.name else ""
        if first_part:
            top_level_names.add(first_part)

    if len(top_level_names) != 1:
        fail(
            "Expected exactly one top-level directory in the seed archive, "
            f"found: {sorted(top_level_names)}. Re-check how the archive "
            "was created."
        )
    return top_level_names.pop()


def build_member_index(archive: tarfile.TarFile) -> dict:
    """
    Build a lookup table from a NORMALIZED relative path (e.g.
    "kicad-template/kicad-template.kicad_sch") to the archive's actual
    TarInfo member.

    This exists because tar archives can store member names with or
    without a leading "./" depending on how they were created (e.g.
    `tar czf x.tgz .` vs `tar czf x.tgz kicad-template`), and tarfile's
    own getmember()/extractfile() do an exact string match against
    whatever raw form was actually stored. By normalizing every name
    through pathlib once here, the rest of the script can look things up
    by a clean, predictable path and not care which convention the
    archive happened to use.
    """
    index = {}
    for member in archive.getmembers():
        normalized = Path(member.name).as_posix()
        index[normalized] = member
    return index


def extract_member_text(archive: tarfile.TarFile, member_index: dict, normalized_path: str) -> str:
    """Read one archive member's contents as UTF-8 text, looked up by its
    normalized relative path (see build_member_index)."""
    member = member_index.get(normalized_path)
    if member is None:
        fail(
            f"Expected '{normalized_path}' inside the seed archive but it "
            "was not found. Check the archive's contents with "
            "'tar tzf kicad-template.tgz'."
        )
    fileobj = archive.extractfile(member)
    if fileobj is None:
        fail(f"Could not read '{normalized_path}' from the seed archive (not a regular file?).")
    try:
        return fileobj.read().decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"'{normalized_path}' is not valid UTF-8 text: {exc}")


def find_seed_uuid(sch_text: str, seed_token: str) -> str:
    """
    Locate the seed's root-sheet UUID inside the .kicad_sch file's own
    top-level (uuid "...") line. We deliberately do NOT hardcode this
    value anywhere in the script -- it's read fresh from the archive
    every run, so a repacked seed with a different UUID just works.
    """
    match = UUID_PATTERN.search(sch_text)
    if not match:
        fail(
            f"Could not find a UUID inside {seed_token}.kicad_sch. "
            "Expected a line like '(uuid \"...\")' near the top of the file."
        )
    return match.group(0)


def build_identity_files(
    archive: tarfile.TarFile,
    member_index: dict,
    root_prefix: str,
    seed_token: str,
    new_name: str,
    scratch_dir: Path,
) -> str:
    """
    Extract, rename, and content-substitute the four identity files into
    scratch_dir. Returns the newly generated UUID that was used, purely
    for the summary printout at the end.

    Nothing is written to the real target directory in this function --
    that only happens after every one of these files has been built
    successfully, in the caller.
    """
    # First pass: read the seed schematic so we know which UUID to replace.
    sch_normalized_path = f"{root_prefix}/{seed_token}.kicad_sch"
    sch_text = extract_member_text(archive, member_index, sch_normalized_path)
    old_uuid = find_seed_uuid(sch_text, seed_token)
    new_uuid = str(uuid.uuid4())

    info(f"Found seed UUID {old_uuid}; generated new UUID {new_uuid} for '{new_name}'.")

    for suffix in IDENTITY_SUFFIXES:
        normalized_path = f"{root_prefix}/{seed_token}{suffix}"
        try:
            text = extract_member_text(archive, member_index, normalized_path)
        except SystemExit:
            # extract_member_text already called fail(); re-raise so the
            # whole script stops instead of continuing with a partial set
            # of identity files.
            raise

        # Two independent substitutions. Order doesn't matter since a
        # project name and a UUID cannot overlap in content.
        text = text.replace(seed_token, new_name)
        text = text.replace(old_uuid, new_uuid)

        out_path = scratch_dir / f"{new_name}{suffix}"
        out_path.write_text(text, encoding="utf-8")
        info(f"  prepared {out_path.name}")

    return new_uuid


def preflight_check(target_dir: Path, new_name: str) -> None:
    """
    Refuse to proceed if any of the three primary project files already
    exist in the target directory. This is the safety check that lets the
    same target directory safely hold multiple sibling designs -- it only
    ever blocks on a name collision, never on the directory being
    non-empty in general.
    """
    existing = [
        target_dir / f"{new_name}{suffix}"
        for suffix in PREFLIGHT_CHECK_SUFFIXES
        if (target_dir / f"{new_name}{suffix}").exists()
    ]
    if existing:
        existing_list = ", ".join(str(p) for p in existing)
        fail(
            f"Project '{new_name}' already appears to exist in "
            f"'{target_dir}'. Found: {existing_list}. "
            "Choose a different project name, or remove these files if "
            "this was a mistake."
        )


def extract_library_files(archive: tarfile.TarFile, root_prefix: str, target_dir: Path) -> None:
    """
    Extract everything in the archive EXCEPT the four identity files,
    directly into target_dir, skipping anything that already exists.
    This covers sym-lib-table, fp-lib-table, and the whole libraries/
    subtree (including empty directories like .pretty and .3dshapes
    folders).
    """
    identity_member_names = set()
    # We don't know seed_token here without re-deriving it, so instead we
    # simply treat "top-level file directly under the root, with one of
    # the identity suffixes" as identity -- everything else is a library
    # file. This keeps the function self-contained and easy to audit.
    for member in archive.getmembers():
        relative = Path(member.name).relative_to(root_prefix) if member.name != root_prefix else Path(".")
        if relative == Path("."):
            continue  # the root directory entry itself; nothing to do
        if len(relative.parts) == 1 and relative.suffix in IDENTITY_SUFFIXES:
            identity_member_names.add(member.name)

    created = []
    skipped = []

    for member in archive.getmembers():
        if member.name in identity_member_names:
            continue
        relative = Path(member.name).relative_to(root_prefix) if member.name != root_prefix else Path(".")
        if relative == Path("."):
            continue

        dest_path = target_dir / relative

        if member.isdir():
            # Directories are safe to "already exist" -- just make sure
            # they're present, never an overwrite concern.
            dest_path.mkdir(parents=True, exist_ok=True)
            continue

        if dest_path.exists():
            skipped.append(str(relative))
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        fileobj = archive.extractfile(member)
        if fileobj is None:
            fail(f"Could not read library file '{member.name}' from the archive.")
        dest_path.write_bytes(fileobj.read())
        created.append(str(relative))

    if created:
        info("Created library files:")
        for name in created:
            info(f"  + {name}")
    if skipped:
        info("Skipped (already present):")
        for name in skipped:
            info(f"  = {name}")
    if not created and not skipped:
        info("No library files found in archive outside the identity files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a new KiCad 10 project from a seed archive."
    )
    parser.add_argument("new_project_name", help="Name for the new project.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to initialize into (default: current directory).",
    )
    parser.add_argument(
        "--seed-archive",
        type=Path,
        default=None,
        help="Path to the seed .tgz (default: kicad-template.tgz next to this script).",
    )
    args = parser.parse_args()

    info(f"Starting kicad_init v{SCRIPT_VERSION}")

    validate_project_name(args.new_project_name)

    seed_path = args.seed_archive
    if seed_path is None:
        seed_path = Path(__file__).resolve().parent / "kicad-template.tgz"

    target_dir = args.target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    info(f"New project name : {args.new_project_name}")
    info(f"Target directory : {target_dir}")
    info(f"Seed archive     : {seed_path}")

    # Fail fast, before touching the archive at all, if this project name
    # already exists in the target directory.
    preflight_check(target_dir, args.new_project_name)

    archive = open_seed_archive(seed_path)
    try:
        root_prefix = detect_root_prefix(archive)
        seed_token = root_prefix  # by construction, the archive's single
        # top-level directory name IS the seed's project-name token.
        info(f"Detected seed token from archive: '{seed_token}'")

        # Build the normalized member lookup once, up front, so every
        # subsequent lookup by relative path is immune to whichever raw
        # naming convention (with or without "./") this particular
        # archive happens to use.
        member_index = build_member_index(archive)

        # --- Stage 1: build the identity files in a scratch directory ---
        scratch_dir = Path(tempfile.mkdtemp(prefix="kicad_init_"))
        try:
            new_uuid = build_identity_files(
                archive, member_index, root_prefix, seed_token, args.new_project_name, scratch_dir
            )

            # Re-check immediately before moving, in case anything changed
            # in the target directory during the (normally very fast)
            # extraction/substitution work above.
            preflight_check(target_dir, args.new_project_name)

            for suffix in IDENTITY_SUFFIXES:
                src = scratch_dir / f"{args.new_project_name}{suffix}"
                dst = target_dir / f"{args.new_project_name}{suffix}"
                shutil.move(str(src), str(dst))
                info(f"Installed {dst.name}")
        finally:
            shutil.rmtree(scratch_dir, ignore_errors=True)

        # --- Stage 2: extract shared library files, skipping existing ---
        extract_library_files(archive, root_prefix, target_dir)

    finally:
        archive.close()

    info(f"Done. Project '{args.new_project_name}' initialized in '{target_dir}'.")
    info(f"(kicad_init v{SCRIPT_VERSION}, new sheet UUID: {new_uuid})")


if __name__ == "__main__":
    main()
