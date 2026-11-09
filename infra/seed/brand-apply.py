"""Write the Proliv droplet logo + favicon set into /app/data/webapp-logo.

Runs INSIDE remnawave-minishop-backend (python /tmp/brand-apply.py) and calls
the same helpers as the admin Appearance upload, so paths/digests are
identical to an admin UI upload. Prints the URLs to persist as overrides.
"""

import json
from pathlib import Path

from bot.app.web.admin_api_impl.themes import _write_favicon_set, _write_uploaded_logo

body = Path("/tmp/proliv-brand/proliv-drop.png").read_bytes()
logo_url = _write_uploaded_logo(body, "image/png", "proliv-drop.png")
favicon = _write_favicon_set(body, "image/png", "proliv-drop.png")
print(json.dumps({"logo_url": logo_url, "favicon": favicon}, indent=2))
