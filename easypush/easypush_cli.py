#!/usr/bin/env python3
"""
easypush-cli — terminal companion for EasyPush
Usage:
    easypush push [path] [-m "message"] [-r repo] [-b branch]
    easypush history
    easypush config
    easypush open
"""

import sys
import os
import json
import subprocess
import shutil
import pathlib
import argparse
import datetime

CONFIG_FILE = pathlib.Path.home() / ".easypush_config.json"

# ── ANSI colours ──────────────────────────────────────────────────────────────
R = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
BLUE = "\033[34m"


def banner():
    print(f"""
{CYAN}{BOLD}
  ███████╗ █████╗ ███████╗██╗   ██╗██████╗ ██╗   ██╗███████╗██╗  ██╗
  ██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██╔══██╗██║   ██║██╔════╝██║  ██║
  █████╗  ███████║███████╗ ╚████╔╝ ██████╔╝██║   ██║███████╗███████║
  ██╔══╝  ██╔══██║╚════██║  ╚██╔╝  ██╔═══╝ ██║   ██║╚════██║██╔══██║
  ███████╗██║  ██║███████║   ██║   ██║     ╚██████╔╝███████║██║  ██║
  ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝
{R}{DIM}  Git, simplified.{R}
""")


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def run_git(args, cwd, quiet=False):
    git = shutil.which("git")
    if not git:
        print(f"{RED}✗ Git not found. Install from https://git-scm.com{R}")
        sys.exit(1)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run([git] + args, cwd=cwd, capture_output=True, text=True, env=env)
    if not quiet:
        if result.stdout.strip():
            print(f"  {DIM}{result.stdout.strip()}{R}")
        if result.stderr.strip() and result.returncode != 0:
            print(f"  {YELLOW}{result.stderr.strip()}{R}")
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def step(msg):
    print(f"  {CYAN}▶{R} {msg}")


def ok(msg):
    print(f"  {GREEN}✓{R} {msg}")


