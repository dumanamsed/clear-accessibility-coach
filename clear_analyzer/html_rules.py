import re
from bs4 import BeautifulSoup
from .models import Finding
from .contrast import parse_color, contrast_ratio, required_ratio

_IMAGE_EXT_RE = re.compile(
    r"^.+\.(png|jpg|jpeg|gif|bmp|tiff|tif|svg|webp|ico|emf|wmf)$",
    re.IGNORECASE,
)
_WEAK_ALT_PATTERNS = [
    re.compile(r"^image\s*\d*$", re.IGNORECASE),
    re.compile(r"^picture\s*\d*$", re.IGNORECASE),
    re.compile(r"^photo\s*\d*$", re.IGNORECASE),
    re.compile(r"^img[_\s]?\d*$", re.IGNORECASE),
    re.compile(r"^screenshot", re.IGNORECASE),
    re.compile(r"^graphic\s*\d*$", re.IGNORECASE),
    re.compile(r"^chart\s*\d*$", re.IGNORECASE),
]


def analyze_html(content: str) -> list[Finding]:
    findings = []
    soup = BeautifulSoup(content, "html.parser")

    _check_images(soup, findings)
    _check_headings(soup, findings)
    _check_links(soup, findings)
    _check_media(soup, findings)
    _check_contrast(soup, findings)
    _check_use_of_color(soup, findings)
    _check_justified(soup, findings)
    _check_viewport(soup, findings)
    _check_lang(soup, findings)
    _check_tables(soup, findings)
    _check_empty_links(soup, findings)

    return findings


def _check_lang(soup, findings):
    html = soup.find("html")
    if html is not None and not (html.get("lang") or "").strip():
        findings.append(Finding(
            strand="R",
            severity="warning",
            location="<html> element",
            issue="The page does not declare a language. Screen readers need it to choose the correct pronunciation voice.",
            evidence='Add lang="en" (or the content\'s language) to the <html> tag.',
        ))


def _check_tables(soup, findings):
    for i, table in enumerate(soup.find_all("table"), 1):
        if table.find("th") is None:
            findings.append(Finding(
                strand="L",
                severity="warning",
                location=f"Table {i}",
                issue="Table has no header cells (<th>). Screen reader users cannot tell which column or row a value belongs to.",
                evidence="Mark the header row cells with <th scope=\"col\"> (or <th scope=\"row\">).",
            ))


def _check_empty_links(soup, findings):
    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True):
            continue
        # A link whose only content is an image with alt text still has an
        # accessible name — only flag truly nameless links.
        imgs = a.find_all("img")
        if any((img.get("alt") or "").strip() for img in imgs):
            continue
        if (a.get("aria-label") or "").strip() or (a.get("title") or "").strip():
            continue
        findings.append(Finding(
            strand="E",
            severity="warning",
            location=f"Link to {a['href'][:60]}",
            issue="Link has no text or accessible name, so screen readers announce only the raw URL.",
            evidence=str(a)[:120],
        ))


def analyze_text(content: str) -> list[Finding]:
    findings = []
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for i, para in enumerate(paragraphs, 1):
        word_count = len(para.split())
        if word_count > 150:
            findings.append(Finding(
                strand="E",
                severity="tip",
                location=f"Paragraph {i}",
                issue=f"Long paragraph ({word_count} words). Consider breaking it into shorter chunks.",
                evidence=para[:120] + "...",
            ))
    return findings


def _check_images(soup, findings):
    for i, img in enumerate(soup.find_all("img"), 1):
        alt = img.get("alt")
        src = img.get("src", "unknown source")
        if len(src) > 80:
            src = src[:77] + "..."

        if alt is None or alt.strip() == "":
            findings.append(Finding(
                strand="A",
                severity="critical",
                location=f"Image {i}",
                issue="Image is missing alt text or has an empty alt attribute.",
                evidence=f"<img src=\"{src}\">",
            ))
        elif _IMAGE_EXT_RE.match(alt.strip()):
            findings.append(Finding(
                strand="A",
                severity="critical",
                location=f"Image {i}",
                issue="Image alt text is a filename, not a meaningful description.",
                evidence=f"alt=\"{alt.strip()}\", src=\"{src}\"",
            ))
        elif any(p.match(alt.strip()) for p in _WEAK_ALT_PATTERNS):
            findings.append(Finding(
                strand="A",
                severity="warning",
                location=f"Image {i}",
                issue="Image alt text appears to be generic or auto-generated. Consider a description of what the image conveys.",
                evidence=f"alt=\"{alt.strip()}\", src=\"{src}\"",
            ))


