# Vercel serverless entrypoint.
# Vercel's @vercel/python builder looks for a WSGI/ASGI `app` in this module.
# We add the project root to sys.path so the Flask app, templates, static
# assets, and clear_analyzer package all resolve correctly.
#
# NOTE: Vercel serverless functions cap request bodies at ~4.5 MB, which is
# smaller than this app's 25 MB design limit. Large uploads will be rejected
# on Vercel; for full-size uploads use a long-lived host (see render.yaml).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402  (Flask WSGI application object)
