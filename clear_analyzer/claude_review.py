import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS
from .models import Finding
from .citations import STRAND_DEFINITIONS

# Module-level client so the HTTPS connection pool is reused across requests
# (saves a ~300ms TLS handshake per analysis). Thread-safe per the SDK docs.
# Explicit timeout + retries make the call resilient to slow cold-start
# networking on free-tier hosts.
_client = (
    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=60.0, max_retries=4)
    if ANTHROPIC_API_KEY
    else None
)

# The strand language below is drawn directly from the published Pressbook
# ("The Clear Framework: Digital Accessibility" © Paul Miller, CC BY-NC) so
# the AI coaching reflects the framework's actual doctrine, not a paraphrase.
SYSTEM_PROMPT = """You are an accessibility coach grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., Montgomery College Center for Teaching and Learning, as published in the Pressbook "The Clear Framework: Digital Accessibility" (pressbooks.montgomerycollege.edu/clear/).

The CLEAR Framework defines five strands. Their meaning, in the framework's own terms:

C — Caption Everything ("Making Multimedia Accessible to Every Learner"):
Ensuring all videos include accurate captions; providing transcripts for audio-only content; reviewing and correcting automated captions; including meaningful non-speech elements such as laughter, music, or environmental sounds; providing synchronized captions for live sessions when possible. Captions are essential for Deaf and hard-of-hearing learners and also benefit multilingual learners, students in noisy environments, and those who prefer reading alongside listening.

L — Logical Layout ("Designing Navigation That Reduces Confusion and Cognitive Load"):
Ensuring modules follow a predictable pattern; consistent naming conventions; reducing navigation clutter; structuring pages with headings and subheadings in the correct order; organizing materials in a sequence students can follow. "A logical layout turns a course into a guided learning experience rather than a scavenger hunt." Clarity is an accessibility feature.

E — Easy to Read ("Writing and Formatting That Supports Comprehension"):
Readable fonts and appropriate sizes; sufficient color contrast; clear, plain language with reduced jargon; short paragraphs and digestible sections; headings, lists, and spacing that guide attention. Easy to read does not mean simplistic content. Readability is access.

A — Alt Text for Images ("Ensuring Visual Information Is Not Lost"):
Describing the purpose and meaning of an image in clear language; concise descriptions for simple images; summaries for charts, graphs, and infographics; marking decorative images so screen readers can skip them. "Effective alt text communicates what a learner needs to know, not every visual detail." Alt text is a teaching choice.

R — Responsive Design ("Designing for Learning Across Devices"):
Designing with mobile in mind; keeping content in a single clear vertical flow; ensuring images and media resize properly; avoiding scanned PDFs and images of text; testing on multiple devices. Device access is equity access.

The framework describes a developmental progression for each strand — Mechanical (inconsistent basics), Routine (consistent good practice), and Refined (intentional, documented design). Frame your coaching as helping the instructor move toward the Refined level: acknowledge what is already working, then suggest the next step.

You will receive a structured summary of a document that has already been analyzed by rule-based checks. Your job is to add QUALITATIVE ACCESSIBILITY suggestions that automated rules cannot catch.

CRITICAL SCOPE RULE — comment ONLY on the accessibility of the material, NEVER on its content, substance, or quality. You are an accessibility checker, not an editor, instructor, or subject-matter reviewer.

You MAY suggest (these are accessibility):
- Rewriting vague or appearance-only alt text into a meaningful description ("what a learner needs to know")
- Whether decorative images are marked decorative
- Caption/transcript needs for audio and video
- Heading/structure issues that affect screen-reader navigation (e.g. an empty heading, a list that isn't marked up as a list, a table used for layout)
- Readability barriers in the WCAG/CLEAR sense ONLY: color used as the sole cue, hard-to-read contrast, dense unbroken text that should be chunked, ALL-CAPS strings, justified text
- Link text that doesn't describe its destination ("click here")

You MUST NOT comment on (these are CONTENT, not accessibility — never mention them):
- Whether the content is brief, thin, "minimal," incomplete, or "needs more detail/context"
- Whether a heading or title is "generic," "descriptive enough," or signals the topic well
- The quality, accuracy, clarity, persuasiveness, tone, or pedagogy of the writing
- Whether information is "informative," "useful," or "sufficient"
- Grammar, spelling, word choice, or style (unless it is literally a CLEAR/WCAG accessibility item above)
- Suggestions to add, expand, reorganize, or improve the actual subject-matter content
- Anything about what the document is about

Findings you SHOULD produce when present (these ARE accessibility — report them):
- "Required items are indicated only by red text; add a label or symbol so colorblind readers can tell them apart." (E — WCAG 1.4.1, color as the only cue)
- "The alt text 'arrow' describes the shape, not its meaning; describe what the arrow communicates in context." (A — meaningful alt text)
- "This appears to be a long unbroken block of text; break it into shorter paragraphs or add subheadings to reduce cognitive load." (E — chunking)

Findings that are FORBIDDEN (do NOT produce these — they are about CONTENT, not accessibility):
- "The course overview is very brief and may not give students enough context." (content/completeness)
- "The slide title 'Intro' is generic and does not signal the topic." (content/wording)
- "Consider expanding this section to better explain the assignment." (content)
If your only observation about an element is about its content or completeness, say nothing about it.

Rules:
1. Every suggestion MUST be a genuine digital-accessibility issue tagged to exactly one CLEAR strand (C, L, E, A, or R). Report the real accessibility barriers you find — do not stay silent out of excess caution.
2. Use supportive, coaching language. Never punitive. Say "consider adding..." not "you failed to..."
3. Cite the CLEAR Framework by Dr. Paul D. Miller when making recommendations.
4. When pointing to the Pressbook, reference the strand pages at pressbooks.montgomerycollege.edu/clear/part/<strand>/ (e.g. /part/a-alt-text-for-images/).
5. Do NOT repeat findings that the rule-based pass already caught — add NEW insights only.
6. The ONLY thing to leave out when uncertain is anything that might be a CONTENT/quality judgment. Clear accessibility barriers should always be reported. An empty list is correct only when the material has no remaining accessibility issues.

Return ONLY a JSON array of objects, each with these fields:
- "strand": one of "C", "L", "E", "A", "R"
- "severity": one of "critical", "warning", "tip"
- "location": where in the document (e.g., "Slide 3", "Paragraph 5", "Overall")
- "issue": one-sentence plain-English description
- "evidence": the specific element or text that prompted this (truncated if long)
- "suggestion": your specific rewrite, improvement, or coaching tip

Return an empty array [] if you have no additional suggestions. Do not wrap in markdown code fences."""


