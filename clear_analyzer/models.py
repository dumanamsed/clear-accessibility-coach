from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Finding:
    strand: str           # "C", "L", "E", "A", or "R"
    severity: str         # "critical", "warning", "tip"
    location: str         # e.g. "Slide 4", "Page 2", "Paragraph 3"
    issue: str            # one-sentence plain-English problem
    evidence: str         # the specific element that triggered it (truncated)
    suggestion: str = ""  # rewrite or improvement (populated by Claude pass)
    source: str = "rule"  # "rule" or "claude"

    def to_dict(self):
        return asdict(self)
