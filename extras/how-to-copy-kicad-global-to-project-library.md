# Copying a Symbol (and its Footprint + 3D Model) into Project-Specific Libraries — KiCad 10 (AppImage)

This document walks through moving a single component — symbol, footprint, and 3D model — from KiCad's global libraries into project-specific libraries. It captures the exact steps, the reasoning behind them, and every gotcha encountered along the way. Repeat this whole process for each additional symbol you want to migrate.

Summarized by Claude Sonnet 5 from a chat on 2026-08-28

## Background / Setup Assumptions

- Running KiCad 10 via AppImage on Linux.
- A project-specific **symbol** library has already been initialized and registered in the project's symbol library table.
- The schematic already contains one or more instances of the symbol, sourced from a **global** KiCad symbol library (either an official library or your own personal global library).
- Project-specific **footprint** (`.pretty`) and **3D model** (`.3dshapes`) libraries/folders do **not** exist yet at the start of this walkthrough — we create them as we go.

---

## Part 1 — Copy the Symbol into the Project Library

### Step 1: Open the Symbol Editor from the schematic

1. Open the schematic in the Schematic Editor.
2. Single-click (not double-click) the symbol instance you want to copy.
3. Right-click → **Edit Symbol...** (or press `E`).

This opens the Symbol Editor with a **copy** of the symbol loaded in memory — not a live link back to the library file.

**What to check:**
- [ ] Symbol Editor opens successfully.
- [ ] The header/heading in the Symbol Editor indicates you are editing **from the schematic** and that a plain **Save** will update the schematic instance only — *not* any library file. This is an important distinction; don't skip reading it.

> **Lesson learned:** There is also a link/option in this header to "open the symbol from the library" instead — that's a different editing context (editing the library master directly) and is what to use later, in Part 1, Step 6, once the project library actually contains the symbol.

### Step 2: Save a copy into the project-specific symbol library

1. In the Symbol Editor, use **File > Save Copy As...** — *not* **Save As**.
   - **Why "Save Copy As" and not "Save As":** `Save As` can switch your current editing target to the new location, which gets confusing if you're repeating this for multiple symbols. `Save Copy As` just writes a copy out without disturbing your current context.
