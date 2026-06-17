"""Theme-color resolution for Office documents.

Real Word/PowerPoint files almost never store explicit RGB on text. When a user
picks "light gray" or "Accent 1, Lighter 60%", Office stores a *theme color
reference* plus a tint/shade modulation — not an RGB value. To check the
contrast of the colors people actually use, we must resolve those references to
concrete RGB:

  1. Read the document's color scheme (theme1.xml <a:clrScheme>) → slot→RGB.
  2. Map the reference name (text1, accent1, bg1, …) to a scheme slot.
  3. Apply the lightening (tint / lumOff) or darkening (shade / lumMod).

This is what makes "light font" and "light table fill" detectable.
"""
from __future__ import annotations

import re

# WordprocessingML w:themeColor names → DrawingML clrScheme slot.
# (Default Office mapping; clrSchemeMapping overrides are rare in practice.)
DOCX_SLOT = {
    "text1": "dk1", "dark1": "dk1", "background1": "lt1", "light1": "lt1",
    "text2": "dk2", "dark2": "dk2", "background2": "lt2", "light2": "lt2",
    "accent1": "accent1", "accent2": "accent2", "accent3": "accent3",
    "accent4": "accent4", "accent5": "accent5", "accent6": "accent6",
    "hyperlink": "hlink", "followedHyperlink": "folHlink",
}

# DrawingML schemeClr names (PPTX) → clrScheme slot. The slide master's clrMap
# turns tx1/bg1 into dk1/lt1 etc.; we apply the default map.
PPTX_SLOT = {
    "tx1": "dk1", "dk1": "dk1", "bg1": "lt1", "lt1": "lt1",
    "tx2": "dk2", "dk2": "dk2", "bg2": "lt2", "lt2": "lt2",
    "accent1": "accent1", "accent2": "accent2", "accent3": "accent3",
    "accent4": "accent4", "accent5": "accent5", "accent6": "accent6",
    "hlink": "hlink", "folHlink": "folHlink",
}

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _hex_to_rgb(h):
    if not h or len(h) < 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def read_clr_scheme(theme_xml: bytes) -> dict:
    """Parse a theme1.xml byte string into {slot: (r,g,b)}.

    Each slot child is either <a:srgbClr val="RRGGBB"/> or
    <a:sysClr val="windowText" lastClr="000000"/> (we use lastClr)."""
    from lxml import etree
    scheme = {}
    try:
        root = etree.fromstring(theme_xml)
    except Exception:
        return scheme
    clr = root.find(f".//{_A}clrScheme")
    if clr is None:
        return scheme
    for slot_el in clr:
        slot = etree.QName(slot_el).localname  # dk1, lt1, accent1, ...
        srgb = slot_el.find(f"{_A}srgbClr")
        sys = slot_el.find(f"{_A}sysClr")
        rgb = None
        if srgb is not None:
            rgb = _hex_to_rgb(srgb.get("val", ""))
        elif sys is not None:
            rgb = _hex_to_rgb(sys.get("lastClr", "")) or (
                (0, 0, 0) if sys.get("val") == "windowText" else (255, 255, 255)
            )
        if rgb:
            scheme[slot] = rgb
    return scheme


def apply_tint(rgb, tint_byte: int):
    """WML themeTint: lighten toward white. tint_byte is 0-255 (hex in XML)."""
    t = tint_byte / 255.0
    return tuple(round(c * t + 255 * (1 - t)) for c in rgb)


def apply_shade(rgb, shade_byte: int):
    """WML themeShade: darken toward black."""
    s = shade_byte / 255.0
    return tuple(round(c * s) for c in rgb)


def apply_lum(rgb, lum_mod=None, lum_off=None):
    """DrawingML lumMod/lumOff (PPTX), values in thousandths (e.g. 60000 = 60%).
    Applied to the L channel in HSL — this is how PowerPoint produces its
    'Lighter/Darker' theme variants."""
    import colorsys
    r, g, b = [c / 255.0 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if lum_mod is not None:
        l = l * (lum_mod / 100000.0)
    if lum_off is not None:
        l = l + (lum_off / 100000.0)
    l = max(0.0, min(1.0, l))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))


# ---------- DOCX ----------

def docx_theme_map(document) -> dict:
    """Return {slot: rgb} for a python-docx Document, or {} if no theme part."""
    try:
        part = document.part
        for rel in part.package.iter_parts():
            if rel.partname.endswith("theme/theme1.xml") or (
                "theme" in str(rel.partname) and str(rel.partname).endswith(".xml")
            ):
                return read_clr_scheme(rel.blob)
    except Exception:
        pass
    return {}


