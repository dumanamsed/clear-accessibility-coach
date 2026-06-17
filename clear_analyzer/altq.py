"""Alt-text quality checks shared by the HTML, DOCX, and PPTX analyzers.

From CLEAR's "Alt Text for Images" self-assessment checklist:
  - "Alt text avoids phrases like 'Image of.'"  (screen readers already announce
    the element as an image, so the prefix is redundant)
  - "Alt text is concise."  CLEAR's implementation guidance: 125 characters or
    less for simple images; longer descriptions belong in extended text.
"""
from __future__ import annotations

import re

from .models import Finding

_REDUNDANT_PREFIX = re.compile(
    r"^\s*(an?\s+)?(image|picture|photo|photograph|graphic|icon|screenshot|pic)\s+(of|showing|depicting|that shows)\b",
    re.IGNORECASE,
)
_MAX_ALT_LEN = 150  # generous vs CLEAR's ~125; complex images need extended text


def alt_quality_findings(alt: str, location: str) -> list[Finding]:
    """Return concise CLEAR A-strand tips for an image that DOES have alt text
    (missing/filename/generic alt is handled separately by each analyzer)."""
    findings: list[Finding] = []
    if not alt:
        return findings
    a = alt.strip()
    if not a:
        return findings

    if _REDUNDANT_PREFIX.match(a):
        findings.append(Finding(
            strand="A",
            severity="tip",
            location=location,
            issue="Alt text starts with a redundant phrase like \"image of…\". Screen readers "
                  "already announce that it is an image, so describe the content directly.",
            evidence=a[:90],
        ))

    if len(a) > _MAX_ALT_LEN:
        findings.append(Finding(
            strand="A",
            severity="tip",
            location=location,
            issue=f"Alt text is long ({len(a)} characters). CLEAR recommends concise alt text "
                  f"(~125 characters); move detailed explanation into a caption or nearby text, "
                  f"and reserve extended descriptions for complex visuals.",
            evidence=a[:90] + "…",
        ))

    return findings
