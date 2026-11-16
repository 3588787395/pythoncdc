#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump the 41 target rules with every anchor and the CURRENT source line text."""
import json
import os
import sys

GAP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(os.path.dirname(GAP), "g4_audit")


def load(p):
    with open(p, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(GAP))))
    # repo root: find it
    cur = GAP
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        nxt = os.path.dirname(cur)
        if nxt == cur:
            raise SystemExit("no repo root")
        cur = nxt
    root = cur
    os.chdir(root)
    gap = os.path.join(root, ".trae", "specs", "achieve-any-syntax-completeness",
                       "rounds", "round13", "jspace_v3", "fresh", "gate_gap")
    aud = os.path.join(root, ".trae", "specs", "achieve-any-syntax-completeness",
                       "rounds", "round13", "jspace_v3", "fresh", "g4_audit")
    d = load(os.path.join(gap, "g4_empty_cov.json"))
    u = load(os.path.join(aud, "rule_universe_current.json"))
    um = {r["rule_id"]: r for r in u["rules"]}
    cache = {}
    lines = []
    rule_ids = []
    for i, c in enumerate(d["clusters"][:5]):
        lines.append("=" * 78)
        lines.append("CLUSTER %d  %s  (%d rules)" % (i + 1, c["cluster"], c["empty_count"]))
        for rid in c["empty_rule_ids"]:
            rule_ids.append(rid)
            r = um[rid]
            anchors = r.get("anchors") or [r["anchor"]]
            lines.append("  %s kind=%s sym=%s occ=%s scope=%s"
                         % (rid, r["kind"], r.get("symbol"), r.get("occurrences"),
                            r.get("scope")))
            for a in anchors:
                rel, _, ln = a.rpartition(":")
                try:
                    ln = int(ln)
                except ValueError:
                    continue
                if rel not in cache:
                    try:
                        cache[rel] = open(rel, encoding="utf-8",
                                          errors="replace").read().splitlines()
                    except OSError:
                        cache[rel] = []
                src = cache[rel]
                cur = src[ln - 1].strip()[:120] if 0 < ln <= len(src) else "<OUT-OF-RANGE>"
                lines.append("      %s:%d | %s" % (rel, ln, cur))
    path = os.path.join(gap, "_work", "anchors.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("rules=%d unique=%d -> %s" % (len(rule_ids), len(set(rule_ids)), path))


if __name__ == "__main__":
    sys.exit(main())