def _check_headings(soup, findings):
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    if not headings:
        body_text = soup.get_text(strip=True)
        if len(body_text) > 100:
            findings.append(Finding(
                strand="L",
                severity="warning",
                location="Entire document",
                issue="No heading elements found. Use headings to create a logical content hierarchy.",
                evidence="Document contains body text but no <h1>–<h6> elements.",
            ))
        return

    h1s = [h for h in headings if h.name == "h1"]
    if not h1s:
        findings.append(Finding(
            strand="L",
            severity="warning",
            location="Entire document",
            issue="No <h1> element found. Every page should have a primary heading.",
            evidence=f"First heading found is <{headings[0].name}>.",
        ))

    for j in range(1, len(headings)):
        prev_level = int(headings[j - 1].name[1])
        curr_level = int(headings[j].name[1])
        if curr_level > prev_level + 1:
            text = headings[j].get_text(strip=True)[:60]
            findings.append(Finding(
                strand="L",
                severity="warning",
                location=f"Heading: \"{text}\"",
                issue=f"Heading level skips from <h{prev_level}> to <h{curr_level}>.",
                evidence=f"<{headings[j].name}>{text}</{headings[j].name}>",
            ))


def _check_links(soup, findings):
    generic_texts = {"click here", "here", "link", "read more", "learn more"}
    for a in soup.find_all("a", href=True):
        link_text = a.get_text(strip=True).lower()
        if link_text in generic_texts:
            findings.append(Finding(
                strand="E",
                severity="tip",
                location=f"Link to {a['href'][:60]}",
                issue="Link uses generic text that does not describe its destination.",
                evidence=f'<a href="...">{a.get_text(strip=True)}</a>',
            ))


def _check_media(soup, findings):
    media_count = 0

    for tag_name in ("video", "audio"):
        for elem in soup.find_all(tag_name):
            media_count += 1
            findings.append(Finding(
                strand="C",
                severity="warning",
                location=f"<{tag_name}> element",
                issue=f"Embedded {tag_name} detected. Confirm that captions or a transcript are available.",
                evidence=str(elem)[:120],
            ))

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if any(domain in src.lower() for domain in ("youtube.com", "youtu.be", "vimeo.com")):
            media_count += 1
            findings.append(Finding(
                strand="C",
                severity="warning",
                location="Embedded video iframe",
                issue="Embedded video detected. Confirm that captions are enabled and accurate.",
                evidence=f'<iframe src="{src[:80]}">',
            ))


def _style_props(style: str) -> dict:
    """Parse a CSS declaration string into a {prop: value} dict."""
    props = {}
    for decl in style.split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            props[k.strip().lower()] = v.strip()
    return props


def _font_px(props: dict):
    """Best-effort font size in px from a style dict (pt/px/em/rem/%)."""
    fs = props.get("font-size")
    if not fs:
        return None
    m = re.match(r"([\d.]+)\s*(px|pt|em|rem|%)?", fs.strip(), re.IGNORECASE)
    if not m:
        return None
    val = float(m.group(1)); unit = (m.group(2) or "px").lower()
    if unit == "px":
        return val
    if unit == "pt":
        return val * 1.333
    if unit in ("em", "rem"):
        return val * 16.0
    if unit == "%":
        return val / 100.0 * 16.0
    return None


def _is_bold(props: dict) -> bool:
    w = props.get("font-weight", "").strip().lower()
    return w in ("bold", "bolder", "600", "700", "800", "900")


def _stylesheet_rules(soup):
    """Pull color/background/text-decoration declarations out of <style> blocks,
    keyed by selector. We can't resolve the full cascade without a browser, but
    a single rule that sets BOTH a text color and a background is self-contained
    and a common source of low-contrast text — worth checking."""
    rules = []
    for style_tag in soup.find_all("style"):
        css = style_tag.get_text() or ""
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        for m in re.finditer(r"([^{}]+)\{([^{}]+)\}", css):
            selector = m.group(1).strip()
            rules.append((selector, _style_props(m.group(2))))
    return rules


def _evaluate_contrast(fg_raw, bg_raw, props, location, evidence, findings):
    fg_rgb = parse_color(fg_raw)
    bg_rgb = parse_color(bg_raw, over=(255, 255, 255))
    if not fg_rgb or not bg_rgb:
        return
    ratio = contrast_ratio(fg_rgb, bg_rgb)
    needed = required_ratio(_font_px(props), _is_bold(props))
    if ratio + 0.05 < needed:
        size_note = "large text" if needed == 3.0 else "normal text"
        findings.append(Finding(
            strand="E",
            severity="warning",
            location=location,
            issue=f"Color contrast is {ratio:.1f}:1, below the WCAG 2.2 AA minimum "
                  f"of {needed:g}:1 for {size_note} (Success Criterion 1.4.3, Contrast Minimum).",
            evidence=evidence,
        ))


