import os
from dotenv import load_dotenv

load_dotenv()

CTL_CONTACT_EMAIL = "CTL@montgomerycollege.edu"  # PLACEHOLDER — replace with real CTL email

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 2000

MAX_UPLOAD_SIZE_MB = 25
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {".pptx", ".docx", ".pdf", ".html", ".htm", ".txt"}

FLASK_PORT = 5465
