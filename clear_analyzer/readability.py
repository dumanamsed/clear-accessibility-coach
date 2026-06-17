"""Plain-language / readability analysis for the CLEAR "Easy to Read" strand.

CLEAR's Easy to Read self-assessment lists, as an explicit checklist item:
    "Readability tools used (Flesch-Kincaid target 70+ Reading Ease;
     Grade Level 8 or below)."
and its implementation guidance: "Keep sentences under 15-25 words."

This module computes those exact metrics on a document's body text so the tool
can surface them, rather than leaving readability entirely to manual judgment.
It is deliberately gentle (coaching, not punitive): it only speaks up when text
is clearly hard to read, and it reports the actual scores so faculty can decide.
"""
from __future__ import annotations

import re

from .models import Finding

_SENTENCE_SPLIT = re.compile(r"[.!?]+(?:\s|$)")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_VOWEL_GROUPS = re.compile(r"[aeiouy]+")


def _count_syllables(word: str) -> int:
    """Heuristic syllable count — good enough for aggregate readability scores."""
    w = word.lower()
    groups = _VOWEL_GROUPS.findall(w)
    count = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee", "ie")) and count > 1:
        count -= 1  # silent final e
    return max(1, count)


def _split_sentences(text: str):
    parts = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return parts


def analyze_readability(text: str) -> list[Finding]:
    """Return Easy-to-Read findings about plain-language / sentence length.

    Skips short or non-prose text (slide fragments, tables) where the scores
    would be meaningless."""
    findings: list[Finding] = []
    if not text:
        return findings

    sentences = _split_sentences(text)
    words = _WORD_RE.findall(text)
    if len(words) < 60 or len(sentences) < 3:
        return findings  # too little prose to score meaningfully

    syllables = sum(_count_syllables(w) for w in words)
    n_words, n_sent = len(words), len(sentences)
    wps = n_words / n_sent          # words per sentence
    spw = syllables / n_words       # syllables per word

    flesch_ease = 206.835 - 1.015 * wps - 84.6 * spw
    fk_grade = 0.39 * wps + 11.8 * spw - 15.59

    # Only flag when clearly outside CLEAR's targets (70+ ease, grade <=8), with
    # generous slack so ordinary academic prose isn't nagged on every upload.
    if flesch_ease < 50 or fk_grade > 12:
        findings.append(Finding(
            strand="E",
            severity="tip",
            location="Overall document",
            issue=(
                f"Readability check: Flesch Reading Ease {flesch_ease:.0f} "
                f"(CLEAR target 70+) and grade level {fk_grade:.0f} (CLEAR target 8 or below). "
                f"Consider plainer language and shorter sentences where the content allows."
            ),
            evidence=f"{n_words} words, {n_sent} sentences, ~{wps:.0f} words/sentence on average.",
        ))

    # Very long individual sentences (CLEAR: keep sentences under 15-25 words).
    long_sentences = [s for s in sentences if len(_WORD_RE.findall(s)) > 35]
    if long_sentences:
        sample = long_sentences[0]
        findings.append(Finding(
            strand="E",
            severity="tip",
            location="Overall document",
            issue=(
                f"{len(long_sentences)} very long sentence"
                f"{'s' if len(long_sentences) != 1 else ''} (over 35 words) detected. "
                f"CLEAR's Easy to Read guidance recommends keeping sentences under 15–25 words; "
                f"long sentences raise cognitive load."
            ),
            evidence=(sample[:120] + "…") if len(sample) > 120 else sample,
        ))

    return findings
