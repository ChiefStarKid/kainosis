"""Reference implementation of the km close-out verdict rules (docs/closeout-verdict.md).
Stdlib only. Usage: python scripts/km_verdict_check.py ledger.json  -> prints the verdict line."""
import json
import sys


def blockers(ledger):
    lean = ledger.get("mode", "full") == "lean"
    out = []
    for c in ledger.get("candidates", []):
        d, cid = c.get("disposition"), c.get("id")
        if d not in ("written", "merged", "rejected", "deferred"):
            out.append(f"candidate {cid}: no valid disposition")
        elif d in ("written", "merged") and not (c.get("verified") and c.get("evidence")):
            out.append(f"candidate {cid}: claims '{d}' but it is unverified")
        elif d == "deferred" and not (c.get("where") or c.get("accepted")):
            out.append(f"candidate {cid}: deferred with no home")
    if not lean:
        rs = ledger.get("reverse_sweep") or {}
        if not rs.get("ran"):
            out.append("reverse sweep did not run")
        elif rs.get("unreconciled"):
            out.append(f"reverse sweep: {len(rs['unreconciled'])} find(s) not in the ledger")
        for le in ledger.get("loose_ends", []):
            if le.get("status") == "open" and not le.get("accepted"):
                out.append(f"loose end open: {le.get('item')}")
            elif le.get("status") == "tracked" and not le.get("where"):
                out.append(f"loose end tracked with no location: {le.get('item')}")
        for co in ledger.get("carry_over", []):
            if not (co.get("where") or co.get("accepted")):
                out.append(f"carry-over unanchored: {co.get('item')}")
    return out


def verdict(ledger):
    b = blockers(ledger)
    if ledger.get("mode", "full") == "lean":
        if b:
            return "NOT SAFE TO COMPACT - " + "; ".join(b)
        return "SAFE TO COMPACT (lean: no reverse sweep, no loose-ends sweep; not an archive/delete verdict)"
    return "NOT SAFE - " + "; ".join(b) if b else "SAFE"


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(verdict(json.load(f)))
