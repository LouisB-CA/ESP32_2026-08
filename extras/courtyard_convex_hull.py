"""
courtyard_convex_hull.py

IMPORTANT: pcbnew.GetBoard() in the Scripting Console always refers to the
main PCB Editor's board -- it has NO access to whatever footprint you have
open in the separate Footprint Editor window, and there's no "selection"
concept on a footprint loaded outside the editor. So instead of working off
of a GUI selection, this script loads the footprint directly from its
library file, processes every shape on the courtyard layer(s), and saves
the result back to the same library file on disk.

SETUP (edit these two lines below before running):
  LIB_PATH        = the .pretty folder containing your footprint
                     (Preferences > Manage Footprint Libraries to find it)
  FOOTPRINT_NAME  = the footprint's name (shown in the Footprint Editor's
                     title bar as "LibraryNickname:FootprintName" -- you
                     want the FootprintName part)

BEFORE RUNNING:
  1. In the Footprint Editor, save the footprint (Ctrl+S) so your current
     edits are on disk.
  2. Close the footprint in the Footprint Editor (or at least don't have
     unsaved changes in it) -- this script edits the on-disk library file
     directly, and reopening/reverting afterward will discard anything
     unsaved in the editor.

Run this in KiCad's Scripting Console (Tools > Scripting Console, opened
from the main PCB Editor window -- it works fine for this since we're not
touching the PCB Editor's board at all).

AFTER RUNNING:
  Back in the Footprint Editor, use File > Revert (or close and reopen the
  footprint from the library) to load the updated version.

Test on a copy of your library first, and keep a backup of the .pretty
folder handy.
"""

import pcbnew
import math
import os

LIB_PATH = r"/path/to/YourLibrary.pretty"   # <-- EDIT THIS
FOOTPRINT_NAME = "YourFootprintName"         # <-- EDIT THIS
LAYERS = (pcbnew.F_CrtYd, pcbnew.B_CrtYd)    # process front and/or back courtyard

GRID_NM = 100000        # 0.1 mm, in nanometres (KiCad internal units)
CIRCLE_SEGMENTS = 48    # how finely to approximate circles before hulling


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points):
    """Andrew's monotone chain. Input/output: list of (x, y) tuples."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def shape_points(shape):
    """Return a list of (x, y) points (in nm) approximating a PCB_SHAPE's outline."""
    st = shape.GetShape()
    pts = []

    if st == pcbnew.S_CIRCLE:
        c = shape.GetCenter()
        r = shape.GetRadius()
        for i in range(CIRCLE_SEGMENTS):
            theta = 2 * math.pi * i / CIRCLE_SEGMENTS
            pts.append((c.x + r * math.cos(theta), c.y + r * math.sin(theta)))

    elif st == pcbnew.S_RECT:
        p1 = shape.GetStart()
        p2 = shape.GetEnd()
        pts = [(p1.x, p1.y), (p2.x, p1.y), (p2.x, p2.y), (p1.x, p2.y)]

    elif st == pcbnew.S_POLY:
        poly = shape.GetPolyShape()
        outline = poly.Outline(0)
        for i in range(outline.PointCount()):
            v = outline.CPoint(i)
            pts.append((v.x, v.y))

    else:
        # Segments, arcs, or anything else: just use the endpoints.
        p1 = shape.GetStart()
        p2 = shape.GetEnd()
        pts = [(p1.x, p1.y), (p2.x, p2.y)]

    return pts


def snap_outward(pt, cx, cy, grid=GRID_NM):
    x, y = pt
    x = grid * (math.ceil(x / grid) if x >= cx else math.floor(x / grid))
    y = grid * (math.ceil(y / grid) if y >= cy else math.floor(y / grid))
    return (int(x), int(y))


def process_layer(fp, layer):
    """Replace all PCB_SHAPE graphics on `layer` within footprint `fp` with
    a single convex-hull polygon. Returns True if a replacement was made."""
    shapes = [
        item for item in fp.GraphicalItems()
        if isinstance(item, pcbnew.PCB_SHAPE) and item.GetLayer() == layer
    ]

    if len(shapes) < 1:
        return False  # nothing on this layer, nothing to do

    if len(shapes) == 1 and shapes[0].GetShape() == pcbnew.S_POLY:
        return False  # already a single polygon, leave it alone

    width = shapes[0].GetWidth()

    all_points = []
    for s in shapes:
        all_points.extend(shape_points(s))

    if len(all_points) < 3:
        print(f"Layer {layer}: not enough points to form a polygon, skipping.")
        return False

    cx = sum(p[0] for p in all_points) / len(all_points)
    cy = sum(p[1] for p in all_points) / len(all_points)

    hull = convex_hull(all_points)
    snapped = [snap_outward(p, cx, cy) for p in hull]
    final_hull = convex_hull(snapped)

    new_shape = pcbnew.PCB_SHAPE(fp)
    new_shape.SetShape(pcbnew.S_POLY)
    new_shape.SetFilled(False)
    new_shape.SetLayer(layer)
    new_shape.SetWidth(width)

    poly = pcbnew.SHAPE_POLY_SET()
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in final_hull:
        chain.Append(pcbnew.VECTOR2I(x, y))
    chain.SetClosed(True)
    poly.AddOutline(chain)
    new_shape.SetPolyShape(poly)

    fp.Add(new_shape)
    for s in shapes:
        fp.Remove(s)

    print(f"Layer {layer}: replaced {len(shapes)} shape(s) with a "
          f"{len(final_hull)}-vertex convex hull polygon.")
    return True


def main():
    if not os.path.isdir(LIB_PATH):
        print(f"LIB_PATH does not look like a folder: {LIB_PATH}\n"
              f"Edit LIB_PATH/FOOTPRINT_NAME at the top of this script first.")
        return

    fp = pcbnew.FootprintLoad(LIB_PATH, FOOTPRINT_NAME)
    if fp is None:
        print(f"Could not load footprint '{FOOTPRINT_NAME}' from {LIB_PATH}. "
              f"Check the library path and footprint name (case-sensitive, "
              f"no .kicad_mod extension).")
        return

    changed = False
    for layer in LAYERS:
        if process_layer(fp, layer):
            changed = True

    if not changed:
        print("No courtyard layers needed changes.")
        return

    pcbnew.FootprintSave(LIB_PATH, fp)
    print(f"Saved updated footprint back to {LIB_PATH}. "
          f"Use File > Revert in the Footprint Editor to see the change.")


main()
