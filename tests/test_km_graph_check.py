"""Run: python -X utf8 -I tests/test_km_graph_check.py
km_graph_check.py preflight: the line the skill acts on instead of three Error handling rows."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
script = str(root / "scripts" / "km_graph_check.py")
example = str(root / "examples" / "graph")


def run(*a, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PLUGIN_OPTION_MEMORY_PATH", "KM_MEMORY_PATH")}
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, "-X", "utf8", "-I", script, *a], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr


with tempfile.TemporaryDirectory() as t:
    base = Path(t)
    # STOP: unset (empty), unexpanded placeholder, missing dir, no --mem and no env
    for args in (["--mem", ""], ["--mem", "${user_config.memory_path}"], ["--mem", str(base / "absent")], []):
        rc, out, err = run(*args)
        assert rc == 2 and out.startswith("preflight: STOP (") and len(out.splitlines()) == 1, (args, rc, out, err)
    assert "not set" in run("--mem", "")[1] and "not found" in run("--mem", str(base / "absent"))[1]
    # the environment variable still works
    rc, out, _ = run("--preflight", env_extra={"KM_MEMORY_PATH": example})
    assert rc == 0 and out.strip() == "preflight: OK", out
    # CREATE-ONLY: empty dir (log.md alone is not a memory file), then a file without MEMORY.md
    empty = base / "empty"
    empty.mkdir()
    rc, out, _ = run("--mem", str(empty), "--preflight")
    assert rc == 0 and out.strip() == "preflight: CREATE-ONLY (no memory files)", out
    (empty / "log.md").write_text("x\n", encoding="utf-8")
    assert run("--mem", str(empty), "--preflight")[1].strip() == "preflight: CREATE-ONLY (no memory files)"
    (empty / "a.md").write_text("---\nname: a\n---\nx\n", encoding="utf-8")
    rc, out, _ = run("--mem", str(empty))
    assert out.splitlines()[0] == "preflight: CREATE-ONLY (MEMORY.md missing)" and "files: 1" in out, out
    # OK: the normal summary follows the line, unchanged
    rc, out, _ = run("--mem", example)
    L = out.splitlines()
    assert rc == 0 and L[0] == "preflight: OK" and L[1].startswith("memory dir:"), out
    assert "islands (0 inbound [[ ]]): 0" in out and "dead [[ ]] links: 0" in out
    # --json stays pure JSON and carries the state
    rc, out, _ = run("--mem", example, "--json")
    assert json.loads(out)["preflight"] == "OK"
    # a failure inside the analysis is a DEGRADED line and exit 1, not a traceback
    bad = base / "bad"
    bad.mkdir()
    (bad / "MEMORY.md").write_text("x\n", encoding="utf-8")
    (bad / "a.md").write_text("x\n", encoding="utf-8")
    sys.path.insert(0, str(root / "scripts"))
    import km_graph_check as kg

    def boom(*a, **k):
        raise RuntimeError("boom")

    kg.analyse = boom
    sys.argv = ["km_graph_check", "--mem", str(bad)]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            kg.main()
    except SystemExit as e:
        assert e.code == 1
    else:
        raise AssertionError("expected exit 1")
    assert buf.getvalue().strip() == "preflight: DEGRADED (graph check failed: RuntimeError: boom)", buf.getvalue()
print("ok: km_graph_check")
