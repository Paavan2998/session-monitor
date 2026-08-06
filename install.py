"""Install the session-monitor status line into Claude Code's settings.json.

    python install.py              # install for the current user (~/.claude)
    python install.py --project    # install for this repo only (./.claude)
    python install.py --uninstall  # remove the statusLine key again

Paths are resolved from this file's location and the running interpreter, so
the repo works wherever it is cloned.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
STATUSLINE = REPO_ROOT / "session_monitor" / "statusline.py"


def settings_path(project):
    base = REPO_ROOT if project else Path.home()
    return base / ".claude" / "settings.json"


def load(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON ({exc}). Fix or move it, then re-run.")


def save(path, settings):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(".json.bak")
        shutil.copy2(path, backup)
        print(f"backed up existing settings -> {backup}")
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        action="store_true",
        help="write to this repo's .claude/settings.json instead of the user's",
    )
    parser.add_argument(
        "--uninstall", action="store_true", help="remove the statusLine key"
    )
    args = parser.parse_args()

    path = settings_path(args.project)
    settings = load(path)

    if args.uninstall:
        if settings.pop("statusLine", None) is None:
            print(f"no statusLine configured in {path}; nothing to do")
            return
        save(path, settings)
        print(f"removed statusLine from {path}")
    else:
        if not STATUSLINE.exists():
            sys.exit(f"error: {STATUSLINE} is missing — is the repo complete?")
        # sys.executable rather than "python": the interpreter running this
        # installer is the one we know exists.
        settings["statusLine"] = {
            "type": "command",
            "command": f'"{sys.executable}" "{STATUSLINE}"',
            "padding": 0,
        }
        save(path, settings)
        print(f"installed statusLine into {path}")

    print("restart Claude Code to pick up the change.")


if __name__ == "__main__":
    main()
