"""Claude Code status line renderer.

Reads the session JSON that Claude Code pipes to stdin and prints two lines:

    [Opus 5 (1M context)] * xhigh | <dir> | <branch>
    <context bar> 36% | 61.2k | 49m 53s | 5h 12% · 7d 40%

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
RED = "\033[38;5;203m"
RESET = "\033[0m"

BAR_WIDTH = 20
GIT_CACHE_TTL = 5.0

# Soft budgets, from Claude Code's own "what's contributing to your limits"
# advice: context past ~150k and sessions past 8h are what burn the plan.
CONTEXT_WARN = 150_000
CONTEXT_HOT = 200_000
HOURS_WARN = 4
HOURS_HOT = 8


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


def context_tokens(data):
    """Tokens currently held in the window (input + both cache buckets)."""
    window = data.get("context_window", {})
    usage = window.get("current_usage") or {}
    if usage:
        return (
            usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        )
    return window.get("total_input_tokens", 0)


def thousands(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def tokens_segment(data):
    used = context_tokens(data)
    if used >= CONTEXT_HOT or data.get("exceeds_200k_tokens"):
        colour, flag = RED, " ⚠"
    elif used >= CONTEXT_WARN:
        colour, flag = ORANGE, " ⚠"
    else:
        colour, flag = GREEN, ""
    return f"{colour}{thousands(used)}{flag}{RESET}"


def limits_segment(data):
    limits = data.get("rate_limits") or {}
    five = limits.get("five_hour", {}).get("used_percentage")
    week = limits.get("seven_day", {}).get("used_percentage")
    if five is None and week is None:
        return None
    worst = max(v for v in (five, week) if v is not None)
    colour = RED if worst >= 90 else ORANGE if worst >= 70 else OLIVE
    parts = []
    if five is not None:
        parts.append(f"5h {round(five)}%")
    if week is not None:
        parts.append(f"7d {round(week)}%")
    return f"{colour}{' · '.join(parts)}{RESET}"


def duration(ms):
    total = int(ms // 1000)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def duration_segment(ms):
    hours = ms / 3_600_000
    if hours >= HOURS_HOT:
        colour, flag = RED, " ⚠"
    elif hours >= HOURS_WARN:
        colour, flag = ORANGE, ""
    else:
        colour, flag = WHITE, ""
    return f"⏱ {colour}{duration(ms)}{flag}{RESET}"


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
        tokens_segment(data),
        duration_segment(cost.get("total_duration_ms", 0)),
    ]
    limits = limits_segment(data)
    if limits:
        bottom.append(limits)

    print(sep.join(top))
    print(sep.join(bottom))


if __name__ == "__main__":
    main()
