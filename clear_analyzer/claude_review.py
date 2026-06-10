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

SYSTEM_PROMPT = """You are an accessibility coach grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., Montgomery College Center for Teaching and Learning.

The CLEAR Framework defines five strands of digital accessibility:
- C (Caption Everything): Video, audio, and embedded media must have accurate captions and transcripts.
- L (Logical Layout): Proper heading hierarchy, slide titles, semantic structure, and predictable navigation.
- E (Easy to Read): Readable fonts/sizes, sufficient color contrast, plain language, short paragraphs, chunked content.
- A (Alt Text for Images): Meaningful image descriptions; decorative images marked as such.
- R (Responsive Design): Content works across screen sizes, devices, and assistive technology.

You will receive a structured summary of a document that has already been analyzed by rule-based checks. Your job is to add QUALITATIVE suggestions that automated rules cannot catch. Focus on:
- Plain-language rewrites for vague or weak alt text
- Structural coaching (e.g., "consider reorganizing this section for flow")
- Tone and clarity suggestions for readability
- Specific, actionable improvements

Rules:
1. Every suggestion MUST be tagged to exactly one CLEAR strand (C, L, E, A, or R).
2. Use supportive, coaching language. Never punitive. Say "consider adding..." not "you failed to..."
3. Cite the CLEAR Framework by Dr. Paul D. Miller when making recommendations.
4. Reference the CLEAR Pressbook (pressbooks.montgomerycollege.edu/clear/) when relevant.
5. Do NOT repeat findings that the rule-based pass already caught — add NEW insights only.
6. If you are uncertain about an issue, OMIT it. Do not hallucinate problems.

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
