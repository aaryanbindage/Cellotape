# EasyPush 🚀

**Git made simple — a beautiful GUI and CLI for pushing files to GitHub, GitLab, or Bitbucket.**

No Git knowledge required. Just pick your files, write a message, and push.

---

## What's included

| File | Purpose |
|------|---------|
| `easypush.py` | Full GUI application (recommended) |
| `easypush_cli.py` | Terminal / command-line tool |
| `install_mac.sh` | One-click installer for macOS |
| `install_windows.bat` | One-click installer for Windows |

---

## Requirements

- **Python 3.8+** — [python.org](https://python.org)
- **Git** — [git-scm.com](https://git-scm.com)
- A **GitHub / GitLab / Bitbucket** account
- A **Personal Access Token** from your provider

---

## Installation

### macOS

```bash
bash install_mac.sh
```

Then launch with:
```bash
easypush gui      # Open the GUI
easypush push     # Push from terminal
```

### Windows

Double-click `install_windows.bat`, then use from any terminal:
```
easypush gui
easypush push
```

### Manual install (any OS)

```bash
pip install customtkinter
python easypush.py          # GUI
python easypush_cli.py gui  # GUI via CLI
python easypush_cli.py push # Terminal push
```

---

## GUI Quick Start

1. **Run** `easypush.py`
2. Go to **⚙️ Settings** — enter your provider, username, and token
3. Go to **🚀 Push** — choose your folder, pick a commit message, hit PUSH
4. Done! Your files are live.

---

## CLI Reference

```bash
easypush config              # Set up credentials (run this first)
easypush push                # Push current folder (asks for message)
easypush push ./my-project   # Push a specific folder
easypush push -m "Add docs"  # Push with message
easypush push -r my-repo -b develop  # Specify repo and branch
easypush history             # See your push history
easypush open                # Open last repo in browser
easypush gui                 # Launch the GUI
```

---

## Getting a Personal Access Token

### GitHub
1. Go to github.com → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic) → Generate new token
3. Select scopes: **repo** (full control)
4. Copy the token and paste it into EasyPush Settings

### GitLab
1. Go to gitlab.com → Profile → Access Tokens
2. Add new token → select **api** scope
3. Copy and paste into EasyPush Settings

### Bitbucket
1. Go to bitbucket.org → Personal settings → App passwords
2. Create app password → select **Repositories: Read & Write**
3. Copy and paste into EasyPush Settings

---

## How it works

EasyPush runs standard Git commands for you:

```
git init -b main
git add --all
git commit -m "your message"
git remote add origin https://...
git push -u origin main --force
```

Your credentials are stored locally at `~/.easypush_config.json`.
Tokens are stored in plain text — use a token with minimal permissions.

---

## Tips

- **Push often** — small pushes are better than one huge one
- **Your commit messages are your history** — be descriptive
- The repo must exist on GitHub/GitLab/Bitbucket before you push
  (EasyPush pushes to existing repos; it doesn't create them)
- Use `--force` is fine for personal projects; for shared repos, be careful

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Git not found" | Install Git from git-scm.com |
| "Push failed: 403" | Token doesn't have write access — regenerate with `repo` scope |
| "Push failed: 404" | Repo doesn't exist — create it on the website first |
| "Push failed: 401" | Wrong username or token |
| GUI won't open | Run `pip install customtkinter` |

---

Made with ❤️ — EasyPush v1.0
