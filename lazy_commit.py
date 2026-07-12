#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lazy-commit: automated git activity tracker

Generates realistic commit patterns, issue lifecycles, and review notes
for local git repositories. Useful for maintaining consistent project logs
and tracking development velocity over time.

Usage:
    python3 lazy_commit.py --plan           # preview this month's schedule
    python3 lazy_commit.py --dry-run        # simulate without writing
    python3 lazy_commit.py --force          # force a single commit now
    python3 lazy_commit.py --no-push        # commit only, skip remote sync
"""

import os
import sys
import json
import random
import subprocess
import argparse
from datetime import datetime
import calendar

# --- config -----------------------------------------------------------------

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(REPO_DIR, ".lazy_state.json")
ACTIVITY_FILE = os.path.join(REPO_DIR, "activity.log")
PULLS_FILE = os.path.join(REPO_DIR, "pulls.log")
REVIEWS_FILE = os.path.join(REPO_DIR, "reviews.md")
ISSUES_DIR = os.path.join(REPO_DIR, "issues")
ISSUES_OPEN_DIR = os.path.join(ISSUES_DIR, "open")
ISSUES_CLOSED_DIR = os.path.join(ISSUES_DIR, "closed")
DEFAULT_SEED = 42

COMMIT_MESSAGES = [
    "update activity log", "routine maintenance", "sync changes", "wip",
    "minor update", "cleanup", "refactor", "docs update", "progress",
    "checkpoint", "adjust configs", "fix formatting", "backup progress",
    "review and update", "daily sync", "tweak parameters", "update notes",
    "code polish", "organize files", "refresh data", "linting",
    "merge conflict resolved", "dependency update", "typo fix", "add comments",
    "optimize imports", "update README", "bump version", "security patch",
    "improve performance", "add test cases", "update dependencies",
    "fix edge case", "enhance logging", "update CI config", "code review",
    "restructure modules", "update docs", "patch bug", "improve error handling",
]

ISSUE_TITLES = [
    "Fix memory leak in {module}", "Refactor {module} for clarity",
    "Add {feature} support", "Update {module} documentation",
    "Investigate slow {module} performance", "Fix race condition in {module}",
    "Improve error handling in {module}", "Add validation for {feature}",
    "Clean up deprecated {module} code", "Optimize {module} query performance",
    "Fix null pointer in {module}", "Add unit tests for {module}",
    "Update {module} config schema", "Resolve deprecation warning in {module}",
    "Improve {module} logging output", "Fix timezone handling in {module}",
    "Add retry logic to {module}", "Refactor {module} state management",
    "Fix buffer overflow in {module}", "Update {module} dependencies",
]

ISSUE_BODIES = [
    "## Problem\n{module} shows inconsistent behavior under load.\n\n## Steps to reproduce\n1. Run stress test\n2. Observe memory growth\n\n## Expected\nStable memory usage.",
    "## Description\nThe {module} logic is getting hard to maintain. Consider splitting into smaller functions.\n\n## Acceptance Criteria\n- [ ] Refactor core logic\n- [ ] Add tests",
    "## Feature Request\nAdd support for {feature} in {module}.\n\n## Use Case\nUsers have requested this for better integration.",
    "## Bug Report\n{module} crashes when input is empty.\n\n## Environment\n- Version: latest\n- OS: Linux",
    "## Technical Debt\n{module} uses deprecated API. Need to migrate before next major release.\n\n## Timeline\nTarget: end of month.",
]

REVIEW_COMMENTS = [
    "LGTM! Consider adding a docstring here.",
    "Nit: variable name could be more descriptive.",
    "This logic looks solid. Maybe extract to a helper?",
    "Good catch on the edge case. Add a test for it?",
    "Performance looks fine, but watch the N+1 query pattern.",
    "Style: prefer early return here to reduce nesting.",
    "Security: validate this input before passing downstream.",
    "Nice refactor. Much cleaner than the previous version.",
    "Consider caching this result if called frequently.",
    "Typo in comment: `recieve` -> `receive`.",
]

MODULES = ["parser", "renderer", "auth", "db", "api", "cache", "worker", "queue", "scheduler", "notifier", "config", "logger", "validator", "router", "middleware"]
FEATURES = ["OAuth2", "WebSocket", "SSE", "GraphQL", "batch processing", "rate limiting", "RBAC", "audit logging", "health checks", "metrics"]

# --- helpers ----------------------------------------------------------------

def run_git(args, cwd=REPO_DIR, check=True, capture=False, timeout=30, env=None):
    cmd = ["git"] + args
    kwargs = {"cwd": cwd, "text": True, "timeout": timeout}
    if env is not None:
        kwargs["env"] = env
    if capture:
        kwargs["capture_output"] = True
    if check:
        kwargs["check"] = True
    return subprocess.run(cmd, **kwargs)

def git_configured():
    try:
        run_git(["config", "user.name"], check=True, capture=True)
        run_git(["config", "user.email"], check=True, capture=True)
        return True
    except Exception:
        return False

def has_remote():
    try:
        result = run_git(["remote"], capture=True)
        return bool(result.stdout.strip())
    except Exception:
        return False

def get_today_commits():
    try:
        result = run_git(["log", "--since=midnight", "--oneline"], capture=True)
        if not result.stdout.strip():
            return 0
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        return len(lines)
    except Exception:
        return 0

def current_year_week():
    """Return (year, week) tuple for proper year-boundary tracking."""
    iso = datetime.now().isocalendar()
    return (iso[0], iso[1])

def current_biweek():
    """Biweek 1-26, consistent year-round."""
    iso = datetime.now().isocalendar()
    # Week 1 always starts biweek 1
    return ((iso[1] - 1) // 2) + 1

def day_of_biweek():
    """Return day 1-14 within current biweek."""
    now = datetime.now()
    iso = now.isocalendar()
    week_in_year = iso[1]
    # Day of biweek: ((week - 1) % 2) * 7 + weekday
    return (((week_in_year - 1) % 2) * 7) + iso[2]

def ensure_dirs():
    for d in [ISSUES_DIR, ISSUES_OPEN_DIR, ISSUES_CLOSED_DIR]:
        os.makedirs(d, exist_ok=True)

# --- noise / scheduling -----------------------------------------------------

def smoothstep(t):
    return t * t * (3 - 2 * t)

def interp_noise(rng, day, grid_spacing, amplitude, grids):
    x = (day - 1) / grid_spacing
    n = int(x)
    f = smoothstep(x - n)
    if n + 1 >= len(grids):
        n = max(0, len(grids) - 2)
        f = 1.0
    return amplitude * (grids[n] * (1 - f) + grids[n + 1] * f)

def generate_commit_plan(year, month, seed, prev_plan=None):
    _, days_in_month = calendar.monthrange(year, month)
    rng = random.Random(year * 10000 + month * 100 + seed)

    num_rest = rng.randint(1, 5)
    rest_days = set()
    blocked = set()
    if prev_plan:
        last_day = max(int(k) for k in prev_plan.keys())
        if prev_plan.get(str(last_day), 1) == 0:
            blocked.add(1)

    attempts = 0
    while len(rest_days) < num_rest and attempts < 5000:
        candidate = rng.randint(1, days_in_month)
        if candidate in blocked or candidate in rest_days:
            attempts += 1
            continue
        if (candidate - 1) in rest_days or (candidate + 1) in rest_days:
            attempts += 1
            continue
        rest_days.add(candidate)
        blocked.add(candidate - 1)
        blocked.add(candidate + 1)
        attempts += 1

    gs = 3 + rng.randint(0, 2)
    ng = (days_in_month // gs) + 3
    g1 = [(rng.random() - 0.5) * 0.8 for _ in range(ng)]
    g2s = max(2, gs // 2)
    ng2 = (days_in_month // g2s) + 3
    g2 = [(rng.random() - 0.5) * 0.5 for _ in range(ng2)]
    g3 = [(rng.random() - 0.5) * 0.3 for _ in range(ng)]

    plan = {}
    for day in range(1, days_in_month + 1):
        sday = str(day)
        if day in rest_days:
            plan[sday] = 0
            continue
        val = 0.5
        val += interp_noise(rng, day, gs, 1.0, g1)
        val += interp_noise(rng, day, g2s, 1.0, g2)
        val += interp_noise(rng, day, gs, 1.0, g3)
        val = max(0.0, min(1.0, val))
        if val < 0.45:
            plan[sday] = 1
        elif val < 0.82:
            plan[sday] = 2
        else:
            plan[sday] = 3
    return plan

def generate_weekly_plan(year, week, seed, activity_name, max_per_week=3):
    # Use string hash for cross-platform deterministic seeding
    hash_input = f"{year}-{week}-{activity_name}"
    hash_val = sum(ord(c) * (31 ** i) for i, c in enumerate(hash_input)) & 0xFFFFFFFF
    rng = random.Random(year * 10000 + week * 100 + seed + hash_val)
    target = rng.randint(0, max_per_week)
    if target == 0:
        return {"target": 0, "days": []}
    pool = list(range(1, 8))
    rng.shuffle(pool)
    days = sorted(pool[:target])
    return {"target": target, "days": days}

def generate_issue_plan(year, biweek, seed):
    rng = random.Random(year * 10000 + biweek * 100 + seed + 777)
    random_event = rng.random() < 0.10

    if random_event:
        target_new = 3
        spawn_day = rng.randint(1, 14)
        spawn_days = [spawn_day]
    else:
        target_new = rng.randint(0, 4)
        if target_new == 0:
            spawn_days = []
        else:
            pool = list(range(1, 15))
            rng.shuffle(pool)
            spawn_days = sorted(pool[:target_new])

    return {
        "target_new": target_new,
        "spawn_days": spawn_days,
        "random_event": random_event,
        "done": 0
    }

def generate_issue_close_plan(year, month, seed, open_issues_count):
    rng = random.Random(year * 10000 + month * 100 + seed + 888)
    if open_issues_count == 0:
        return {"target_close": 0, "close_days": [], "done": 0}

    max_leave = min(2, open_issues_count)
    leave = rng.randint(0, max_leave)
    target_close = open_issues_count - leave

    if target_close <= 0:
        return {"target_close": 0, "close_days": [], "done": 0}

    _, dim = calendar.monthrange(year, month)
    pool = list(range(1, dim + 1))
    rng.shuffle(pool)
    close_days = sorted(pool[:target_close])

    return {"target_close": target_close, "close_days": close_days, "done": 0}

# --- state ------------------------------------------------------------------

def load_or_create_state(seed=DEFAULT_SEED, force_regen=False):
    now = datetime.now()
    year, month = now.year, now.month
    yw = current_year_week()
    biweek = current_biweek()

    if os.path.exists(STATE_FILE) and not force_regen:
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
        except (json.JSONDecodeError, IOError):
            state = {}
    else:
        state = {}

    changed = False

    # Commit plan: regenerate on month change
    if state.get("year") != year or state.get("month") != month or "commit_plan" not in state:
        prev_plan = state.get("commit_plan", {}) if state.get("month") == month - 1 and state.get("year") == year else {}
        state["year"] = year
        state["month"] = month
        state["commit_plan"] = generate_commit_plan(year, month, seed, prev_plan)
        changed = True

    if "pull_plan" not in state:
        state["pull_plan"] = {}
    if "review_plan" not in state:
        state["review_plan"] = {}

    # Weekly plan: use year-week tuple as key
    wkey = f"{yw[0]}-W{yw[1]:02d}"
    if wkey not in state["pull_plan"]:
        state["pull_plan"][wkey] = generate_weekly_plan(yw[0], yw[1], seed, "pull", 3)
        changed = True
    if wkey not in state["review_plan"]:
        state["review_plan"][wkey] = generate_weekly_plan(yw[0], yw[1], seed, "review", 3)
        changed = True

    if "issue_plan" not in state:
        state["issue_plan"] = {}

    bkey = f"{year}-B{biweek:02d}"
    if bkey not in state["issue_plan"]:
        state["issue_plan"][bkey] = generate_issue_plan(year, biweek, seed)
        state["last_spawn_date"] = None  # reset for new biweek
        changed = True

    if "issue_close_plan" not in state:
        state["issue_close_plan"] = {}

    mkey = f"{year}-M{month:02d}"
    if mkey not in state["issue_close_plan"]:
        open_count = len([i for i in state.get("issues", []) if i.get("status") == "open"])
        state["issue_close_plan"][mkey] = generate_issue_close_plan(year, month, seed, open_count)
        changed = True

    if "issues" not in state:
        state["issues"] = []
        changed = True
    if "next_issue_id" not in state:
        state["next_issue_id"] = 1
        changed = True
    if "log" not in state:
        state["log"] = []
        changed = True
    if "last_spawn_date" not in state:
        state["last_spawn_date"] = None
        changed = True

    if changed:
        save_state(state)

    return state

def save_state(state):
    # Cleanup old plan keys (older than 6 months)
    now = datetime.now()
    cutoff_year = now.year
    cutoff_month = now.month - 6
    if cutoff_month <= 0:
        cutoff_year -= 1
        cutoff_month += 12

    for key in list(state.get("pull_plan", {}).keys()):
        try:
            y = int(key.split("-W")[0])
            w = int(key.split("-W")[1])
            # Rough check: older than ~26 weeks
            if y < cutoff_year or (y == cutoff_year and w < (cutoff_month * 4)):
                del state["pull_plan"][key]
        except (ValueError, IndexError):
            pass

    for key in list(state.get("review_plan", {}).keys()):
        try:
            y = int(key.split("-W")[0])
            w = int(key.split("-W")[1])
            if y < cutoff_year or (y == cutoff_year and w < (cutoff_month * 4)):
                del state["review_plan"][key]
        except (ValueError, IndexError):
            pass

    for key in list(state.get("issue_plan", {}).keys()):
        try:
            y = int(key.split("-B")[0])
            if y < cutoff_year:
                del state["issue_plan"][key]
        except (ValueError, IndexError):
            pass

    for key in list(state.get("issue_close_plan", {}).keys()):
        try:
            y = int(key.split("-M")[0])
            if y < cutoff_year:
                del state["issue_close_plan"][key]
        except (ValueError, IndexError):
            pass

    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)

# --- actions ----------------------------------------------------------------

def make_commit(extra_msg=None, push=True, seed=DEFAULT_SEED):
    now = datetime.now()
    if not os.path.exists(ACTIVITY_FILE):
        with open(ACTIVITY_FILE, "w") as f:
            f.write("# Activity Log\n\n")

    verbs = ["update", "sync", "progress", "checkpoint", "refactor", "patch", "tweak", "polish", "clean", "optimize"]
    rng = random.Random(seed + now.year * 10000 + now.month * 100 + now.day * 10 + now.hour)
    entry = f"[{now.strftime('%Y-%m-%d %H:%M')}] {rng.choice(verbs)}\n"
    with open(ACTIVITY_FILE, "a") as f:
        f.write(entry)

    run_git(["add", "-A"])
    msg = extra_msg if extra_msg else rng.choice(COMMIT_MESSAGES)

    date_str = now.strftime("%Y-%m-%d %H:%M:%S %z")
    if not date_str.endswith("Z") and "+" not in date_str and "-" not in date_str[-5:]:
        date_str = now.strftime("%Y-%m-%d %H:%M:%S") + " +0000"

    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    # --allow-empty: commit even if nothing staged (e.g. only gitignored files changed)
    run_git(["commit", "--allow-empty", "-m", msg], check=True, env=env)

    if push and has_remote():
        try:
            run_git(["push"], check=False, capture=True, timeout=60)
        except Exception:
            pass
    return msg

def do_pull(state):
    now = datetime.now()
    if not has_remote():
        return "no remote"

    try:
        result = run_git(["pull", "--ff-only"], check=False, capture=True, timeout=60)
        status = "pulled" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        status = "timeout"
    except Exception as e:
        status = f"error: {e}"

    if not os.path.exists(PULLS_FILE):
        with open(PULLS_FILE, "w") as f:
            f.write("# Pull Log\n\n")

    entry = f"[{now.strftime('%Y-%m-%d %H:%M')}] {status}\n"
    with open(PULLS_FILE, "a") as f:
        f.write(entry)

    state["log"].append({
        "time": now.isoformat(),
        "action": "pull",
        "result": status
    })
    return status

def do_review(state, push=True, seed=DEFAULT_SEED):
    now = datetime.now()
    ensure_dirs()

    rng = random.Random(seed + now.year * 10000 + now.month * 100 + now.day * 10 + now.hour + 1)
    comment = rng.choice(REVIEW_COMMENTS)
    module = rng.choice(MODULES)

    entry = f"\n## Review {now.strftime('%Y-%m-%d %H:%M')} -- {module}\n\n{comment}\n"
    with open(REVIEWS_FILE, "a") as f:
        f.write(entry)

    msg = f"review: {module} -- {comment[:40]}..."
    make_commit(msg, push=push, seed=seed)

    state["log"].append({
        "time": now.isoformat(),
        "action": "review",
        "module": module,
        "result": "committed"
    })
    return msg

def create_issue(state, push=True, seed=DEFAULT_SEED):
    now = datetime.now()
    ensure_dirs()

    rng = random.Random(seed + now.year * 10000 + now.month * 100 + now.day * 10 + now.hour + 2)
    issue_id = state["next_issue_id"]
    state["next_issue_id"] = issue_id + 1

    title_template = rng.choice(ISSUE_TITLES)
    module = rng.choice(MODULES)
    feature = rng.choice(FEATURES)
    title = title_template.format(module=module, feature=feature)

    body_template = rng.choice(ISSUE_BODIES)
    body = body_template.format(module=module, feature=feature)

    complexity = rng.randint(1, 3)
    raw_month = state["month"] + (complexity - 1)
    planned_close_month = ((raw_month - 1) % 12) + 1

    issue = {
        "id": issue_id,
        "title": title,
        "created": now.isoformat(),
        "status": "open",
        "complexity": complexity,
        "planned_close_month": planned_close_month,
        "module": module
    }
    state["issues"].append(issue)

    issue_file = os.path.join(ISSUES_OPEN_DIR, f"ISSUE-{issue_id:03d}.md")
    with open(issue_file, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**ID:** ISSUE-{issue_id:03d}\n")
        f.write(f"**Status:** OPEN\n")
        f.write(f"**Created:** {now.strftime('%Y-%m-%d')}\n")
        f.write(f"**Complexity:** {complexity}\n")
        f.write(f"**Planned Close:** Month {planned_close_month}\n\n")
        f.write(body)

    msg = f"issue: open #{issue_id} -- {title[:50]}"
    make_commit(msg, push=push, seed=seed)

    state["log"].append({
        "time": now.isoformat(),
        "action": "issue_open",
        "issue_id": issue_id,
        "result": "committed"
    })
    return issue_id

def close_issue(state, issue_id, push=True, seed=DEFAULT_SEED):
    now = datetime.now()
    ensure_dirs()

    issue = None
    for i in state["issues"]:
        if i["id"] == issue_id:
            issue = i
            break

    if not issue or issue["status"] != "open":
        return None

    issue["status"] = "closed"
    issue["closed"] = now.isoformat()

    old_path = os.path.join(ISSUES_OPEN_DIR, f"ISSUE-{issue_id:03d}.md")
    new_path = os.path.join(ISSUES_CLOSED_DIR, f"ISSUE-{issue_id:03d}.md")

    if os.path.exists(old_path):
        with open(old_path, "r") as f:
            content = f.read()
        content = content.replace("**Status:** OPEN", f"**Status:** CLOSED\n**Closed:** {now.strftime('%Y-%m-%d')}")
        with open(new_path, "w") as f:
            f.write(content)
        os.remove(old_path)

    msg = f"issue: close #{issue_id} -- {issue['title'][:45]}"
    make_commit(msg, push=push, seed=seed)

    state["log"].append({
        "time": now.isoformat(),
        "action": "issue_close",
        "issue_id": issue_id,
        "result": "committed"
    })
    return issue_id

# --- orchestration ----------------------------------------------------------

def should_do_today(plan_dict, key, day_of_week):
    if key not in plan_dict:
        return False
    plan = plan_dict[key]
    if plan.get("target", 0) == 0:
        return False
    if plan.get("done", 0) >= plan.get("target", 0):
        return False
    return day_of_week in plan.get("days", [])

def process_day(state, seed, dry_run=False, push=True):
    now = datetime.now()
    today = str(now.day)
    weekday = now.isoweekday()
    dob = day_of_biweek()

    actions_taken = []

    # 1. commit
    plan = state["commit_plan"]
    target = plan.get(today, 1)
    current = get_today_commits()

    if current < target:
        remaining = target - current
        hours_left = max(0, 22 - now.hour)

        rng = random.Random(seed + now.year * 10000 + now.month * 100 + now.day * 10 + now.hour)
        if hours_left <= 0:
            should_commit = True
            reason = "last chance"
        else:
            runs_left = max(1, (hours_left + 1) // 2)
            prob = remaining / runs_left
            if now.hour >= 18:
                prob = min(0.90, prob * 2.0)
                reason = f"evening urgency ({prob:.0%})"
            elif now.hour >= 14:
                prob = min(0.75, prob * 1.4)
                reason = f"afternoon push ({prob:.0%})"
            else:
                reason = f"normal ({prob:.0%})"
            should_commit = rng.random() < prob

        if should_commit:
            if dry_run:
                actions_taken.append(f"[DRY] commit ({reason})")
            else:
                try:
                    msg = make_commit(push=push, seed=seed)
                    current += 1
                    actions_taken.append(f"Commit: \"{msg[:40]}...\" ({current}/{target})")
                except Exception as e:
                    actions_taken.append(f"Commit failed: {e}")
        else:
            actions_taken.append(f"Commit waiting... ({remaining} left, {reason})")
    else:
        actions_taken.append(f"Commit target reached ({current}/{target})")

    # 2. pull
    yw = current_year_week()
    wkey = f"{yw[0]}-W{yw[1]:02d}"
    if should_do_today(state["pull_plan"], wkey, weekday):
        if dry_run:
            actions_taken.append("[DRY] pull origin")
            state["pull_plan"][wkey]["done"] = state["pull_plan"][wkey].get("done", 0) + 1
        else:
            status = do_pull(state)
            state["pull_plan"][wkey]["done"] = state["pull_plan"][wkey].get("done", 0) + 1
            actions_taken.append(f"Pull: {status}")

    # 3. review
    if should_do_today(state["review_plan"], wkey, weekday):
        if dry_run:
            actions_taken.append("[DRY] code review")
            state["review_plan"][wkey]["done"] = state["review_plan"][wkey].get("done", 0) + 1
        else:
            msg = do_review(state, push=push, seed=seed)
            state["review_plan"][wkey]["done"] = state["review_plan"][wkey].get("done", 0) + 1
            actions_taken.append(f"Review: {msg[:50]}...")

    # 4. issue spawn (max once per day)
    bkey = f"{now.year}-B{current_biweek():02d}"
    biweek_plan = state["issue_plan"].get(bkey, {})
    today_str = now.strftime("%Y-%m-%d")
    already_spawned = state.get("last_spawn_date") == today_str

    if not already_spawned and biweek_plan.get("done", 0) < biweek_plan.get("target_new", 0):
        should_spawn = False
        if biweek_plan.get("random_event", False):
            spawn_days = biweek_plan.get("spawn_days", [])
            if spawn_days and dob == spawn_days[0]:
                should_spawn = True
        else:
            if dob in biweek_plan.get("spawn_days", []):
                should_spawn = True

        if should_spawn:
            if biweek_plan.get("random_event", False):
                to_spawn = biweek_plan["target_new"] - biweek_plan.get("done", 0)
                for _ in range(to_spawn):
                    if dry_run:
                        actions_taken.append("[DRY] spawn issue (random event)")
                    else:
                        iid = create_issue(state, push=push, seed=seed)
                        actions_taken.append(f"Issue #{iid} created (random event)")
                    biweek_plan["done"] = biweek_plan.get("done", 0) + 1
            else:
                if dry_run:
                    actions_taken.append("[DRY] spawn issue")
                else:
                    iid = create_issue(state, push=push, seed=seed)
                    actions_taken.append(f"Issue #{iid} created")
                biweek_plan["done"] = biweek_plan.get("done", 0) + 1
            if not dry_run:
                state["last_spawn_date"] = today_str

    # 5. issue close
    mkey = f"{now.year}-M{now.month:02d}"
    close_plan = state["issue_close_plan"].get(mkey, {})
    if now.day in close_plan.get("close_days", []) and close_plan.get("done", 0) < close_plan.get("target_close", 0):
        open_issues = [i for i in state["issues"] if i.get("status") == "open"]
        if open_issues:
            eligible = [i for i in open_issues if i.get("planned_close_month", 999) <= now.month]
            if not eligible:
                eligible = open_issues
            to_close = eligible[0]
            if dry_run:
                actions_taken.append(f"[DRY] close issue #{to_close['id']}")
            else:
                close_issue(state, to_close["id"], push=push, seed=seed)
                actions_taken.append(f"Issue #{to_close['id']} closed")
            close_plan["done"] = close_plan.get("done", 0) + 1

    return actions_taken

def print_full_plan(state):
    year, month = state["year"], state["month"]
    _, dim = calendar.monthrange(year, month)

    print(f"\nSchedule: {calendar.month_name[month]} {year}")
    print("=" * 60)

    print("\nCommit Plan:")
    rest_count = 0
    total = 0
    for day in range(1, dim + 1):
        sday = str(day)
        count = state["commit_plan"].get(sday, 1)
        bar = "#" * count if count > 0 else "-"
        marker = " (rest)" if count == 0 else ""
        print(f"  Day {day:2d}: {bar:<3} ({count}){marker}")
        if count == 0:
            rest_count += 1
        total += count
    print(f"  -> {rest_count} rest days, {total} total commits")

    print("\nPull Plan (per week):")
    for wkey, plan in sorted(state["pull_plan"].items(), key=lambda x: x[0]):
        days = plan.get("days", [])
        day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        dstr = ", ".join(day_names[d-1] for d in days) if days else "none"
        print(f"  Week {wkey}: {plan.get('target', 0)}x -- {dstr}")

    print("\nReview Plan (per week):")
    for wkey, plan in sorted(state["review_plan"].items(), key=lambda x: x[0]):
        days = plan.get("days", [])
        day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        dstr = ", ".join(day_names[d-1] for d in days) if days else "none"
        print(f"  Week {wkey}: {plan.get('target', 0)}x -- {dstr}")

    print("\nIssue Plan:")
    for bkey, plan in sorted(state["issue_plan"].items(), key=lambda x: x[0]):
        ev = " [RANDOM EVENT]" if plan.get("random_event") else ""
        print(f"  Biweek {bkey}: {plan.get('target_new', 0)} new{ev}")

    for mkey, plan in sorted(state["issue_close_plan"].items(), key=lambda x: x[0]):
        print(f"  Month {mkey}: close {plan.get('target_close', 0)} issues")

    open_issues = [i for i in state.get("issues", []) if i.get("status") == "open"]
    closed_issues = [i for i in state.get("issues", []) if i.get("status") == "closed"]
    print(f"\nIssue inventory: {len(open_issues)} open, {len(closed_issues)} closed")
    for i in open_issues[:5]:
        print(f"  #{i['id']:03d}: {i['title'][:50]}... (close month {i.get('planned_close_month', '?')})")
    for i in closed_issues[-3:]:
        print(f"  #{i['id']:03d}: {i['title'][:50]}...")
    print()

# --- main -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="lazy-commit: automated git activity tracker"
    )
    parser.add_argument("--plan", action="store_true", help="Show full schedule")
    parser.add_argument("--force", action="store_true", help="Force one commit now")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without executing")
    parser.add_argument("--no-push", action="store_true", help="Skip remote push/pull")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed (default: 42)")
    parser.add_argument("--regenerate", action="store_true", help="Wipe state and regenerate")
    args = parser.parse_args()

    os.chdir(REPO_DIR)
    ensure_dirs()

    if not git_configured():
        print("Git not configured. Set user.name and user.email first.")
        print('  git config --global user.name "Your Name"')
        print('  git config --global user.email "you@example.com"')
        sys.exit(1)

    if args.regenerate and os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print("Old state removed. Regenerating...")

    state = load_or_create_state(seed=args.seed, force_regen=args.regenerate)

    if args.plan:
        print_full_plan(state)
        return

    if args.force:
        if args.dry_run:
            print("[DRY-RUN] Force commit")
        else:
            msg = make_commit(push=not args.no_push, seed=args.seed)
            print(f'Force committed: "{msg}"')
        return

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    actions = process_day(state, args.seed, dry_run=args.dry_run, push=not args.no_push)
    for a in actions:
        print(a)

    if not args.dry_run:
        save_state(state)
    else:
        print("\n[DRY-RUN] state not saved")

if __name__ == "__main__":
    main()
