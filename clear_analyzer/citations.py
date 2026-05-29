PRESSBOOK_BASE = "https://pressbooks.montgomerycollege.edu/clear"

STRAND_DEFINITIONS = {
    "C": {
        "name": "Caption Everything",
        "definition": "Video, audio, and embedded media must have accurate captions and transcripts.",
        "link": f"{PRESSBOOK_BASE}/chapter/c-caption-everything/",
    },
    "L": {
        "name": "Logical Layout",
        "definition": "Use proper heading hierarchy, slide titles, semantic structure, and predictable navigation.",
        "link": f"{PRESSBOOK_BASE}/chapter/l-logical-layout/",
    },
    "E": {
        "name": "Easy to Read",
        "definition": "Use readable fonts and sizes, sufficient color contrast, plain language, short paragraphs, and chunked content.",
        "link": f"{PRESSBOOK_BASE}/chapter/e-easy-to-read/",
    },
    "A": {
        "name": "Alt Text for Images",
        "definition": "Provide meaningful image descriptions; mark decorative images as such.",
        "link": f"{PRESSBOOK_BASE}/chapter/a-alt-text-for-images/",
    },
    "R": {
        "name": "Responsive Design",
        "definition": "Content works across screen sizes, devices, and assistive technology.",
        "link": f"{PRESSBOOK_BASE}/chapter/r-responsive-design/",
    },
}

PRESSBOOK_LINKS = {strand: info["link"] for strand, info in STRAND_DEFINITIONS.items()}

FRAMEWORK_CITATION = (
    "Grounded in the CLEAR Framework by Dr. Paul D. Miller, Ed.D., "
    "Montgomery College Center for Teaching and Learning."
)

STRAND_ORDER = ["C", "L", "E", "A", "R"]
