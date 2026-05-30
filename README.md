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

## Deployment

The repo ships with configs for two hosting options. In both cases, set `ANTHROPIC_API_KEY`
as an environment variable in the host's dashboard (never commit it).

### Render (recommended — supports full 25 MB uploads)

1. Push this repo to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint** and connect the repo.
3. Render reads `render.yaml`. Add your `ANTHROPIC_API_KEY` under the service's **Environment** settings.
4. Deploy. Render runs the app with `gunicorn app:app`.

### Vercel (works, but limited)

`vercel.json` and `api/index.py` are included. **Caveat:** Vercel serverless functions
cap request bodies at ~4.5 MB, below this app's 25 MB design limit, so large PowerPoint/PDF
uploads will be rejected. Pasted text and small files work fine.

```bash
vercel            # from the repo root, then set ANTHROPIC_API_KEY in the project settings
```
