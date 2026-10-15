"""
perfboard_lattice_v1.py

Run this in KiCad's PCB Editor Scripting Console (Tools > Scripting Console).
Draws a lattice of reference lines matching a perfboard's hole spacing, so you
can visually check that your PCB layout will map onto perfboard construction.

Note: this uses the legacy SWIG-based `pcbnew` Python API, which KiCad has
deprecated in favor of the IPC API and is slated for removal in KiCad 11.
It still works in KiCad 10. If you're reading this from a future KiCad
version and it breaks, that's why.
"""

import pcbnew

# ---------------------------------------------------------------------------
# EDIT THESE TO MATCH YOUR PERFBOARD
# ---------------------------------------------------------------------------

# Origin: a PCB grid point read from the KiCad status bar (absolute board
# coordinates, in mm), corresponding to one hole on your perfboard.
ORIGIN_X_MM = 139.70
ORIGIN_Y_MM = 129.54

# Spacing (mm) between each vertical line and the next one to its LEFT,
# starting from the vertical line through the origin. Use negative numbers
# for "moves left." The number of vertical lines drawn is len(X_SPACINGS_MM) + 1.
X_SPACINGS_MM = [-10.16, -10.16, -10.16, -12.70]

# Spacing (mm) between each horizontal line and the next one ABOVE it,
# starting from the horizontal line through the origin. Use negative numbers
# for "moves up the page" (KiCad's Y axis increases downward, so "up" means
# subtracting). The number of horizontal lines drawn is len(Y_SPACINGS_MM) + 1.
Y_SPACINGS_MM = [-7.62, -10.16, -10.16, -10.16, -10.16, -10.16]

# Appearance
LAYER = pcbnew.User_4          # drawn on the "User.4" layer regardless of its display name
LINE_WIDTH_MM = 0.25
LINE_STYLE_NAME = "DASH"       # one of: "SOLID", "DASH", "DOT", "DASHDOT", "DASHDOTDOT"

# ---------------------------------------------------------------------------
# END OF EDITABLE PARAMETERS — the rest recalculates from the above
# ---------------------------------------------------------------------------


def compute_positions(origin_mm, spacings_mm):
    """Turn an origin + a list of signed spacings into a list of absolute
    positions (mm), starting with the origin itself."""
    positions = [origin_mm]
    running = origin_mm
    for delta in spacings_mm:
        running += delta
        positions.append(running)
    return positions


def resolve_line_style(name):
    """Look up a LINE_STYLE value. KiCad's SWIG bindings have exposed enums
    a couple of different ways across versions, so try both."""
    enum_cls = getattr(pcbnew, "LINE_STYLE", None)
    if enum_cls is not None and hasattr(enum_cls, name):
        return getattr(enum_cls, name)
    flat_name = "LINE_STYLE_" + name
    if hasattr(pcbnew, flat_name):
        return getattr(pcbnew, flat_name)
    raise AttributeError(
        "Could not find LINE_STYLE '{}' in this KiCad's pcbnew module.\n"
        "In the console, try: [n for n in dir(pcbnew) if 'LINE_STYLE' in n]\n"
        "or: dir(pcbnew.LINE_STYLE)\n"
        "to see what's available, then update LINE_STYLE_NAME above.".format(name)
    )


def clear_previous_lattice(board, layer):
    """Remove any straight-line PCB_SHAPE objects already on this layer, so
    re-running the script after editing the parameters above replaces the
    old lattice instead of piling a new one on top of it."""
    removed = 0
    for item in list(board.GetDrawings()):
        if (isinstance(item, pcbnew.PCB_SHAPE)
                and item.GetLayer() == layer
                and item.GetShape() == pcbnew.SHAPE_T_SEGMENT):
            board.Remove(item)
            removed += 1
    return removed


def add_line(board, start_mm, end_mm, layer, width_iu, style):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(start_mm[0]), pcbnew.FromMM(start_mm[1])))
    shape.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end_mm[0]), pcbnew.FromMM(end_mm[1])))
    shape.SetLayer(layer)
    shape.SetWidth(width_iu)
    shape.SetLineStyle(style)
    board.Add(shape)


def main():
    board = pcbnew.GetBoard()

    x_positions = compute_positions(ORIGIN_X_MM, X_SPACINGS_MM)
    y_positions = compute_positions(ORIGIN_Y_MM, Y_SPACINGS_MM)

    x_min, x_max = min(x_positions), max(x_positions)
    y_min, y_max = min(y_positions), max(y_positions)

    width_iu = pcbnew.FromMM(LINE_WIDTH_MM)
    style = resolve_line_style(LINE_STYLE_NAME)

    removed = clear_previous_lattice(board, LAYER)

    for x in x_positions:
        add_line(board, (x, y_min), (x, y_max), LAYER, width_iu, style)

    for y in y_positions:
        add_line(board, (x_min, y), (x_max, y), LAYER, width_iu, style)

    pcbnew.Refresh()

    print("Removed {} old line(s). Drew {} vertical and {} horizontal lines on User.4.".format(
        removed, len(x_positions), len(y_positions)))
    print("Vertical x positions (mm): {}".format(["{:.3f}".format(v) for v in x_positions]))
    print("Horizontal y positions (mm): {}".format(["{:.3f}".format(v) for v in y_positions]))


main()
