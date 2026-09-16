# session-monitor

Monitors token usage in session and auto resumes the task when session limit resets.

## Status line

Renders Claude Code's session state as a two-line status bar:

```
[Opus 5 (1M context)] | ⚡ xhigh | 📁 session-monitor | 🌿 main
███████░░░░░░░░░░░░░ 36% | 61.2k | ⏱ 49m 53s | 5h 12% · 7d 40%
```

The bottom row tracks what actually consumes the plan: context used
(bar + percentage of the window, then absolute tokens), session wall time,
and the rolling 5-hour / 7-day rate-limit usage.

Tokens turn amber at 150k and red at 200k; the clock turns amber at 4h and
red at 8h — the two patterns Claude Code's own usage breakdown flags as the
expensive ones. The rate-limit segment is amber from 70% and red from 90%,
and is omitted when Claude Code doesn't report limits (e.g. API-key billing).
Thresholds live at the top of `session_monitor/statusline.py`.

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
