"""WCAG 2.2 color-contrast engine shared across the HTML, DOCX, and PPTX
analyzers.

Grounded in the CLEAR Framework's "Easy to Read" guidance, which restates
WCAG Success Criteria:
  - 1.4.3 Contrast (Minimum), AA: 4.5:1 for normal text, 3:1 for LARGE text.
  - 1.4.1 Use of Color, A: color must not be the only visual means of
    conveying information (e.g. links need an indicator beyond color).

"Large text" per WCAG = 18pt (24px) or larger, OR 14pt (18.66px) or larger
if bold. Applying the 3:1 threshold to large text — and 4.5:1 to everything
else — is the single most common contrast-checker error; we get it right here.
"""
from __future__ import annotations

import re

# WCAG large-text thresholds, in CSS pixels (1pt = 1.333px).
LARGE_PX = 24.0          # 18pt
LARGE_BOLD_PX = 18.66    # 14pt bold


def required_ratio(font_px: float | None, bold: bool = False) -> float:
    """The AA contrast ratio this text must meet given its size/weight."""
    if font_px is None:
        return 4.5  # unknown size — hold to the stricter normal-text bar
    if font_px >= LARGE_PX or (bold and font_px >= LARGE_BOLD_PX):
        return 3.0
    return 4.5


def relative_luminance(rgb) -> float:
    vals = []
    for c in rgb:
        s = c / 255.0
        vals.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast_ratio(fg_rgb, bg_rgb) -> float:
    l1, l2 = relative_luminance(fg_rgb), relative_luminance(bg_rgb)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


# Full CSS named colors (CSS Color Module Level 4). Used so contrast checks
# work on "color: navy" / "background: lightgray" etc., not just hex/rgb.
CSS_NAMED_COLORS = {
    "aliceblue": (240, 248, 255), "antiquewhite": (250, 235, 215), "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212), "azure": (240, 255, 255), "beige": (245, 245, 220),
    "bisque": (255, 228, 196), "black": (0, 0, 0), "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255), "blueviolet": (138, 43, 226), "brown": (165, 42, 42),
    "burlywood": (222, 184, 135), "cadetblue": (95, 158, 160), "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30), "coral": (255, 127, 80), "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220), "crimson": (220, 20, 60), "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139), "darkcyan": (0, 139, 139), "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169), "darkgreen": (0, 100, 0),
    "darkkhaki": (189, 183, 107), "darkmagenta": (139, 0, 139), "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0), "darkorchid": (153, 50, 204), "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122), "darkseagreen": (143, 188, 143), "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79), "darkslategrey": (47, 79, 79), "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211), "deeppink": (255, 20, 147), "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105), "dimgrey": (105, 105, 105), "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34), "floralwhite": (255, 250, 240), "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255), "gainsboro": (220, 220, 220), "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0), "goldenrod": (218, 165, 32), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "green": (0, 128, 0), "greenyellow": (173, 255, 47),
    "honeydew": (240, 255, 240), "hotpink": (255, 105, 180), "indianred": (205, 92, 92),
    "indigo": (75, 0, 130), "ivory": (255, 255, 240), "khaki": (240, 230, 140),
    "lavender": (230, 230, 250), "lavenderblush": (255, 240, 245), "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205), "lightblue": (173, 216, 230), "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255), "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211), "lightgrey": (211, 211, 211), "lightgreen": (144, 238, 144),
    "lightpink": (255, 182, 193), "lightsalmon": (255, 160, 122), "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250), "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153), "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224), "lime": (0, 255, 0), "limegreen": (50, 205, 50),
    "linen": (250, 240, 230), "magenta": (255, 0, 255), "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170), "mediumblue": (0, 0, 205), "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219), "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238), "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204), "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112), "mintcream": (245, 255, 250), "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181), "navajowhite": (255, 222, 173), "navy": (0, 0, 128),
    "oldlace": (253, 245, 230), "olive": (128, 128, 0), "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0), "orangered": (255, 69, 0), "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170), "palegreen": (152, 251, 152), "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147), "papayawhip": (255, 239, 213), "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63), "pink": (255, 192, 203), "plum": (221, 160, 221),
    "powderblue": (176, 224, 230), "purple": (128, 0, 128), "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0), "rosybrown": (188, 143, 143), "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19), "salmon": (250, 128, 114), "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87), "seashell": (255, 245, 238), "sienna": (160, 82, 45),
    "silver": (192, 192, 192), "skyblue": (135, 206, 235), "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144), "slategrey": (112, 128, 144), "snow": (255, 250, 250),
    "springgreen": (0, 255, 127), "steelblue": (70, 130, 180), "tan": (210, 180, 140),
    "teal": (0, 128, 128), "thistle": (216, 191, 216), "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208), "violet": (238, 130, 238), "wheat": (245, 222, 179),
    "white": (255, 255, 255), "whitesmoke": (245, 245, 245), "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50),
}

_HEX_RE = re.compile(r"^#?([0-9a-f]{3,8})$", re.IGNORECASE)
_RGB_RE = re.compile(
    r"rgba?\(\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*,\s*([\d.]+%?)\s*(?:,\s*([\d.]+)\s*)?\)",
    re.IGNORECASE,
)


def _chan(v: str) -> int:
    v = v.strip()
    if v.endswith("%"):
        return round(float(v[:-1]) * 255 / 100)
    return int(round(float(v)))


def parse_color(value, over=(255, 255, 255)):
    """Parse a CSS/Office color string to an (r, g, b) tuple, or None.

    Handles #rgb / #rrggbb / #rrggbbaa, rgb()/rgba() (with %), and CSS named
    colors. Semi-transparent colors are composited over `over` (default white,
    the typical page background) so the resulting contrast is realistic.
    """
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s or s in ("transparent", "inherit", "initial", "currentcolor", "none", "auto"):
        return None

    if s in CSS_NAMED_COLORS:
        return CSS_NAMED_COLORS[s]

    m = _HEX_RE.match(s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        elif len(h) == 4:  # #rgba
            h = "".join(c * 2 for c in h)
        if len(h) >= 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            if len(h) == 8:  # alpha
                a = int(h[6:8], 16) / 255
                return _composite((r, g, b), a, over)
            return (r, g, b)
        return None

    m = _RGB_RE.match(s)
    if m:
        r, g, b = _chan(m.group(1)), _chan(m.group(2)), _chan(m.group(3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        if a < 1.0:
            return _composite((r, g, b), a, over)
        return (r, g, b)

    return None


def _composite(rgb, alpha, over):
    return tuple(round(c * alpha + o * (1 - alpha)) for c, o in zip(rgb, over))


def office_rgb(rgbcolor):
    """Convert a python-docx/pptx RGBColor (or hex string) to (r, g, b)."""
    if rgbcolor is None:
        return None
    s = str(rgbcolor)
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except ValueError:
            return None
    return None


def is_near(rgb, target, tol=24):
    """True if rgb is within `tol` of target on every channel (used to treat
    'almost black' text colors as black so we don't flag normal body text)."""
    return all(abs(a - b) <= tol for a, b in zip(rgb, target))
