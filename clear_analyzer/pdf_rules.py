from io import BytesIO
import fitz
from .models import Finding


def analyze_pdf(file_bytes: bytes) -> list[Finding]:
    findings = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    _check_tagged(doc, findings)
    _check_scanned(doc, findings)
    _check_title(doc, findings)
    _check_images(doc, findings)

    doc.close()
    return findings


def _check_tagged(doc, findings):
    catalog = doc.pdf_catalog()
    is_tagged = False

    # Check MarkInfo dictionary for Marked=true
    try:
        markinfo = doc.xref_get_key(catalog, "MarkInfo")
        if markinfo and markinfo[0] != "null":
            if "true" in markinfo[1].lower():
                is_tagged = True
    except Exception:
        pass

    # Also check for StructTreeRoot as a fallback
    if not is_tagged:
        try:
            struct_tree = doc.xref_get_key(catalog, "StructTreeRoot")
            if struct_tree and struct_tree[0] != "null":
                is_tagged = True
        except Exception:
            pass

    if not is_tagged:
        findings.append(Finding(
            strand="L",
            severity="critical",
            location="Entire document",
            issue="PDF is not tagged. Screen readers and assistive technology cannot parse its structure.",
            evidence="No PDF tag structure or MarkInfo dictionary found.",
        ))


def _check_scanned(doc, findings):
    if len(doc) == 0:
        return

    pages_without_text = 0
    total_pages = len(doc)

    for page in doc:
        text = page.get_text("text").strip()
        if not text:
            pages_without_text += 1

    if pages_without_text == total_pages and total_pages > 0:
        findings.append(Finding(
            strand="A",
            severity="critical",
            location="Entire document",
            issue="This appears to be a scanned PDF with no extractable text. Screen readers cannot read it.",
            evidence=f"All {total_pages} page(s) contain no selectable text.",
        ))
        findings.append(Finding(
            strand="L",
            severity="critical",
            location="Entire document",
            issue="Scanned PDF has no text layer. Consider running OCR to make the content accessible.",
            evidence=f"All {total_pages} page(s) contain no selectable text.",
        ))


def _check_title(doc, findings):
    metadata = doc.metadata
    title = metadata.get("title", "").strip() if metadata else ""
    if not title:
        findings.append(Finding(
            strand="L",
            severity="tip",
            location="Document metadata",
            issue="PDF has no document title set in its metadata.",
            evidence="Title field is empty or missing.",
        ))


def _check_images(doc, findings):
    """Check each page for images and whether surrounding text provides context."""
    for page_num, page in enumerate(doc, 1):
        image_list = page.get_images(full=True)
        if not image_list:
            continue

        page_text = page.get_text("text").strip()
        page_text_lower = page_text.lower()

        for img_idx, img in enumerate(image_list, 1):
            # img tuple: (xref, smask, width, height, bpc, colorspace, alt_text_or_empty, name, filter)
            img_name = img[7] if len(img) > 7 else f"image_{img_idx}"
            img_width = img[2] if len(img) > 2 else 0
            img_height = img[3] if len(img) > 3 else 0

            # Skip tiny images (likely decorative lines, bullets, icons)
            if img_width < 50 and img_height < 50:
                continue

            # If the page has no text at all, the image has no context
            if not page_text:
                findings.append(Finding(
                    strand="A",
                    severity="warning",
                    location=f"Page {page_num}",
                    issue="Image found on a page with no surrounding text to provide context.",
                    evidence=f"Image: {img_name} ({img_width}x{img_height}px)",
                ))
            # Check if the page has very little text relative to having images
            elif len(page_text.split()) < 10 and len(image_list) > 0:
                findings.append(Finding(
                    strand="A",
                    severity="warning",
                    location=f"Page {page_num}",
                    issue="Image found on a page with very little text. Consider adding descriptive context.",
                    evidence=f"Image: {img_name} ({img_width}x{img_height}px), page has {len(page_text.split())} words",
                ))
