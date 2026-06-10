PRESSBOOK_BASE = "https://pressbooks.montgomerycollege.edu/clear"

# Each CLEAR strand is mapped to one official Montgomery College brand color.
# "color" is the full-brightness brand accent, used ONLY for decorative,
# non-text elements (card borders, chip edges) which carry no WCAG contrast
# requirement. "ink" is a darkened same-hue variant that clears WCAG AA 4.5:1
# both as text on white and as a background under white text — use it anywhere
# the strand color touches text. (MC Blue, Edge Green, and Aspire Gold all
# fail 4.5:1 at full brightness; MC's own brand guide mandates AA contrast.)
STRAND_DEFINITIONS = {
    "C": {
        "name": "Caption Everything",
        "definition": "Video, audio, and embedded media must have accurate captions and transcripts.",
        "link": f"{PRESSBOOK_BASE}/chapter/c-caption-everything/",
        "color": "#0095C8",  # MC Blue
        "ink": "#006A94",    # 6.0:1 vs white
    },
    "L": {
        "name": "Logical Layout",
        "definition": "Use proper heading hierarchy, slide titles, semantic structure, and predictable navigation.",
        "link": f"{PRESSBOOK_BASE}/chapter/l-logical-layout/",
        "color": "#51237F",  # MC Purple
        "ink": "#51237F",    # already 11.1:1
    },
    "E": {
        "name": "Easy to Read",
        "definition": "Use readable fonts and sizes, sufficient color contrast, plain language, short paragraphs, and chunked content.",
        "link": f"{PRESSBOOK_BASE}/chapter/e-easy-to-read/",
        "color": "#FBA93E",  # Aspire Gold
        "ink": "#8A5A00",    # 5.9:1 vs white (full gold is 1.9:1 — never use as text)
    },
    "A": {
        "name": "Alt Text for Images",
        "definition": "Provide meaningful image descriptions; mark decorative images as such.",
        "link": f"{PRESSBOOK_BASE}/chapter/a-alt-text-for-images/",
        "color": "#00AC9B",  # Edge Green
        "ink": "#0A7065",    # 6.0:1 vs white
    },
    "R": {
        "name": "Responsive Design",
        "definition": "Content works across screen sizes, devices, and assistive technology.",
        "link": f"{PRESSBOOK_BASE}/chapter/r-responsive-design/",
        "color": "#B82A91",  # Future Fuchsia
        "ink": "#B82A91",    # already 5.6:1
    },
}

PRESSBOOK_LINKS = {strand: info["link"] for strand, info in STRAND_DEFINITIONS.items()}

FRAMEWORK_CITATION = (
    "Grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., "
    "Montgomery College Center for Teaching and Learning."
)

STRAND_ORDER = ["C", "L", "E", "A", "R"]
