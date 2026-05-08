#!/usr/bin/env python3
"""
EasyPush — Git made simple.
Push files to GitHub, GitLab, or Bitbucket without touching the terminal.
"""

import os
import sys
import json
import subprocess
import threading
import pathlib
import shutil
import webbrowser
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk

# ── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = pathlib.Path.home() / ".easypush_config.json"

QUICK_COMMITS = [
    "✨ Add new files",
    "🐛 Fix a bug",
    "📝 Update docs",
    "🎨 Improve styling",
    "♻️  Refactor code",
    "🗑️  Remove old files",
    "🔒 Security update",
    "⚡ Performance boost",
    "🚀 New feature",
    "🧹 General cleanup",
]

PROVIDERS = {
    "GitHub":    {"url": "https://github.com",    "icon": "🐙", "color": "#238636"},
    "GitLab":    {"url": "https://gitlab.com",    "icon": "🦊", "color": "#FC6D26"},
    "Bitbucket": {"url": "https://bitbucket.org", "icon": "🪣", "color": "#0052CC"},
    "Custom":    {"url": "",                       "icon": "⚙️",  "color": "#6E40C9"},
}

TUTORIAL_STEPS = [
    {
        "title": "👋 Welcome to EasyPush!",
        "body": (
            "EasyPush lets you send your files to GitHub, GitLab, or Bitbucket "
            "without memorising any Git commands.\n\n"
            "Think of it like saving to the cloud — except your whole file history "
            "is saved, and you can share it with anyone."
        ),
    },
    {
        "title": "🔑 Step 1 — Connect your account",
        "body": (
            "Go to the ⚙️ Settings tab and enter:\n\n"
            "  • Your chosen provider (GitHub / GitLab / Bitbucket)\n"
            "  • Your username\n"
            "  • A Personal Access Token (PAT)\n\n"
            "A PAT is like a password just for EasyPush. "
            "You create one in your provider's settings under "
            "Developer Settings → Personal Access Tokens."
        ),
    },
    {
        "title": "📁 Step 2 — Choose your files",
        "body": (
            "On the Push tab, click 'Choose Files or Folder'.\n\n"
            "You can pick:\n"
            "  • A single file (e.g. my_essay.docx)\n"
            "  • Multiple files\n"
            "  • An entire folder / project\n\n"
            "EasyPush will track everything inside your chosen folder."
        ),
    },
    {
        "title": "💬 Step 3 — Write a commit message",
        "body": (
            "A commit message is a short note describing what you changed.\n\n"
            "Good examples:\n"
            "  • 'Add chapter 3'\n"
            "  • 'Fix the login bug'\n"
            "  • 'Update readme'\n\n"
            "You can also pick from our Quick Messages — just click one "
            "and it fills in automatically. Easy!"
        ),
    },
    {
        "title": "🚀 Step 4 — Push!",
        "body": (
            "Hit the big green PUSH button.\n\n"
            "EasyPush will:\n"
            "  1. Initialise Git if needed\n"
            "  2. Stage all your files\n"
            "  3. Commit with your message\n"
            "  4. Push to your provider\n\n"
            "The log at the bottom shows you exactly what's happening in real time."
        ),
    },
    {
        "title": "📜 Step 5 — View your history",
        "body": (
            "Switch to the 📜 History tab to see every push you've made.\n\n"
            "Each entry shows:\n"
            "  • The commit message\n"
            "  • When it was pushed\n"
            "  • The short commit ID\n\n"
            "You can also click 'Open on Web' to view your repo online."
        ),
    },
    {
        "title": "🎉 You're ready!",
        "body": (
            "That's everything you need to know.\n\n"
            "Pro tips:\n"
            "  • Push often — small, frequent pushes are better than one huge one\n"
            "  • Your commit messages are your future memory — be descriptive\n"
            "  • EasyPush saves your settings so you only set up once\n\n"
            "Happy pushing! 🚀"
        ),
    },
]


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {
        "provider": "GitHub",
        "username": "",
        "token": "",
        "custom_url": "",
        "default_branch": "main",
        "recent_repos": [],
    }


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def run_git(args, cwd, env=None):
    """Run a git command, return (stdout, stderr, returncode)."""
    git = shutil.which("git")
    if not git:
        return "", "Git not found. Please install Git from https://git-scm.com", 1
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    result = subprocess.run(
        [git] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=full_env,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


# ── Main App ─────────────────────────────────────────────────────────────────

class EasyPush(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EasyPush")
        self.geometry("860x680")
        self.minsize(700, 580)
        self.config = load_config()
        self.selected_path = tk.StringVar(value="")
        self.repo_name = tk.StringVar(value="")
        self.commit_msg = tk.StringVar(value="")
        self.branch = tk.StringVar(value=self.config.get("default_branch", "main"))
        self._build_ui()
        self._check_git()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(
            self.sidebar,
            text="Easy\nPush",
            font=ctk.CTkFont(family="Georgia", size=28, weight="bold"),
            text_color="#58a6ff",
        )
        logo.pack(pady=(28, 4))
        ctk.CTkLabel(
            self.sidebar,
            text="Git, simplified.",
            font=ctk.CTkFont(size=11),
            text_color="#8b949e",
        ).pack(pady=(0, 28))

        self.nav_buttons = {}
        tabs = [
            ("🚀  Push", "push"),
            ("📜  History", "history"),
            ("⚙️   Settings", "settings"),
            ("📖  Tutorial", "tutorial"),
        ]
        for label, key in tabs:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#21262d",
                text_color="#c9d1d9",
                height=40,
                corner_radius=8,
                command=lambda k=key: self._show_tab(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # Provider badge at sidebar bottom
        self.provider_badge = ctk.CTkLabel(
            self.sidebar,
            text=self._provider_label(),
            font=ctk.CTkFont(size=11),
            text_color="#8b949e",
        )
        self.provider_badge.pack(side="bottom", pady=16)

        # Main area
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="#0d1117")
        self.main.pack(side="left", fill="both", expand=True)

        self.frames = {}
        for key in ["push", "history", "settings", "tutorial"]:
            f = ctk.CTkFrame(self.main, corner_radius=0, fg_color="#0d1117")
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.frames[key] = f

        self._build_push()
        self._build_history()
        self._build_settings()
        self._build_tutorial()
        self._show_tab("push")

    def _provider_label(self):
        p = self.config.get("provider", "GitHub")
        icon = PROVIDERS.get(p, {}).get("icon", "🔗")
        return f"{icon} {p}"

    def _show_tab(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color="#21262d", text_color="#58a6ff")
            else:
                btn.configure(fg_color="transparent", text_color="#c9d1d9")
        self.frames[key].lift()
        if key == "history":
            self._refresh_history()

    # ── Push Tab ──────────────────────────────────────────────────────────────

    def _build_push(self):
        f = self.frames["push"]

        ctk.CTkLabel(f, text="Push Files", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(f, text="Select files, write a message, and send to your repo.",
                     font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", padx=28, pady=(0, 18))

        # File picker
        file_card = ctk.CTkFrame(f, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        file_card.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(file_card, text="📁  Project / Files", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8b949e").pack(anchor="w", padx=16, pady=(12, 4))

        row = ctk.CTkFrame(file_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.path_label = ctk.CTkLabel(
            row,
            textvariable=self.selected_path,
            font=ctk.CTkFont(size=12),
            text_color="#c9d1d9",
            wraplength=400,
            justify="left",
        )
        self.path_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(row, text="Choose…", width=100, height=32,
                      font=ctk.CTkFont(size=12), command=self._pick_path).pack(side="right")

        # Repo name
        repo_card = ctk.CTkFrame(f, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        repo_card.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(repo_card, text="🗄️  Repository Name", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8b949e").pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkEntry(repo_card, textvariable=self.repo_name, placeholder_text="my-awesome-project",
                     font=ctk.CTkFont(size=13), height=36).pack(fill="x", padx=16, pady=(0, 12))

        # Commit message
        commit_card = ctk.CTkFrame(f, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        commit_card.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(commit_card, text="💬  Commit Message", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8b949e").pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkEntry(commit_card, textvariable=self.commit_msg, placeholder_text="Describe what you changed…",
                     font=ctk.CTkFont(size=13), height=36).pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(commit_card, text="Quick messages:", font=ctk.CTkFont(size=11),
                     text_color="#8b949e").pack(anchor="w", padx=16)

        quick_frame = ctk.CTkFrame(commit_card, fg_color="transparent")
        quick_frame.pack(fill="x", padx=16, pady=(4, 12))

        for i, msg in enumerate(QUICK_COMMITS):
            btn = ctk.CTkButton(
                quick_frame,
                text=msg,
                font=ctk.CTkFont(size=11),
                height=26,
                fg_color="#21262d",
                hover_color="#30363d",
                text_color="#c9d1d9",
                corner_radius=6,
                command=lambda m=msg: self.commit_msg.set(m),
            )
            btn.grid(row=i // 5, column=i % 5, padx=3, pady=2, sticky="w")

        # Branch
        branch_row = ctk.CTkFrame(f, fg_color="transparent")
        branch_row.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(branch_row, text="Branch:", font=ctk.CTkFont(size=12),
                     text_color="#8b949e").pack(side="left")
        ctk.CTkEntry(branch_row, textvariable=self.branch, width=120,
                     font=ctk.CTkFont(size=12), height=30).pack(side="left", padx=8)

        # Push button
        self.push_btn = ctk.CTkButton(
            f,
            text="🚀  PUSH",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=48,
            fg_color="#238636",
            hover_color="#2ea043",
            corner_radius=10,
            command=self._do_push,
        )
        self.push_btn.pack(fill="x", padx=24, pady=(0, 12))

        # Log
        log_card = ctk.CTkFrame(f, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        log_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        log_header = ctk.CTkFrame(log_card, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(log_header, text="📋  Log", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8b949e").pack(side="left")
        ctk.CTkButton(log_header, text="Clear", width=55, height=22,
                      font=ctk.CTkFont(size=10), fg_color="#21262d", hover_color="#30363d",
                      command=self._clear_log).pack(side="right")

        self.log_box = ctk.CTkTextbox(log_card, font=ctk.CTkFont(family="Courier", size=11),
                                      fg_color="transparent", text_color="#c9d1d9", state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=8)

    def _pick_path(self):
        choice = filedialog.askdirectory(title="Choose project folder")
        if not choice:
            choice = filedialog.askopenfilenames(title="Choose files")
            if choice:
                # Use parent directory
                choice = os.path.dirname(choice[0])
        if choice:
            self.selected_path.set(choice)
            # Auto-fill repo name from folder name
            if not self.repo_name.get():
                self.repo_name.set(pathlib.Path(choice).name.replace(" ", "-").lower())

    def _log(self, text, color=None):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _do_push(self):
        # Validate
        path = self.selected_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("No folder selected", "Please choose a project folder first.")
            return
        msg = self.commit_msg.get().strip()
        if not msg:
            messagebox.showerror("No commit message", "Please write a commit message.")
            return
        repo = self.repo_name.get().strip()
        if not repo:
            messagebox.showerror("No repo name", "Please enter a repository name.")
            return
        username = self.config.get("username", "").strip()
        token = self.config.get("token", "").strip()
        if not username or not token:
            messagebox.showerror("Not configured",
                                 "Please set your username and token in ⚙️ Settings first.")
            self._show_tab("settings")
            return

        self.push_btn.configure(state="disabled", text="Pushing…")
        threading.Thread(target=self._push_worker, args=(path, msg, repo, username, token), daemon=True).start()

    def _push_worker(self, path, msg, repo, username, token):
        self._log("─" * 50)
        self._log(f"📁 Folder : {path}")
        self._log(f"🗄️  Repo   : {repo}")
        self._log(f"💬 Message: {msg}")
        self._log("")

        provider = self.config.get("provider", "GitHub")
        branch = self.branch.get().strip() or "main"

        if provider == "GitHub":
            remote_url = f"https://{username}:{token}@github.com/{username}/{repo}.git"
            web_url = f"https://github.com/{username}/{repo}"
        elif provider == "GitLab":
            remote_url = f"https://oauth2:{token}@gitlab.com/{username}/{repo}.git"
            web_url = f"https://gitlab.com/{username}/{repo}"
        elif provider == "Bitbucket":
            remote_url = f"https://{username}:{token}@bitbucket.org/{username}/{repo}.git"
            web_url = f"https://bitbucket.org/{username}/{repo}"
        else:
            custom = self.config.get("custom_url", "").rstrip("/")
            remote_url = f"{custom}/{username}/{repo}.git"
            web_url = f"{custom}/{username}/{repo}"

        steps = [
            (["init", "-b", branch], "Initialising git…"),
            (["add", "--all"], "Staging files…"),
            (["commit", "-m", msg, "--allow-empty"], "Committing…"),
        ]

        cwd = path
        for args, label in steps:
            self._log(f"▶ {label}")
            out, err, code = run_git(args, cwd)
            if out:
                self._log(f"  {out}")
            if err and code != 0:
                self._log(f"  ⚠ {err}")
                if code != 0:
                    self._log(f"\n❌ Failed at step: {label}")
                    self.after(0, lambda: self.push_btn.configure(state="normal", text="🚀  PUSH"))
                    return

        # Set/update remote
        self._log("▶ Setting remote…")
        run_git(["remote", "remove", "origin"], cwd)  # ignore errors
        out, err, code = run_git(["remote", "add", "origin", remote_url], cwd)

        # Push
        self._log(f"▶ Pushing to {provider}…")
        out, err, code = run_git(
            ["push", "-u", "origin", branch, "--force"],
            cwd,
            env={"GIT_TERMINAL_PROMPT": "0"},
        )
        if code == 0:
            self._log(f"\n✅ Success! View at: {web_url}")
            self._save_history(msg, repo, web_url)
            self.after(0, lambda: messagebox.showinfo(
                "Pushed!", f"Your files are live!\n\n{web_url}"))
        else:
            detail = err or out
            self._log(f"\n❌ Push failed:\n{detail}")
            self._log("\n💡 Check your token, username, and that the repo exists on the provider website.")
            self.after(0, lambda: messagebox.showerror(
                "Push failed",
                f"Could not push to {provider}.\n\n"
                f"Tips:\n• Make sure the repo exists on {provider}\n"
                f"• Check your token has write access\n"
                f"• Verify your username is correct"
            ))

        self.after(0, lambda: self.push_btn.configure(state="normal", text="🚀  PUSH"))

    # ── History Tab ───────────────────────────────────────────────────────────

    def _build_history(self):
        f = self.frames["history"]
        ctk.CTkLabel(f, text="Push History", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(f, text="Every push you've made from this machine.",
                     font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", padx=28, pady=(0, 16))

        self.history_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _refresh_history(self):
        for w in self.history_scroll.winfo_children():
            w.destroy()
        history = self.config.get("history", [])
        if not history:
            ctk.CTkLabel(self.history_scroll, text="No pushes yet.\nMake your first push on the 🚀 Push tab!",
                         font=ctk.CTkFont(size=13), text_color="#8b949e", justify="center").pack(pady=60)
            return
        for entry in reversed(history):
            card = ctk.CTkFrame(self.history_scroll, corner_radius=8, fg_color="#161b22",
                                border_width=1, border_color="#30363d")
            card.pack(fill="x", pady=5)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(top, text=entry.get("msg", ""), font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#c9d1d9").pack(side="left")
            bot = ctk.CTkFrame(card, fg_color="transparent")
            bot.pack(fill="x", padx=14, pady=(0, 10))
            ctk.CTkLabel(bot, text=f"📦 {entry.get('repo','')}  •  🕐 {entry.get('time','')}",
                         font=ctk.CTkFont(size=11), text_color="#8b949e").pack(side="left")
            url = entry.get("url", "")
            if url:
                ctk.CTkButton(bot, text="Open on Web ↗", width=110, height=26,
                              font=ctk.CTkFont(size=11), fg_color="#21262d", hover_color="#30363d",
                              command=lambda u=url: webbrowser.open(u)).pack(side="right")

    def _save_history(self, msg, repo, url):
        import datetime
        history = self.config.get("history", [])
        history.append({
            "msg": msg,
            "repo": repo,
            "url": url,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        # Keep last 50
        self.config["history"] = history[-50:]
        save_config(self.config)

    # ── Settings Tab ──────────────────────────────────────────────────────────

    def _build_settings(self):
        f = self.frames["settings"]
        ctk.CTkLabel(f, text="Settings", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(f, text="Configure your Git provider and credentials.",
                     font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", padx=28, pady=(0, 18))

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Provider
        pcard = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        pcard.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(pcard, text="Git Provider", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=16, pady=(14, 8))

        self.provider_var = tk.StringVar(value=self.config.get("provider", "GitHub"))
        pbtn_frame = ctk.CTkFrame(pcard, fg_color="transparent")
        pbtn_frame.pack(fill="x", padx=16, pady=(0, 14))
        self.provider_btns = {}
        for i, (name, info) in enumerate(PROVIDERS.items()):
            btn = ctk.CTkButton(
                pbtn_frame,
                text=f"{info['icon']} {name}",
                font=ctk.CTkFont(size=13),
                height=38,
                fg_color="#21262d" if self.config.get("provider") == name else "transparent",
                hover_color="#30363d",
                border_width=1,
                border_color="#30363d",
                corner_radius=8,
                command=lambda n=name: self._select_provider(n),
            )
            btn.grid(row=0, column=i, padx=4, sticky="ew", in_=pbtn_frame)
            pbtn_frame.columnconfigure(i, weight=1)
            self.provider_btns[name] = btn

        # Custom URL (shown only for Custom)
        self.custom_url_frame = ctk.CTkFrame(pcard, fg_color="transparent")
        self.custom_url_var = tk.StringVar(value=self.config.get("custom_url", ""))
        ctk.CTkLabel(self.custom_url_frame, text="Custom Git URL:", font=ctk.CTkFont(size=12),
                     text_color="#8b949e").pack(anchor="w")
        ctk.CTkEntry(self.custom_url_frame, textvariable=self.custom_url_var,
                     placeholder_text="https://mygitserver.com", height=34).pack(fill="x", pady=(4, 12))
        if self.config.get("provider") == "Custom":
            self.custom_url_frame.pack(fill="x", padx=16)

        # Credentials
        ccard = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#161b22", border_width=1, border_color="#30363d")
        ccard.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(ccard, text="Credentials", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=16, pady=(14, 8))

        self.username_var = tk.StringVar(value=self.config.get("username", ""))
        self.token_var = tk.StringVar(value=self.config.get("token", ""))
        self.branch_default_var = tk.StringVar(value=self.config.get("default_branch", "main"))

        for label, var, placeholder, show in [
            ("Username", self.username_var, "your-github-username", ""),
            ("Personal Access Token", self.token_var, "ghp_xxxxxxxxxxxx", "*"),
            ("Default Branch", self.branch_default_var, "main", ""),
        ]:
            ctk.CTkLabel(ccard, text=label, font=ctk.CTkFont(size=12), text_color="#8b949e").pack(
                anchor="w", padx=16, pady=(4, 0))
            ctk.CTkEntry(ccard, textvariable=var, placeholder_text=placeholder,
                         show=show, height=34).pack(fill="x", padx=16, pady=(4, 8))

        # Token help
        token_help = ctk.CTkFrame(ccard, fg_color="#0d1117", corner_radius=6)
        token_help.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(
            token_help,
            text="💡  How to get a token:\n"
                 "GitHub → Settings → Developer Settings → Personal Access Tokens → Generate new token\n"
                 "GitLab → Profile → Access Tokens → Add new token  |  Bitbucket → Security → App passwords",
            font=ctk.CTkFont(size=10),
            text_color="#8b949e",
            justify="left",
            wraplength=500,
        ).pack(anchor="w", padx=12, pady=8)

        # Save
        ctk.CTkButton(scroll, text="💾  Save Settings", height=42, font=ctk.CTkFont(size=14),
                      fg_color="#238636", hover_color="#2ea043", corner_radius=10,
                      command=self._save_settings).pack(fill="x", pady=(4, 0))

        # Git status
        self.git_status_label = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11), text_color="#8b949e")
        self.git_status_label.pack(anchor="w", pady=(12, 0))

    def _select_provider(self, name):
        for n, btn in self.provider_btns.items():
            btn.configure(fg_color="#21262d" if n == name else "transparent")
        if name == "Custom":
            self.custom_url_frame.pack(fill="x", padx=16)
        else:
            self.custom_url_frame.pack_forget()
        self.provider_var.set(name)

    def _save_settings(self):
        self.config["provider"] = self.provider_var.get()
        self.config["username"] = self.username_var.get().strip()
        self.config["token"] = self.token_var.get().strip()
        self.config["custom_url"] = self.custom_url_var.get().strip()
        self.config["default_branch"] = self.branch_default_var.get().strip() or "main"
        self.branch.set(self.config["default_branch"])
        save_config(self.config)
        self.provider_badge.configure(text=self._provider_label())
        messagebox.showinfo("Saved", "Settings saved successfully!")

    def _check_git(self):
        git = shutil.which("git")
        if not git:
            self.after(500, lambda: messagebox.showwarning(
                "Git not found",
                "Git is not installed on this computer.\n\n"
                "Please download and install Git from:\nhttps://git-scm.com/downloads\n\n"
                "Then restart EasyPush."
            ))

    # ── Tutorial Tab ──────────────────────────────────────────────────────────

    def _build_tutorial(self):
        f = self.frames["tutorial"]
        self._tut_step = 0

        ctk.CTkLabel(f, text="Tutorial", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#f0f6fc").pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(f, text="Learn EasyPush in 6 simple steps.",
                     font=ctk.CTkFont(size=12), text_color="#8b949e").pack(anchor="w", padx=28, pady=(0, 16))

        # Progress dots
        self.dot_frame = ctk.CTkFrame(f, fg_color="transparent")
        self.dot_frame.pack(pady=(0, 12))
        self.dots = []
        for i in range(len(TUTORIAL_STEPS)):
            d = ctk.CTkLabel(self.dot_frame, text="●", font=ctk.CTkFont(size=14),
                             text_color="#8b949e")
            d.pack(side="left", padx=4)
            self.dots.append(d)

        # Card
        self.tut_card = ctk.CTkFrame(f, corner_radius=14, fg_color="#161b22",
                                     border_width=1, border_color="#30363d")
        self.tut_card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        self.tut_title = ctk.CTkLabel(self.tut_card, text="",
                                      font=ctk.CTkFont(size=18, weight="bold"),
                                      text_color="#f0f6fc", wraplength=560)
        self.tut_title.pack(padx=28, pady=(32, 12))

        self.tut_body = ctk.CTkLabel(self.tut_card, text="",
                                     font=ctk.CTkFont(size=13), text_color="#c9d1d9",
                                     wraplength=560, justify="left")
        self.tut_body.pack(padx=28, pady=(0, 32))

        # Nav
        nav = ctk.CTkFrame(f, fg_color="transparent")
        nav.pack(fill="x", padx=28, pady=(0, 24))

        self.tut_back_btn = ctk.CTkButton(nav, text="← Back", width=100, height=38,
                                          fg_color="#21262d", hover_color="#30363d",
                                          font=ctk.CTkFont(size=13),
                                          command=self._tut_back)
        self.tut_back_btn.pack(side="left")

        self.tut_next_btn = ctk.CTkButton(nav, text="Next →", width=100, height=38,
                                          fg_color="#238636", hover_color="#2ea043",
                                          font=ctk.CTkFont(size=13),
                                          command=self._tut_next)
        self.tut_next_btn.pack(side="right")

        ctk.CTkButton(nav, text="Start Pushing 🚀", width=140, height=38,
                      fg_color="#1f6feb", hover_color="#388bfd",
                      font=ctk.CTkFont(size=13),
                      command=lambda: self._show_tab("push")).pack(side="right", padx=8)

        self._render_tutorial()

    def _render_tutorial(self):
        step = TUTORIAL_STEPS[self._tut_step]
        self.tut_title.configure(text=step["title"])
        self.tut_body.configure(text=step["body"])
        for i, d in enumerate(self.dots):
            d.configure(text_color="#58a6ff" if i == self._tut_step else "#30363d")
        self.tut_back_btn.configure(state="normal" if self._tut_step > 0 else "disabled")
        self.tut_next_btn.configure(
            state="normal" if self._tut_step < len(TUTORIAL_STEPS) - 1 else "disabled")

    def _tut_next(self):
        if self._tut_step < len(TUTORIAL_STEPS) - 1:
            self._tut_step += 1
            self._render_tutorial()

    def _tut_back(self):
        if self._tut_step > 0:
            self._tut_step -= 1
            self._render_tutorial()


if __name__ == "__main__":
    app = EasyPush()
    app.mainloop()
