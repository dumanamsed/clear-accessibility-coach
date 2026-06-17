PRESSBOOK_BASE = "https://pressbooks.montgomerycollege.edu/clear"

# Each CLEAR strand is mapped to one official Montgomery College brand color.
# "color" is the full-brightness brand accent, used ONLY for decorative,
# non-text elements (card borders, chip edges) which carry no WCAG contrast
# requirement. "ink" is a darkened same-hue variant that clears WCAG AA 4.5:1
# both as text on white and as a background under white text — use it anywhere
# the strand color touches text. (MC Blue, Edge Green, and Aspire Gold all
# fail 4.5:1 at full brightness; MC's own brand guide mandates AA contrast.)
# Strand names, definitions, and links are drawn from the published Pressbook
# ("The Clear Framework: Digital Accessibility" © Paul Miller, CC BY-NC).
# Definitions use each strand's official subtitle and signature line. Links
# point to the strand introduction pages, which live at /part/<slug>/ —
# NOT /chapter/<slug>/ (those resolve to self-assessment quizzes or 404).
STRAND_DEFINITIONS = {
    "C": {
        "name": "Caption Everything",
        "definition": "Making multimedia accessible to every learner: accurate captions for all video, transcripts for audio-only content, and meaningful sound cues included.",
        "link": f"{PRESSBOOK_BASE}/part/c-caption-everything/",
        "color": "#0095C8",  # MC Blue
        "ink": "#006A94",    # 6.0:1 vs white
    },
    "L": {
        "name": "Logical Layout",
        "definition": "Designing navigation that reduces confusion and cognitive load: predictable structure, headings in the correct order, and consistent organization. Clarity is an accessibility feature.",
        "link": f"{PRESSBOOK_BASE}/part/l-logical-layout/",
        "color": "#51237F",  # MC Purple
        "ink": "#51237F",    # already 11.1:1
    },
    "E": {
        "name": "Easy to Read",
        "definition": "Writing and formatting that supports comprehension: readable fonts, sufficient contrast, plain language, and short, digestible sections. Readability is access.",
        "link": f"{PRESSBOOK_BASE}/part/e-easy-to-read/",
        "color": "#FBA93E",  # Aspire Gold
        "ink": "#8A5A00",    # 5.9:1 vs white (full gold is 1.9:1 — never use as text)
    },
    "A": {
        "name": "Alt Text for Images",
        "definition": "Ensuring visual information is not lost: meaningful descriptions for instructional images, with decorative images marked so screen readers can skip them. Alt text is a teaching choice.",
        "link": f"{PRESSBOOK_BASE}/part/a-alt-text-for-images/",
        "color": "#00AC9B",  # Edge Green
        "ink": "#0A7065",    # 6.0:1 vs white
    },
    "R": {
        "name": "Responsive Design",
        "definition": "Designing for learning across devices: content that flows cleanly on phones and laptops alike, resizes properly, and avoids images of text. Device access is equity access.",
        "link": f"{PRESSBOOK_BASE}/part/r-responsive-design/",
        "color": "#B82A91",  # Future Fuchsia
        "ink": "#B82A91",    # already 5.6:1
    },
}

PRESSBOOK_LINKS = {strand: info["link"] for strand, info in STRAND_DEFINITIONS.items()}

# Requirements from each strand's CLEAR self-assessment checklist that an
# automated tool CANNOT verify from a file alone (they need human judgment or
# live testing). Surfacing them keeps the full CLEAR requirement set visible so
# faculty don't mistake "no automated findings" for "fully accessible."
MANUAL_CHECKS = {
    "C": [
        "Captions are accurate and edited for clarity, spelling, and timing — not just auto-generated.",
        "Audio-only content (podcasts, narration) has a transcript.",
        "Meaningful non-speech audio (music, sound effects) is described, and speakers are identified.",
        "Live sessions include captions when possible.",
    ],
    "L": [
        "Reading and focus order follow a logical, intuitive path.",
        "Everything is operable by keyboard alone, and the keyboard focus indicator is visible.",
        "Interactive elements meet the 24×24 px minimum target size.",
        "Any drag-based interaction has a non-drag alternative.",
    ],
    "E": [
        "Text can be resized to 200% without losing content or breaking layout.",
        "Information is never conveyed by color alone (also use text, icons, or labels).",
        "A dark-mode or high-contrast option is offered where the platform supports it.",
    ],
    "A": [
        "Each description conveys the image's purpose and meaning, not just its appearance.",
        "Charts, graphs, and infographics have a text summary or extended description of the data.",
        "Purely decorative images are intentionally marked decorative so screen readers skip them.",
    ],
    "R": [
        "Tested on multiple devices — desktop, tablet, and phone.",
        "Content reflows with no horizontal scrolling on small screens.",
        "Links and buttons are easy to see and tap on touch screens.",
        "Shared in accessible formats (structured Word, tagged PDF).",
    ],
}

FRAMEWORK_CITATION = (
    "Grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., "
    "Montgomery College Center for Teaching and Learning."
)

STRAND_ORDER = ["C", "L", "E", "A", "R"]
