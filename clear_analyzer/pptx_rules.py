from io import BytesIO
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.shapes import MSO_SHAPE_TYPE
from lxml import etree
from .models import Finding

# All namespaces used in PPTX XML
NSMAP = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def analyze_pptx(file_bytes: bytes) -> list[Finding]:
    findings = []
    prs = Presentation(BytesIO(file_bytes))

    for slide_num, slide in enumerate(prs.slides, 1):
        loc = f"Slide {slide_num}"
        _check_images(slide, loc, findings)
        _check_title(slide, loc, findings)
        _check_media(slide, loc, findings)
        _check_text(slide, loc, findings)

    return findings


def _get_alt_text(shape):
    """Extract alt text from any shape by walking the XML tree.

    python-pptx doesn't expose alt text directly on all shape types.
    Alt text lives in the 'descr' attribute of the cNvPr element inside
    the shape's non-visual properties (nvSpPr, nvPicPr, nvGrpSpPr, etc.).
    We also check the newer a16:creationId parent's descr.
    """
    el = shape._element

    # Method 1: Find any cNvPr element anywhere in this shape's XML
    for cNvPr in el.iter():
        if cNvPr.tag.endswith("}cNvPr") or cNvPr.tag == "cNvPr":
            descr = cNvPr.get("descr", "")
            if descr and descr.strip():
                return descr.strip()

    # Method 2: Check for decorative flag (Office 365+)
    # <adec:decorative val="1"/> means intentionally decorative
    for dec in el.iter():
        if "decorative" in dec.tag.lower():
            val = dec.get("val", "")
            if val == "1":
                return "__DECORATIVE__"

    return ""


def _check_images(slide, loc, findings):
    """Check ALL shapes that contain images, not just PICTURE type."""
    seen_shapes = set()

    for shape in slide.shapes:
        _check_shape_for_image(shape, loc, findings, seen_shapes)


def _check_shape_for_image(shape, loc, findings, seen_shapes):
    """Recursively check a shape (and grouped shapes) for images."""
    shape_id = id(shape)
    if shape_id in seen_shapes:
        return
    seen_shapes.add(shape_id)

    # Check grouped shapes recursively
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        if hasattr(shape, "shapes"):
            for child_shape in shape.shapes:
                _check_shape_for_image(child_shape, loc, findings, seen_shapes)
        return

    # Determine if this shape contains an image
    is_image = False

    # Direct picture type
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        is_image = True

    # Placeholder with an image fill
    if not is_image and hasattr(shape, "placeholder_format") and shape.placeholder_format is not None:
        el = shape._element
        blipFills = list(el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blipFill"))
        if blipFills:
            is_image = True

    # Any shape with a blipFill (image fill) that isn't a placeholder
    if not is_image:
        el = shape._element
        blipFills = list(el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blipFill"))
        if blipFills:
            is_image = True

    # Shape with an image in its spPr (shape properties) via blipFill
    if not is_image:
        el = shape._element
        # Check for pic element
        pics = list(el.iter("{http://schemas.openxmlformats.org/presentationml/2006/main}pic"))
        if not pics:
            pics = list(el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}pic"))
        if pics:
            is_image = True

    if not is_image:
        return

    alt_text = _get_alt_text(shape)

    if alt_text == "__DECORATIVE__":
        # Marked as decorative — this is correct, no finding needed
        return

    if not alt_text:
        name = shape.name or "Image"
        findings.append(Finding(
            strand="A",
            severity="critical",
            location=loc,
            issue="Image is missing alt text.",
            evidence=f"Shape: {name}",
        ))


def _check_title(slide, loc, findings):
    has_title = False
    if slide.shapes.title and slide.shapes.title.has_text_frame:
        title_text = slide.shapes.title.text_frame.text.strip()
        if title_text:
            has_title = True

    if not has_title:
        for shape in slide.shapes:
            if shape.has_text_frame and shape.placeholder_format is not None:
                idx = shape.placeholder_format.idx
                if idx == 0:
                    if shape.text_frame.text.strip():
                        has_title = True
                        break

    if not has_title:
        findings.append(Finding(
            strand="L",
            severity="warning",
            location=loc,
            issue="Slide does not have a filled title.",
            evidence="Title placeholder is empty or missing.",
        ))


def _check_media(slide, loc, findings):
    detected = set()
    for shape in slide.shapes:
        if shape.shape_type in (
            MSO_SHAPE_TYPE.MEDIA,
            MSO_SHAPE_TYPE.EMBEDDED_OLE_OBJECT,
        ):
            detected.add(shape.name or "media object")
            findings.append(Finding(
                strand="C",
                severity="warning",
                location=loc,
                issue="Embedded media detected. Confirm that captions or a transcript are available.",
                evidence=f"Shape: {shape.name or 'media object'}",
            ))
            continue

        # Check XML for video/audio references not caught by shape_type
        if hasattr(shape, '_element'):
            el = shape._element
            el_xml = el.xml if hasattr(el, 'xml') else ""
            shape_name = shape.name or "media element"
            if shape_name not in detected:
                if "video" in el_xml.lower() or "audio" in el_xml.lower():
                    # Avoid false positives from shape names containing "video"
                    has_media_ref = False
                    for tag in ("videoFile", "audioFile", "MediaBookmark"):
                        if tag.lower() in el_xml.lower():
                            has_media_ref = True
                            break
                    # Also check for OLE or embedded media relationships
                    if not has_media_ref:
                        for tag in ("<a:videoFile", "<a:audioFile", "r:link", "r:embed"):
                            if tag in el_xml:
                                has_media_ref = True
                                break
                    if has_media_ref:
                        detected.add(shape_name)
                        findings.append(Finding(
                            strand="C",
                            severity="warning",
                            location=loc,
                            issue="Embedded media detected. Confirm that captions or a transcript are available.",
                            evidence=f"Shape: {shape_name}",
                        ))


def _check_text(slide, loc, findings):
    small_font_flagged = False
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue

        for para in shape.text_frame.paragraphs:
            if not small_font_flagged:
                for run in para.runs:
                    font = run.font
                    if font.size and font.size < Pt(18):
                        findings.append(Finding(
                            strand="E",
                            severity="tip",
                            location=loc,
                            issue=f"Text uses a small font size ({font.size.pt:.0f}pt). Consider 18pt or larger for readability.",
                            evidence=run.text[:80] if run.text else "(empty run)",
                        ))
                        small_font_flagged = True
                        break

            for run in para.runs:
                if run.hyperlink and run.hyperlink.address:
                    link_text = run.text.strip().lower()
                    if link_text in ("click here", "here", "link") or (
                        link_text.startswith("http://") or link_text.startswith("https://")
                    ):
                        findings.append(Finding(
                            strand="E",
                            severity="tip",
                            location=loc,
                            issue="Hyperlink uses generic or bare-URL text.",
                            evidence=f'Link text: "{run.text.strip()}"',
                        ))

        if shape.has_text_frame and shape.placeholder_format is not None:
            idx = shape.placeholder_format.idx
            if idx not in (0, 1):
                continue
            bullet_count = sum(
                1 for p in shape.text_frame.paragraphs if p.text.strip()
            )
            if bullet_count > 7:
                findings.append(Finding(
                    strand="E",
                    severity="tip",
                    location=loc,
                    issue=f"Text frame has {bullet_count} bullet points. Consider limiting to 7 or fewer per slide.",
                    evidence=f"Shape: {shape.name or 'text frame'}",
                ))
