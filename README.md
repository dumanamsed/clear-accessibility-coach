# CLEAR Accessibility Coach

A web application that helps Montgomery College faculty evaluate their instructional materials against the **CLEAR Framework** developed by Dr. Paul D. Miller, Ed.D., Co-Founder of the Universal Design Center at Montgomery College's Center for Teaching and Learning.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy the environment file and add your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the application
python app.py
```

Open [http://localhost:5465](http://localhost:5465) in your browser.

## Configuration

Edit `config.py` to set:
- `CTL_CONTACT_EMAIL` — replace the placeholder with the real CTL contact email
- `CLAUDE_MODEL` — the Claude model used for AI-powered review (default: `claude-sonnet-4-6`)

## Supported File Types

- `.pptx` (PowerPoint)
- `.docx` (Word)
- `.pdf`
- `.html` / `.txt`
- Paste text or HTML directly

## Privacy

Files are analyzed in memory only and never written to disk. No user accounts, no database, no sessions.