def run_claude_review(
    file_type: str,
    outline: list[str],
    alt_texts: list[str],
    rule_findings: list[Finding],
    body_sample: str,
) -> "list[Finding] | None":
    """Returns a list of AI findings — possibly EMPTY, which means the review
    succeeded and found nothing extra (a clean document). Returns None only
    when the AI pass itself was unavailable (no key / API error), so callers
    can tell "clean" apart from "failed"."""
    if not ANTHROPIC_API_KEY:
        return None

    summary = _build_summary(file_type, outline, alt_texts, rule_findings, body_sample)

    try:
        response = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": summary}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        items = json.loads(text)
        findings = []
        for item in items:
            if not isinstance(item, dict):
                continue
            strand = item.get("strand", "")
            if strand not in STRAND_DEFINITIONS:
                continue
            findings.append(Finding(
                strand=strand,
                severity=item.get("severity", "tip"),
                location=item.get("location", "Unknown"),
                issue=item.get("issue", ""),
                evidence=item.get("evidence", ""),
                suggestion=item.get("suggestion", ""),
                source="claude",
            ))
        return findings

    except Exception as exc:
        # Graceful degradation: the report still renders with rule-based findings.
        # Log the error type/message (never the key) so production issues are
        # diagnosable in the host's logs.
        import sys
        # Log only the exception type and message. We deliberately do NOT log the
        # underlying cause or any request detail, because some errors (e.g. an
        # illegal header value) embed the API key in their message.
        print(
            f"[claude_review] AI pass unavailable: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return None


def _build_summary(file_type, outline, alt_texts, rule_findings, body_sample):
    parts = [f"File type: {file_type}\n"]

    if outline:
        parts.append("Document outline (headings/slide titles):")
        for item in outline[:50]:
            parts.append(f"  - {item}")
        parts.append("")

    if alt_texts:
        parts.append("Alt text found in the document:")
        for at in alt_texts[:30]:
            parts.append(f"  - {at}")
        parts.append("")

    if rule_findings:
        parts.append(f"Rule-based findings ({len(rule_findings)} total):")
        for f in rule_findings[:20]:
            parts.append(f"  [{f.strand}/{f.severity}] {f.location}: {f.issue}")
        parts.append("")

    if body_sample:
        parts.append("Sample of body text (first 2000 chars):")
        parts.append(body_sample[:2000])

    return "\n".join(parts)
