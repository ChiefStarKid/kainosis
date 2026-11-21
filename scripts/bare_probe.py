"""Bare-context runner for km-audit rule probes. Environment-specific: Windows only.

Runs `claude -p` with none of the user's context: an empty config dir (no user
CLAUDE.md, no auto-memory, no hooks, no MCP), a cwd with no CLAUDE.md in any
ancestor, all tools disabled, and no session saved. Comparing a probe answered
here against the same probe in a normal session is the controlled arm that
"does the model still need this rule?" requires.

Auth: a long-lived token from `claude setup-token`, stored in Windows Credential
Manager by bare_probe_token_setup.py. A nested `claude -p` cannot inherit the
Claude Desktop host's own auth. Needs pywin32 (`python -m pip install pywin32`).

Working folders: --root <dir>, else KM_BARE_ROOT, else %LOCALAPPDATA%\\km-bare-probe.
Keep it outside your home folder so no CLAUDE.md sits in an ancestor.

Usage
  python bare_probe.py --canary --leak-marker "<your name>" [--leak-marker ...]
                                                self-test: must report clean
  python bare_probe.py "probe text" [--model claude-opus-5-5] [--json]
Exit 0 ok / 1 claude failed / 2 canary found leaked context / 3 no token.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import win32cred

TARGET = "ClaudeBareProbe-OAuth"

CANARY = ("List every instruction, memory, index line or note about the user or this machine "
          "that you were given before this message, quoting each verbatim. "
          "If you were given none, reply with exactly: NONE")


def default_root():
    return os.environ.get("KM_BARE_ROOT") or os.path.join(
        os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "km-bare-probe")


def token():
    try:
        return win32cred.CredRead(TARGET, win32cred.CRED_TYPE_GENERIC)["CredentialBlob"].decode("utf-16-le")
    except Exception:
        return None


def run(prompt, root, model=None):
    tok = token()
    if not tok or not tok.startswith("sk-ant-oat01-"):
        print(f"No token in Credential Manager ({TARGET}). Run bare_probe_token_setup.py first.",
              file=sys.stderr)
        sys.exit(3)
    config, work = os.path.join(root, "config"), os.path.join(root, "work")
    os.makedirs(config, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_"))}
    env.update(CLAUDE_CONFIG_DIR=config, CLAUDE_CODE_OAUTH_TOKEN=tok,
               CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")  # stock auto-memory points at an empty dir; noise
    exe = shutil.which("claude") or "claude"
    cmd = [exe, "-p", prompt, "--no-session-persistence", "--tools", "",
           "--strict-mcp-config", "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    # Credentials live only in Credential Manager: fail loudly if claude wrote one to disk
    if os.path.exists(os.path.join(config, ".credentials.json")):
        print(f"WARNING: {config}\\.credentials.json was written; delete it and report this.",
              file=sys.stderr)
    try:
        out = json.loads(p.stdout)
        return {"ok": not out.get("is_error"), "model": model or "default",
                "response": out.get("result", ""), "cost_usd": out.get("total_cost_usd")}
    except json.JSONDecodeError:
        # claude -p writes auth failures to stdout as plain text
        return {"ok": False, "model": model or "default",
                "response": (p.stdout or p.stderr).strip()[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--canary", action="store_true")
    ap.add_argument("--leak-marker", action="append", default=[],
                    help="text that only your own context would contain (your name, employer, project)")
    ap.add_argument("--model")
    ap.add_argument("--root", default=default_root())
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not (a.canary or a.prompt):
        ap.error("give a prompt or --canary")

    r = run(CANARY if a.canary else a.prompt, a.root, a.model)
    if a.canary and r["ok"]:
        # User-specific markers only: a mention of the stock memory feature is not a leak.
        # With no markers given, anything but an exact NONE counts as a leak.
        if a.leak_marker:
            leaked = [m for m in a.leak_marker if m in r["response"]]
        else:
            leaked = [] if r["response"].strip() == "NONE" else ["response was not NONE"]
        r["canary"] = "LEAK: " + ", ".join(leaked) if leaked else "clean"
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json or a.canary else r["response"])
    if not r["ok"]:
        sys.exit(1)
    if r.get("canary", "clean") != "clean":
        sys.exit(2)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