def _check_contrast(soup, findings):
    # 1) Inline styles that set a text color and a background together.
    for elem in soup.find_all(style=True):
        props = _style_props(elem.get("style", ""))
        fg = props.get("color")
        bg = props.get("background-color") or props.get("background")
        if fg and bg:
            preview = elem.get_text(strip=True)[:50]
            _evaluate_contrast(
                fg, bg, props,
                f'Element with text: "{preview}"' if preview else f"<{elem.name}>",
                f"color: {fg}; background: {bg}", findings,
            )

    # 2) <style> rules that set both color and background in one declaration.
    for selector, props in _stylesheet_rules(soup):
        fg = props.get("color")
        bg = props.get("background-color") or props.get("background")
        if fg and bg:
            _evaluate_contrast(
                fg, bg, props,
                f"CSS rule: {selector[:50]}",
                f"{selector} {{ color: {fg}; background: {bg} }}", findings,
            )


# Phrases that lean on color alone to convey meaning (WCAG 1.4.1).
_COLOR_REFERENCE_RE = re.compile(
    r"\b(?:the\s+)?(red|green|blue|yellow|orange|purple|pink|gray|grey)\s+"
    r"(button|link|text|box|highlight|section|item|tab|circle|dot|square|arrow|line)\b",
    re.IGNORECASE,
)


def _check_use_of_color(soup, findings):
    """WCAG 1.4.1 Use of Color (Level A): color must not be the only visual
    means of conveying information. CLEAR's Easy to Read guidance restates this:
    'Ensure links are visually distinguishable... with color AND an additional
    indicator like underlining.'"""
    # Links stripped of their underline and relying on color alone.
    decoration_none_selectors = any(
        "none" in (props.get("text-decoration", "") + props.get("text-decoration-line", "")).lower()
        and ("a" == sel.strip().lower() or sel.strip().lower().startswith("a"))
        for sel, props in _stylesheet_rules(soup)
    )
    flagged_inline = 0
    for a in soup.find_all("a", href=True):
        if not a.get_text(strip=True):
            continue  # nameless links handled elsewhere
        props = _style_props(a.get("style", ""))
        deco = (props.get("text-decoration", "") + props.get("text-decoration-line", "")).lower()
        inline_no_underline = "none" in deco
        # A link inside a paragraph that removes its underline relies on color.
        in_text = a.find_parent(["p", "li", "td", "span", "div"]) is not None
        if (inline_no_underline or (decoration_none_selectors and props.get("color"))) and in_text and flagged_inline < 5:
            flagged_inline += 1
            findings.append(Finding(
                strand="E",
                severity="warning",
                location=f"Link to {a['href'][:50]}",
                issue="Link removes its underline, so within body text it may be distinguishable "
                      "by color alone (WCAG 1.4.1, Use of Color). Keep an underline or another "
                      "non-color indicator.",
                evidence=a.get_text(strip=True)[:80],
            ))
    # Body copy that instructs by color name only.
    seen = 0
    for text in soup.find_all(string=_COLOR_REFERENCE_RE):
        if seen >= 3:
            break
        m = _COLOR_REFERENCE_RE.search(str(text))
        if m:
            seen += 1
            findings.append(Finding(
                strand="E",
                severity="tip",
                location="Body text",
                issue="Instructions appear to reference an element by color alone "
                      "(WCAG 1.4.1). Add a label, position, or icon so colorblind readers can follow.",
                evidence=f'"...{m.group(0)}..."',
            ))


def _check_justified(soup, findings):
    """CLEAR Easy to Read: 'Use left-aligned text rather than justified text.
    Justified text can create uneven spacing between words, making it harder
    to read' — especially for dyslexic readers."""
    flagged = 0
    seen_selectors = False
    for sel, props in _stylesheet_rules(soup):
        if props.get("text-align", "").strip().lower() == "justify":
            seen_selectors = True
            break
    for elem in soup.find_all(style=True):
        if flagged >= 3:
            break
        props = _style_props(elem.get("style", ""))
        if props.get("text-align", "").strip().lower() == "justify":
            flagged += 1
            findings.append(Finding(
                strand="E",
                severity="tip",
                location=f"<{elem.name}>",
                issue="Text is fully justified, which creates uneven word spacing ('rivers') "
                      "that is harder to read. CLEAR recommends left-aligned text.",
                evidence=elem.get_text(strip=True)[:80] or "text-align: justify",
            ))
    if seen_selectors and flagged == 0:
        findings.append(Finding(
            strand="E",
            severity="tip",
            location="Stylesheet",
            issue="A style rule sets text-align: justify. CLEAR recommends left-aligned "
                  "text — justification creates uneven spacing that is harder to read.",
            evidence="text-align: justify",
        ))


def _check_viewport(soup, findings):
    meta_vp = soup.find("meta", attrs={"name": "viewport"})
    html = soup.find("html")
    if html and not meta_vp:
        findings.append(Finding(
            strand="R",
            severity="tip",
            location="<head> section",
            issue="No <meta name=\"viewport\"> tag found. This may affect display on mobile devices.",
            evidence="Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        ))


