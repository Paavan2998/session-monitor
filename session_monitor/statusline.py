"""Claude Code status line renderer.

Reads the session JSON that Claude Code pipes to stdin and prints two lines:

    [Opus 5 (1M context)] * xhigh | <dir> | <branch>
    <context bar> 36% | $25.58 | 49m 53s

Wired up via settings.json -> statusLine.
"""

import json
import os
import subprocess
import sys
import time

# 256-colour palette, matched to the reference screenshot.
TEAL = "\033[38;5;80m"
ORANGE = "\033[38;5;179m"
GREY = "\033[38;5;242m"
WHITE = "\033[38;5;253m"
OLIVE = "\033[38;5;142m"
DARK = "\033[38;5;238m"
GREEN = "\033[38;5;114m"
RESET = "\033[0m"

BAR_WIDTH = 20
GIT_CACHE_TTL = 5.0


def git_branch(cwd, session_id):
    """Current branch name, cached per session so we don't shell out every tick."""
    cache = os.path.join(
        os.environ.get("TEMP", os.path.expanduser("~")),
        f"claude-statusline-git-{session_id}.txt",
    )
    try:
        if time.time() - os.path.getmtime(cache) < GIT_CACHE_TTL:
            with open(cache, encoding="utf-8") as fh:
                return fh.read().strip() or None
    except OSError:
        pass

    try:
        branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        branch = ""

    try:
        with open(cache, "w", encoding="utf-8") as fh:
            fh.write(branch)
    except OSError:
        pass
    return branch or None


def model_label(data):
    """e.g. "Opus 5 (1M context)" — the 1M suffix comes from the window size."""
    name = data.get("model", {}).get("display_name") or "Claude"
    size = data.get("context_window", {}).get("context_window_size") or 0
    if size >= 1_000_000:
        name += " (1M context)"
    return name


def context_bar(pct):
    filled = round(BAR_WIDTH * pct / 100)
    return f"{OLIVE}{'█' * filled}{DARK}{'░' * (BAR_WIDTH - filled)}{RESET}"


def duration(ms):
    total = int(ms // 1000)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    cwd = data.get("workspace", {}).get("current_dir") or data.get("cwd") or "."
    sep = f" {GREY}|{RESET} "

    top = [
        f"{TEAL}[{model_label(data)}]{RESET}",
        f"{ORANGE}⚡ {data.get('effort', {}).get('level', 'medium')}{RESET}",
        f"📁 {WHITE}{os.path.basename(cwd.rstrip('/\\')) or cwd}{RESET}",
    ]
    branch = git_branch(cwd, data.get("session_id", "default"))
    if branch:
        top.append(f"🌿 {WHITE}{branch}{RESET}")

    cost = data.get("cost", {})
    pct = data.get("context_window", {}).get("used_percentage") or 0
    bottom = [
        f"{context_bar(pct)} {OLIVE}{round(pct)}%{RESET}",
        f"{GREEN}${cost.get('total_cost_usd', 0):.2f}{RESET}",
        f"⏱ {WHITE}{duration(cost.get('total_duration_ms', 0))}{RESET}",
    ]

    print(sep.join(top))
    print(sep.join(bottom))


if __name__ == "__main__":
    main()