def fail(msg):
    print(f"  {RED}✗{R} {msg}")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_push(args):
    cfg = load_config()
    if not cfg:
        print(f"{YELLOW}No config found. Run: easypush config{R}")
        sys.exit(1)

    path = args.path or os.getcwd()
    path = os.path.abspath(path)
    if not os.path.exists(path):
        fail(f"Path not found: {path}")
        sys.exit(1)

    msg = args.message
    if not msg:
        try:
            msg = input(f"{BOLD}Commit message:{R} ").strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
    if not msg:
        fail("Commit message cannot be empty.")
        sys.exit(1)

    repo = args.repo or pathlib.Path(path).name.replace(" ", "-").lower()
    branch = args.branch or cfg.get("default_branch", "main")
    username = cfg.get("username", "")
    token = cfg.get("token", "")
    provider = cfg.get("provider", "GitHub")

    if not username or not token:
        fail("Username or token not set. Run: easypush config")
        sys.exit(1)

    print(f"\n{BOLD}Pushing {CYAN}{path}{R}")
    print(f"  Provider : {CYAN}{provider}{R}")
    print(f"  Repo     : {CYAN}{username}/{repo}{R}")
    print(f"  Branch   : {CYAN}{branch}{R}")
    print(f"  Message  : {CYAN}{msg}{R}")
    print()

    if provider == "GitHub":
        remote = f"https://{username}:{token}@github.com/{username}/{repo}.git"
        web = f"https://github.com/{username}/{repo}"
    elif provider == "GitLab":
        remote = f"https://oauth2:{token}@gitlab.com/{username}/{repo}.git"
        web = f"https://gitlab.com/{username}/{repo}"
    elif provider == "Bitbucket":
        remote = f"https://{username}:{token}@bitbucket.org/{username}/{repo}.git"
        web = f"https://bitbucket.org/{username}/{repo}"
    else:
        base = cfg.get("custom_url", "").rstrip("/")
        remote = f"{base}/{username}/{repo}.git"
        web = f"{base}/{username}/{repo}"

    step(f"Initialising…")
    run_git(["init", "-b", branch], path, quiet=True)
    ok("Git ready")

    step("Staging all files…")
    run_git(["add", "--all"], path, quiet=True)
    ok("Files staged")

    step("Committing…")
    _, err, code = run_git(["commit", "-m", msg, "--allow-empty"], path, quiet=True)
    ok("Committed")

    step("Removing old remote (if any)…")
    run_git(["remote", "remove", "origin"], path, quiet=True)
    run_git(["remote", "add", "origin", remote], path, quiet=True)

    step("Pushing…")
    _, err, code = run_git(["push", "-u", "origin", branch, "--force"], path, quiet=True)

    if code == 0:
        print(f"\n{GREEN}{BOLD}✓ Push successful!{R}")
        print(f"  {BLUE}{web}{R}\n")
        # Save to history
        history = cfg.get("history", [])
        history.append({
            "msg": msg,
            "repo": repo,
            "url": web,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        cfg["history"] = history[-50:]
        save_config(cfg)
    else:
        print(f"\n{RED}{BOLD}✗ Push failed.{R}")
        if err:
            print(f"  {DIM}{err}{R}")
        print(f"\n  {YELLOW}Tips:{R}")
        print(f"   • Make sure the repo '{repo}' exists on {provider}")
        print(f"   • Check your token has write access")
        print(f"   • Verify your username\n")
        sys.exit(1)


def cmd_history(args):
    cfg = load_config()
    history = cfg.get("history", [])
    if not history:
        print(f"\n{DIM}No pushes yet. Run: easypush push{R}\n")
        return
    print(f"\n{BOLD}Push History{R}  ({len(history)} total)\n")
    print(f"  {'Time':<17} {'Repo':<25} {'Message'}")
    print(f"  {'─'*16} {'─'*24} {'─'*30}")
    for entry in reversed(history[-20:]):
        t = entry.get("time", "")
        r = entry.get("repo", "")
        m = entry.get("msg", "")
        if len(m) > 40:
            m = m[:37] + "…"
        print(f"  {DIM}{t:<17}{R} {CYAN}{r:<25}{R} {m}")
    print()


def cmd_config(args):
    cfg = load_config()
    print(f"\n{BOLD}EasyPush Configuration{R}\n")

    providers = ["GitHub", "GitLab", "Bitbucket", "Custom"]
    for i, p in enumerate(providers, 1):
        marker = f"{GREEN}●{R}" if cfg.get("provider") == p else " "
        print(f"  {marker} {i}. {p}")
    try:
        choice = input(f"\n{BOLD}Choose provider [1-4]:{R} ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(providers):
            cfg["provider"] = providers[idx]
    except (ValueError, KeyboardInterrupt):
        print("Keeping current provider.")

    fields = [
        ("username", "Username", ""),
        ("token", "Personal Access Token", ""),
        ("default_branch", "Default Branch", "main"),
    ]
    if cfg.get("provider") == "Custom":
        fields.insert(0, ("custom_url", "Custom Git URL", ""))

    for key, label, default in fields:
        current = cfg.get(key, default)
        display = f" [{current}]" if current and key != "token" else (" [set]" if cfg.get(key) else "")
        try:
            val = input(f"  {label}{display}: ").strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
        if val:
            cfg[key] = val

    save_config(cfg)
    print(f"\n{GREEN}✓ Config saved!{R}\n")


def cmd_open(args):
    cfg = load_config()
    history = cfg.get("history", [])
    if not history:
        print("No history yet.")
        return
    url = history[-1].get("url", "")
    if url:
        import webbrowser
        webbrowser.open(url)
        print(f"Opening: {url}")
    else:
        print("No URL found.")


def cmd_gui(args):
    """Launch the GUI."""
    script = pathlib.Path(__file__).parent / "easypush.py"
    if script.exists():
        subprocess.Popen([sys.executable, str(script)])
    else:
        print(f"{RED}GUI not found. Make sure easypush.py is in the same folder.{R}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    banner()
    parser = argparse.ArgumentParser(
        prog="easypush",
        description="Git, simplified.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # push
    p_push = sub.add_parser("push", help="Push files to your repo")
    p_push.add_argument("path", nargs="?", help="Folder to push (default: current dir)")
    p_push.add_argument("-m", "--message", help="Commit message")
    p_push.add_argument("-r", "--repo", help="Repository name")
    p_push.add_argument("-b", "--branch", help="Branch name (default: main)")

    # history
    sub.add_parser("history", help="Show push history")

    # config
    sub.add_parser("config", help="Set up your provider and credentials")

    # open
    sub.add_parser("open", help="Open last pushed repo in browser")

    # gui
    sub.add_parser("gui", help="Launch the EasyPush GUI")

    args = parser.parse_args()

    if args.command == "push":
        cmd_push(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "open":
        cmd_open(args)
    elif args.command == "gui":
        cmd_gui(args)
    else:
        parser.print_help()
        print(f"\n{DIM}Quick start: easypush config  →  easypush push{R}\n")


if __name__ == "__main__":
    main()
