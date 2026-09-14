"""Shared matplotlib theme + palette for the SDI notebooks.

Colors are the validated reference palette: categorical slots are used in fixed
order (never cycled), sequential encodings use a single hue light->dark, and the
diverging ramp is blue<->red with a neutral gray midpoint. Notebook output is
rendered on a light surface, so only the light steps are defined here.
"""

from matplotlib.colors import LinearSegmentedColormap
import matplotlib as mpl

# --- surfaces & ink --------------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# --- categorical: fixed order, first three validate all-pairs --------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
BLUE, ORANGE, AQUA = SERIES

# --- sequential: one hue, light -> dark ------------------------------------
BLUE_RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
SEQ = LinearSegmentedColormap.from_list("sdi_seq", BLUE_RAMP)

# --- diverging: warm/cool poles, neutral gray midpoint ---------------------
DIV = LinearSegmentedColormap.from_list(
    "sdi_div", ["#104281", "#3987e5", "#9ec5f4", "#f0efec", "#f0a3a3", "#d03b3b", "#8f2020"]
)

# --- status (reserved; never reused as a series color) ---------------------
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"


def apply_theme():
    """Thin marks, hairline recessive grid, generous padding."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
        "axes.titlecolor": INK,
        "axes.titlepad": 10,
        "axes.labelsize": 9,
        "axes.labelcolor": INK_SECONDARY,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "grid.linestyle": "-",       # solid hairlines; dashing reads as "threshold"
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelcolor": INK_SECONDARY,
        "ytick.labelcolor": INK_SECONDARY,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "lines.linewidth": 2,
        "lines.markersize": 8,
        "figure.constrained_layout.use": True,
    })


def style_table(styler, caption=None, fmt=None, hide_index=True):
    """Consistent look for the notebook's DataFrame tables."""
    s = styler
    if caption:
        s = s.set_caption(caption)
    if fmt:
        s = s.format(fmt)
    if hide_index:
        s = s.hide(axis="index")
    return s.set_table_styles([
        {"selector": "caption",
         "props": [("caption-side", "top"), ("font-size", "10.5pt"),
                   ("font-weight", "600"), ("color", INK),
                   ("text-align", "left"), ("padding-bottom", "6px")]},
        {"selector": "th",
         "props": [("background-color", PAGE), ("color", INK_SECONDARY),
                   ("font-weight", "600"), ("text-align", "right"),
                   ("border-bottom", f"1px solid {AXIS}")]},
        {"selector": "td",
         "props": [("text-align", "right"), ("font-variant-numeric", "tabular-nums"),
                   ("border-bottom", f"1px solid {GRID}")]},
        {"selector": "", "props": [("border-collapse", "collapse")]},
    ])
