"""One-time: store a `claude setup-token` OAuth token in Credential Manager for bare_probe.py.

Run in a plain terminal (not inside Claude):
  1. claude setup-token                  -> copy the token it prints (sk-ant-oat01-...)
  2. python bare_probe_token_setup.py    -> reads the token from the clipboard

The token is read from the clipboard (pasting into a hidden prompt is unreliable in
Windows PowerShell 5.1: it stored 1 character on 2026-11-21), validated, written straight
to Credential Manager (target ClaudeBareProbe-OAuth), and the clipboard is cleared.
Only the length is printed; the token is never echoed or written to disk.
Windows only (pywin32). On macOS the equivalent store is Keychain; not implemented.
"""
import re
import subprocess

import win32cred

TARGET = "ClaudeBareProbe-OAuth"


def clipboard():
    return subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                          capture_output=True, text=True).stdout


# Console copy of a wrapped line can insert line breaks: drop all whitespace
tok = re.sub(r"\s+", "", clipboard() or "")
if not re.fullmatch(r"sk-ant-oat01-[A-Za-z0-9_\-]{40,}", tok):
    raise SystemExit(f"Clipboard doesn't hold a setup-token (got {len(tok)} chars, expected "
                     "sk-ant-oat01-...). Copy the token line and run again. Nothing stored.")
win32cred.CredWrite({
    "Type": win32cred.CRED_TYPE_GENERIC,
    "TargetName": TARGET,
    "UserName": "claude-bare-probe",
    "CredentialBlob": tok,
    "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
}, 0)
subprocess.run(["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ' '"])
print(f"Stored in Credential Manager as {TARGET} ({len(tok)} chars). Clipboard cleared.")
