# lazy-commit

![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

> Because showing up every day is hard. Let your repo do it for you.

**lazy-commit** is a lightweight, zero-dependency Python tool that keeps your GitHub contribution graph green by generating realistic, human-looking development activity in a private repository.

No fake accounts. No API tokens. No sketchy browser extensions. Just real git commits, pulls, code reviews, and issue lifecycles — scheduled naturally so it never looks robotic.

---

## The Problem

You know that green contribution graph on GitHub? The one that makes you look like a disciplined developer? Yeah, that one.

Keeping it green means coding **every single day**. Life gets in the way. You miss a day. Then two. Then your graph looks like a Christmas tree that got hit by a truck.

**lazy-commit fixes that.** It runs quietly in the background, doing just enough realistic work to keep your graph alive — while you sleep, game, or do literally anything else.

---

## What It Actually Does

| Activity | How Often | What It Looks Like |
|----------|-----------|-------------------|
| **Commits** | 0-3 per day | Real commit messages, timestamps, file changes |
| **Pulls** | 0-3 per week | `git pull --ff-only` with logged results |
| **Code Reviews** | 0-3 per week | Markdown review notes on random modules |
| **Issues Opened** | 0-4 per 2 weeks | Full issue templates with complexity tracking |
| **Issues Closed** | 75-100% per month | Natural lifecycle, some drag to next month |
| **Rest Days** | 1-5 per month | Zero commits — because even devs need weekends |

Everything is committed to git. Everything has timestamps. Everything looks like you actually did the work. Because technically, the tool *is* doing the work.

---

## Why It Looks Real

Most "green graph" tools are dumb. They commit the same message at the same time every day. Any recruiter or engineer with two brain cells can spot that from orbit.

**lazy-commit is smarter:**

- **Multi-octave smooth noise** generates daily commit targets — some days busy, some days chill, some days zero
- **Probabilistic scheduling** — more likely to commit in the evening if behind target, just like a real dev procrastinating
- **Random events** — sometimes 3 issues spawn in one day (crunch time), sometimes nothing happens for days
- **Issue complexity** — issues take 1-3 months to close, some intentionally left hanging
- **40+ commit messages** — no repetitive "update" spam
- **Real review comments** — LGTM, nits, security notes, the whole deal

---

## Quick Start (5 Minutes)

### Step 1: Create a Private Repo

1. Go to [github.com/new](https://github.com/new)
2. Name it `lazy-commit` (or whatever)
3. **Set it to Private**
4. **Do NOT** initialize with README, .gitignore, or license
5. Click **Create repository**

### Step 2: Enable Private Contributions

1. Go to your GitHub profile: `github.com/YOURNAME`
2. Click **Contribution settings** (top-right of the green graph)
3. Check **Private contributions**
4. Save

> Without this, your private repo activity won't show on your graph. This is the magic switch.

### Step 3: Clone & Setup

```bash
git clone https://github.com/Kijanggoreng/lazy-commit.git
cd lazy-commit

# Drop all files from this repo into the folder
git config user.name "Your Name"
git config user.email "you@example.com"

git add .
git commit -m "init: lazy-commit activity tracker"
git push origin main
```

### Step 4: Install the Timer

```bash
chmod +x install.sh
./install.sh
```

This creates a **user-level systemd timer** (no root, no sudo) that runs 8 times per day with randomized delays.

### Step 5: Done

That's it. The timer runs automatically. Your graph fills itself. You go live your life.

---

## Usage

```bash
# Preview this month's schedule
python3 lazy_commit.py --plan

# Simulate without doing anything
python3 lazy_commit.py --dry-run

# Force one commit right now
python3 lazy_commit.py --force

# Commit but don't push to remote
python3 lazy_commit.py --no-push

# Try a different activity pattern
python3 lazy_commit.py --seed 502 --plan
```

---

## Seeds

| Seed | Vibe |
|------|------|
| `42` | Default — balanced |
| `502` | Chill — mostly 1 commit/day |
| `654` | Balanced — mix of 1s and 2s |
| `777` | Hustle mode — more busy days |

---

## How It Works Under the Hood

```
Timer fires (8x daily, random delay)
    |
    v
Load state from .lazy_state.json
    |
    v
Check if new month/week/biweek -> regenerate plans
    |
    v
For today:
    - Should we commit? (probabilistic, time-aware)
    - Should we pull? (weekly plan)
    - Should we review? (weekly plan)
    - Should we open an issue? (biweekly plan)
    - Should we close an issue? (monthly plan)
    |
    v
Execute actions -> git add -> git commit -> git push
    |
    v
Save updated state
```

All runtime data (state, logs, issues, reviews) lives in `.gitignore`. Only the engine and docs are committed to GitHub.

---

## Files

| File | What It Is |
|------|-----------|
| `lazy_commit.py` | The brain. 700+ lines of scheduling logic. |
| `install.sh` | One-command installer. Sets up systemd timer. |
| `DESCRIPTION.md` | Short project description for package indexes. |
| `.lazy_state.json` | Persistent schedule state *(gitignored)* |
| `activity.log` | Commit history log *(gitignored)* |
| `pulls.log` | Pull attempt log *(gitignored)* |
| `reviews.md` | Code review notes *(gitignored)* |
| `issues/open/` | Active issue files *(gitignored)* |
| `issues/closed/` | Resolved issue files *(gitignored)* |

---

## Uninstall

```bash
systemctl --user stop lazy_commit.timer
systemctl --user disable lazy_commit.timer
rm ~/.config/systemd/user/lazy_commit.*
systemctl --user daemon-reload
```

Your repo and GitHub history stay intact.

---

## Requirements

- Python 3.6+ (pure stdlib, zero dependencies)
- Git
- Linux with systemd (most distros)
- A GitHub account
- 5 minutes of your life

---

## License

MIT — see [LICENSE](LICENSE).

---

> *"The best code is the code you don't have to write. But if GitHub needs to see something, this'll do."*