2. In the dialog, choose your **project-specific symbol library** as the destination.
3. Keep the symbol name **identical** to the original. This makes it trivial later to swap the schematic's reference to the new library copy, since only the library nickname changes, not the symbol name.
4. Confirm the save.
5. Close the Symbol Editor. It will prompt:
   - **"Update the symbol (the schematic version)?"** → Answer **No** (you don't want to disturb the current schematic instance yet).
   - **"Update the library?"** → Answer **Yes**.

**What to check:**
- [ ] The dialog let you pick your project-specific symbol library correctly.
- [ ] No errors reported (a silent success is normal/expected here).
- [ ] Reopening the project library shows the new symbol is present, and you can now insert it from the project-specific library onto the schematic.

> **Note:** This step only copies the symbol *definition*. It does **not** change which library the *existing* schematic instance points to — that happens later, and in this workflow was effectively handled by placing brand-new instances from the project library (see Part 4).

---

## Part 2 — Copy the Footprint into a Project-Specific Footprint Library

Before editing the library symbol's footprint field, the footprint must actually exist in a project-specific location — you can't point a field at something that isn't there yet.

### Step 3: Open the footprint in the Footprint Editor

1. Open the PCB Editor (or go straight to the Footprint Editor).
2. Right-click the footprint on the board → **Edit Footprint** (or, if not yet placed, use **File > Open Footprint from Library** in the Footprint Editor).
3. Confirm the Footprint Editor's header — like the Symbol Editor — indicates that saving will update the **board only**, not any library.

**What to check:**
- [ ] Footprint Editor opens with the footprint loaded.
- [ ] Header confirms "editing a copy" / board-only save behavior.
- [ ] Note which global library it's currently sourced from (for reference).

### Step 4: Create the project-specific footprint library (if it doesn't exist yet)

> **Lesson learned:** Don't assume a `.pretty` directory exists just because you *planned* to create one earlier — verify first. In this walkthrough, the `.pretty` directory did not actually exist yet, which was discovered only when `Save As` had nowhere sensible to write to.

1. In the Footprint Editor (or PCB Editor), go to **File > New Library...**
2. Choose a save location inside your project folder (alongside the project-specific symbol library, for consistency). KiCad creates a `.pretty` directory at this location.
3. When prompted **Global vs. Project** library table, choose **Project**.
   - Note: **Project** may already appear as the default choice — but confirm it rather than assuming.
4. Confirm the new `.pretty` directory now exists and is registered in the project's footprint library table.

**What to check:**
- [ ] Prompted for Global vs. Project, and Project was selected.
- [ ] New `.pretty` directory exists on disk.

### Step 5: Save a copy of the footprint into the new library

1. With the new project footprint library created and registered, go to **File > Save As...** in the Footprint Editor.
   - Note: unlike the Symbol Editor, the Footprint Editor in KiCad 10 typically only offers **Save As** (no separately labeled "Save Copy As") — but it behaves the same way here: it writes a copy out without forcibly changing your active editing target.
2. Choose your new project-specific `.pretty` library as the destination.
3. Keep the footprint name **identical** to the original, for the same reason as with the symbol.
4. Confirm the save.
5. On closing the Footprint Editor, if prompted to update the board, answer **No** (same reasoning as the symbol — don't disturb the current board instance yet).

**What to check:**
- [ ] A `.kicad_mod` file now exists inside the new project `.pretty` directory.
- [ ] Prompt on close (if any) answered **No** to updating the board.

---

## Part 3 — Copy the 3D Model into the Project

The `.3dshapes` folder is **not** a KiCad-managed library table entry the way symbol/footprint libraries are — it's just a folder convention. The footprint stores a *path string* (often using an environment variable) pointing to the actual `.step`/`.wrl`/`.wrl` file. We need to find that file, copy it, and repoint the footprint at the new location.

### Step 6: Identify the exact 3D model path

1. With your **new project-library copy** of the footprint open in the Footprint Editor, open **Footprint Properties** → **3D Models** tab.
2. Note the exact path string shown, e.g.:
   ```
   ${KICAD10_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-92_Inline.step
   ```
3. Optionally confirm the resolved value of the environment variable via **Preferences > Configure Paths...** (look up `KICAD10_3DMODEL_DIR`).

### Step 7: Locate and copy the actual file — AppImage FUSE-mount gotcha

> **Lesson learned — important AppImage-specific issue:** The AppImage mounts itself via FUSE at runtime (e.g. `/tmp/.mount_kicad...`). This FUSE mount is **only accessible to the user account that launched the AppImage** — by default, **not even root** can read it, and `ls -la` on the mount point may show no owner/group information when queried as a different user.

**Do not extract the AppImage contents to work around this** — it's unnecessary. Instead:

1. Run the copy command as the **same normal user** who launched KiCad — **not** as root, and **not** with `sudo`.
   ```bash
   cp "/tmp/.mount_<your-mount-id>/<path from KICAD10_3DMODEL_DIR>/Package_TO_SOT_THT.3dshapes/TO-92_Inline.step" \
      /path/to/your/project/.3dshapes/
   ```
2. Verify: `ls -la /tmp/.mount_<your-mount-id>/` should be readable as your normal user, even if it fails as root.

**What to check:**
- [ ] Confirmed the mount is unreadable as root but readable as the normal user (validates the FUSE permissions theory — this is expected, not a bug to "fix").
- [ ] `.step` file successfully copied into the project's `.3dshapes` directory.

### Step 8: Repoint the footprint's 3D model field at the project copy

1. Still in **Footprint Properties > 3D Models** tab, on the project-library copy of the footprint:
   - Click the **folder icon** and browse to your newly-copied `.step` file. This adds it to the model list using a clean project-relative path (typically using the `${KIPRJMOD}` variable) rather than a hardcoded absolute path.
   - Select the **old** entry (the one referencing `${KICAD10_3DMODEL_DIR}`) and remove it using the **trash can icon**.
2. Confirm the remaining entry's path contains `${KIPRJMOD}`, confirming it's now a project-relative reference rather than pointing back into the global/AppImage location.

**What to check:**
- [ ] Old `${KICAD10_3DMODEL_DIR}`-based entry removed.
- [ ] New entry added, confirmed to use `${KIPRJMOD}` in its path.
- [ ] Footprint saved.

> **Note on reference designator at the footprint level:** The footprint may still display a leftover reference designator (e.g. `U2`) inherited from the specific board instance it was copied from. This does **not** need to be fixed here — reference designators are annotated/assigned at the schematic level (see Part 4), and the footprint will pick up whatever the schematic assigns when the board is updated.

---

## Part 4 — Fix the Library Symbol: Reference Designator and Footprint Field

Now that the project footprint library actually contains a footprint, the symbol's footprint field can be pointed at it.

### Step 9: Edit the symbol directly from the library (not from the schematic)

1. Open the Symbol Editor **directly from the project-specific symbol library** this time (not via "Edit Symbol" from a schematic instance) — you're editing the library master copy now, not a temporary schematic-linked copy.
2. Select your symbol and open it for editing.

### Step 10: Set the reference designator prefix to `U?`

1. Find the **Reference** field (shown on the symbol itself, and in symbol properties).
2. Change it from a specific designator like `U2` to `U?`.
   - **Why:** Library symbols should always use the `<Prefix>?` form (e.g. `U?`, `R?`, `C?`). This is what allows KiCad to auto-number each new instance placed on a schematic (U1, U2, U3, ...). Since the copy was made from a live schematic instance, it inherited that instance's specific designator (`U2`) instead of the generic placeholder — this needs to be corrected in the library master.

### Step 11: Set the footprint field to point at the project footprint library

1. Open the symbol's **Properties**.
2. Find the **Footprint** field.
3. Use the **"..."** browse button next to the field (recommended over typing manually, to avoid library-nickname typos) and select your project footprint library's copy, e.g.:
   ```
   YourFootprintLibraryName:TO-92_Inline
   ```

**What to check:**
- [ ] Browse button for the footprint field lists your project footprint library as an available option (confirms it's correctly registered in the project's footprint library table).
- [ ] Field set to the project library's footprint, not the global one.

### Step 12: Save

1. Since you're editing directly in the library (not from a schematic copy this time), a plain **Save** is correct and sufficient — no "Save Copy As" needed here.

**What to check:**
- [ ] Reopening the symbol in the library shows `U?` as the reference designator.
- [ ] Reopening the symbol shows the new project-library footprint reference.

---

## Part 5 — Use the Updated Symbol on the Schematic and Board

### Step 13: Place new instances from the project library

1. Insert new copies of the symbol from the **project-specific symbol library** onto the schematic (rather than editing the old global-sourced instances in place).
2. Confirm new instances come in showing `U?` (not a leftover specific designator like `U2`) — confirming Step 10 worked correctly.

### Step 14: Annotate and update the PCB

1. Annotate the schematic (KiCad will prompt for this if new un-annotated `U?` symbols are present before letting you update the PCB).
2. Update the PCB from the schematic (Tools/Update PCB from Schematic, or the equivalent toolbar action).
3. Open the 3D Viewer and confirm all instances — old and new — render correctly with the appropriate footprints and 3D models.

**What to check:**
- [ ] Schematic annotation completed without errors.
- [ ] PCB update completed, all new footprints placed correctly.
- [ ] 3D Viewer shows all instances (including the newly added ones) rendering as expected.

---

## Summary Checklist (Whole Process, Per Symbol)

- [ ] Open symbol from schematic via **Edit Symbol** (confirm "schematic-only save" header)
- [ ] **Save Copy As** into project symbol library (answer **No**/**Yes** to update-schematic/update-library prompts)
- [ ] Open footprint via **Edit Footprint** (confirm "board-only save" header)
- [ ] Create project `.pretty` library via **File > New Library**, registering to **Project** (not Global)
- [ ] **Save As** footprint copy into the new project `.pretty` library (answer **No** to update-board prompt)
- [ ] Check footprint's **3D Models** tab for the exact model path
- [ ] Copy the `.step`/3D model file as the **normal user** (not root) due to AppImage FUSE mount permissions — no need to extract the AppImage
- [ ] Add new 3D model reference via folder icon (confirm it uses `${KIPRJMOD}`); remove old global reference via trash icon
- [ ] Open symbol **directly from the project library** (not from schematic) for master editing
- [ ] Change Reference field from specific designator (e.g. `U2`) to prefix form (e.g. `U?`)
- [ ] Set Footprint field to the project footprint library's copy via the "..." browse button
- [ ] Plain **Save** (editing library master directly)
- [ ] Place new symbol instances from the project library on the schematic; confirm `U?` auto-numbering
- [ ] Annotate schematic, update PCB, confirm 3D Viewer shows everything correctly

---

## Key Lessons Learned

- **"Save Copy As" vs "Save As"** in the Symbol Editor: use *Save Copy As* to avoid switching your active editing context.
- **Editing-context headers matter**: both the Symbol Editor and Footprint Editor clearly indicate whether a plain Save will affect only the current schematic/board instance, or a library file. Always check this before saving.
- **Verify libraries/folders actually exist before assuming so** — don't rely on memory of what you set up earlier; check the filesystem or library tables directly.
- **Global vs. Project library table choice** matters and may default to Project — but always confirm rather than assume.
- **`.3dshapes` is a folder convention, not a managed library table entry** — 3D model paths are just path strings stored per-footprint, often using environment variables like `${KICAD10_3DMODEL_DIR}` (global) or `${KIPRJMOD}` (project-relative).
- **AppImage FUSE mounts are per-user**: files exposed by a running AppImage (e.g. bundled 3D models under `/tmp/.mount_...`) are typically readable only by the user account that launched the AppImage — not root, and not other users. This is expected FUSE behavior, not a bug, and does **not** require extracting the AppImage to work around.
- **Library symbols use `<Prefix>?` reference designators** (e.g. `U?`), not a specific instance number — this is what enables auto-numbering when placing new instances. A symbol copied from a live schematic instance inherits that instance's specific number and must be corrected.
- **Footprint-level reference designators do not need manual correction** — they're driven by schematic annotation, not the footprint library entry.
- **Use the browse ("...") buttons** for footprint fields and 3D model paths where available, rather than typing library nicknames/paths manually, to avoid typos.
- **Keep symbol/footprint names identical** between the global original and the project-specific copy — this keeps the relationship between old and new copies obvious and simplifies re-pointing schematic/board instances later.
- **New schematic instances placed from the updated project library are the simplest way to get the corrected reference designator behavior** — rather than trying to force an existing instance to re-link to the new library.
