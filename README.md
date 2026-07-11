# lazy-commit

Automated git activity tracker for solo developers and side projects.

## What It Does

Keeps your project history consistent with periodic commits, issue tracking, and review notes. Useful for:

- Maintaining a daily development log
- Tracking issue lifecycles locally
- Generating realistic commit patterns for portfolio repos

## Features

- **Commit scheduling** — 0-3 commits/day with natural variance and rest days
- **Issue lifecycle** — open, track complexity, close over time
- **Code review notes** — append review comments as tracked markdown
- **Deterministic seeds** — reproduce the same schedule with `--seed`
- **Remote sync** — auto push/pull when a remote is configured

## Quick Start (Private Repo on GitHub)

### Step 1: Create a Private Repo on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Name it whatever you want (e.g. `lazy-commit`)
3. Set it to **Private**
4. Do NOT initialize with README, .gitignore, or license (we bring our own)
5. Click **Create repository**

### Step 2: Enable Private Contributions on Your Profile

1. Go to your GitHub profile: `github.com/YOURNAME`
2. Click the **Contribution settings** dropdown (top-right of the contribution graph)
3. Check **Private contributions** — this makes private repo activity visible on your green graph
4. Save

### Step 3: Clone & Setup

```bash
# clone repo
git clone https://github.com/Kijanggoreng/lazy-commit
cd lazy-commit

# copy the lazy-commit files into the repo
# (place lazy_commit.py, install.sh, README.md, LICENSE, etc. here)

# configure git
git config user.name "Your Name"
git config user.email "you@example.com"

# initial commit
git add .
git commit -m "init: lazy-commit activity tracker"
git push origin main
```

### Step 4: Install the Timer

```bash
chmod +x install.sh
./install.sh
```

This sets up a **user-level systemd timer** (no root needed) that runs 8x daily.

### Step 5: Done

From now on, the timer runs automatically. Your private repo will accumulate commits, pulls, reviews, and issues — and they will show up on your GitHub contribution graph.

## Usage

```bash
python3 lazy_commit.py --plan           # preview this month's schedule
python3 lazy_commit.py --dry-run        # simulate without writing anything
python3 lazy_commit.py --force          # force one commit now
python3 lazy_commit.py --no-push         # commit only, skip remote sync
python3 lazy_commit.py --seed 502 --plan   # try a different pattern
```

## Seeds


| Seed | Style |
|------|-------|
| 42   | Default |
| 502  | Relaxed, mostly 1 commit/day |
| 654  | Balanced mix |
| 777  | Aggressive |

## Files

| File | Purpose |
|------|---------|
| `lazy_commit.py` | Main engine |
| `install.sh` | Systemd user timer setup |
| `.lazy_state.json` | Persistent schedule state (gitignored) |
| `activity.log` | Generated log (gitignored) |
| `issues/` | Open/closed issue tracking (gitignored) |
| `reviews.md` | Review notes (gitignored) |
| `pulls.log` | Pull history (gitignored) |

## Uninstall

```bash
systemctl --user stop lazy_commit.timer
systemctl --user disable lazy_commit.timer
rm ~/.config/systemd/user/lazy_commit.*
systemctl --user daemon-reload
```

## License

MIT — see [LICENSE](LICENSE).