def resolve_docx_color(color_el, theme_map):
    """Resolve a <w:color> element to (r,g,b). Handles themeColor + tint/shade,
    falling back to the explicit w:val. Returns None if unresolved/auto."""
    from docx.oxml.ns import qn
    if color_el is None:
        return None
    theme_name = color_el.get(qn("w:themeColor"))
    val = color_el.get(qn("w:val"))
    rgb = None
    if theme_name:
        slot = DOCX_SLOT.get(theme_name)
        if slot and slot in theme_map:
            rgb = theme_map[slot]
    if rgb is None and val and val.lower() != "auto":
        rgb = _hex_to_rgb(val)
    if rgb is None:
        return None
    tint = color_el.get(qn("w:themeTint"))
    shade = color_el.get(qn("w:themeShade"))
    if tint:
        try:
            rgb = apply_tint(rgb, int(tint, 16))
        except ValueError:
            pass
    elif shade:
        try:
            rgb = apply_shade(rgb, int(shade, 16))
        except ValueError:
            pass
    return rgb


def docx_cell_fill(tc, theme_map):
    """Resolve a table cell's shading fill to (r,g,b), or None (no/auto fill)."""
    from docx.oxml.ns import qn
    tcPr = tc.find(qn("w:tcPr"))
    if tcPr is None:
        return None
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        return None
    fill = shd.get(qn("w:fill"))
    theme_fill = shd.get(qn("w:themeFill"))
    rgb = None
    if theme_fill:
        slot = DOCX_SLOT.get(theme_fill)
        if slot and slot in theme_map:
            rgb = theme_map[slot]
    if rgb is None and fill and fill.lower() not in ("auto", ""):
        rgb = _hex_to_rgb(fill)
    if rgb is None:
        return None
    tint = shd.get(qn("w:themeFillTint"))
    shade = shd.get(qn("w:themeFillShade"))
    if tint:
        try:
            rgb = apply_tint(rgb, int(tint, 16))
        except ValueError:
            pass
    elif shade:
        try:
            rgb = apply_shade(rgb, int(shade, 16))
        except ValueError:
            pass
    return rgb


# ---------- PPTX ----------

def pptx_theme_map(prs) -> dict:
    """Return {slot: rgb} from the first theme part in a python-pptx Presentation."""
    try:
        for part in prs.part.package.iter_parts():
            name = str(part.partname)
            if "/theme/" in name and name.endswith(".xml"):
                m = read_clr_scheme(part.blob)
                if m:
                    return m
    except Exception:
        pass
    return {}


def resolve_pptx_run_color(rPr, theme_map):
    """Resolve a run's <a:rPr> solidFill to (r,g,b). Handles srgbClr and
    schemeClr (with lumMod/lumOff). Returns None if not a solid explicit color."""
    if rPr is None:
        return None
    fill = rPr.find(f"{_A}solidFill")
    if fill is None:
        return None
    srgb = fill.find(f"{_A}srgbClr")
    if srgb is not None:
        rgb = _hex_to_rgb(srgb.get("val", ""))
        return _apply_child_lum(srgb, rgb)
    scheme = fill.find(f"{_A}schemeClr")
    if scheme is not None:
        slot = PPTX_SLOT.get(scheme.get("val", ""))
        rgb = theme_map.get(slot) if slot else None
        if rgb:
            return _apply_child_lum(scheme, rgb)
    return None


def _apply_child_lum(clr_el, rgb):
    if rgb is None:
        return None
    lum_mod = clr_el.find(f"{_A}lumMod")
    lum_off = clr_el.find(f"{_A}lumOff")
    tint = clr_el.find(f"{_A}tint")
    shade = clr_el.find(f"{_A}shade")
    if lum_mod is not None or lum_off is not None:
        rgb = apply_lum(
            rgb,
            int(lum_mod.get("val")) if lum_mod is not None else None,
            int(lum_off.get("val")) if lum_off is not None else None,
        )
    if tint is not None:
        # DML tint val in thousandths: blend toward white by (1 - t)
        t = int(tint.get("val")) / 100000.0
        rgb = tuple(round(c * t + 255 * (1 - t)) for c in rgb)
    if shade is not None:
        s = int(shade.get("val")) / 100000.0
        rgb = tuple(round(c * s) for c in rgb)
    return rgb
