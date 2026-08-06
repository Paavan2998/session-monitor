# session-monitor

Monitors token usage in session and auto resumes the task when session limit resets.

## Status line

Renders Claude Code's session state as a two-line status bar:

```
[Opus 5 (1M context)] | ⚡ xhigh | 📁 session-monitor | 🌿 main
███████░░░░░░░░░░░░░ 36% | $25.58 | ⏱ 49m 53s
```

### Install

Requires Python 3.9+ and Claude Code.

```
git clone <this repo>
cd session-monitor
python install.py
```

Then restart Claude Code.

The installer writes a `statusLine` entry into `~/.claude/settings.json`, backing up
any existing file to `settings.json.bak` first. All other settings are preserved.

| Command | Effect |
| --- | --- |
| `python install.py` | install for the current user (`~/.claude/settings.json`) |
| `python install.py --project` | install for this repo only (`./.claude/settings.json`) |
| `python install.py --uninstall` | remove the `statusLine` entry |

Paths are resolved from the repo's location and the interpreter you run the
installer with, so no editing is needed after cloning.

## Auto-resume

Not implemented yet.
