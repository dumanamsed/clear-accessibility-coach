import re
from bs4 import BeautifulSoup
from .models import Finding


def analyze_html(content: str) -> list[Finding]:
    findings = []
    soup = BeautifulSoup(content, "html.parser")

    _check_images(soup, findings)
    _check_headings(soup, findings)
    _check_links(soup, findings)
    _check_media(soup, findings)
    _check_contrast(soup, findings)
    _check_viewport(soup, findings)

    return findings


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
        if alt is None or alt.strip() == "":
            src = img.get("src", "unknown source")
            if len(src) > 80:
                src = src[:77] + "..."
            findings.append(Finding(
                strand="A",
                severity="critical",
                location=f"Image {i}",
                issue="Image is missing alt text or has an empty alt attribute.",
                evidence=f"<img src=\"{src}\">",
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


def _check_contrast(soup, findings):
    for elem in soup.find_all(style=True):
        style = elem.get("style", "")
        color_match = re.search(r"(?:^|;)\s*color\s*:\s*([^;]+)", style)
        bg_match = re.search(r"background(?:-color)?\s*:\s*([^;]+)", style)
        if color_match and bg_match:
            fg = color_match.group(1).strip()
            bg = bg_match.group(1).strip()
            fg_rgb = _parse_color(fg)
            bg_rgb = _parse_color(bg)
            if fg_rgb and bg_rgb:
                ratio = _contrast_ratio(fg_rgb, bg_rgb)
                if ratio < 4.5:
                    text_preview = elem.get_text(strip=True)[:60]
                    findings.append(Finding(
                        strand="E",
                        severity="warning",
                        location=f"Element with text: \"{text_preview}\"",
                        issue=f"Inline color contrast ratio is {ratio:.1f}:1, below WCAG AA minimum of 4.5:1.",
                        evidence=f"color: {fg}; background: {bg}",
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


def _parse_color(color_str: str):
    color_str = color_str.strip().lower()
    hex_match = re.match(r"^#([0-9a-f]{3,8})$", color_str)
    if hex_match:
        hex_val = hex_match.group(1)
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        if len(hex_val) >= 6:
            return (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))

    rgb_match = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color_str)
    if rgb_match:
        return (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)))

    named = {
        "white": (255, 255, 255), "black": (0, 0, 0),
        "red": (255, 0, 0), "yellow": (255, 255, 0),
        "gray": (128, 128, 128), "grey": (128, 128, 128),
    }
    return named.get(color_str)


def _relative_luminance(rgb):
    vals = []
    for c in rgb:
        s = c / 255.0
        vals.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _contrast_ratio(fg_rgb, bg_rgb):
    l1 = _relative_luminance(fg_rgb)
    l2 = _relative_luminance(bg_rgb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)
