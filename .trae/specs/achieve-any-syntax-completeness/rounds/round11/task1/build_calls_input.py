#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Task-1 J-sample input with input_model.calls filled.

Task 1.4 re-runs the J sample under the corrected measurement semantics.  The
six DIFFERENT entries get real calls so R1 (B142) is observed instead of R7
only.  round9/judgment_space.json stays untouched; this writes a 100-entry
working copy under round11/task1/.

JS-IF-017/021/088/090/097 share v_b71_face.pyc (B142 nested finally/continue).
JS-IF-076 is x01_if_deep_hosts.pyc; if_in_while() is deliberately excluded
because the current product loses the break and loops forever, which would turn
the R7 function-body evidence into a timeout INCONCLUSIVE.  Termination
evidence for if_in_while belongs to Task 3 after the break fix.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def repo_root() -> str:
    root = HERE
    while root and not os.path.isdir(os.path.join(root, ".git")):
        root = os.path.dirname(root)
    return root


B142_CALLS = ["v_nest_fin_continue([[0, 1]])", "v_nest_fin_continue([0])"]
X01_CALLS = ["if_in_for()", "if_in_try()", "if_shallow()", "if_in_match()"]

CALLS = {
    "JS-IF-017": list(B142_CALLS),
    "JS-IF-021": list(B142_CALLS),
    "JS-IF-088": list(B142_CALLS),
    "JS-IF-090": list(B142_CALLS),
    "JS-IF-097": list(B142_CALLS),
    "JS-IF-076": list(X01_CALLS),
}


def main() -> int:
    root = repo_root()
    space_path = os.path.join(root, ".trae", "specs", "attack-completeness-claims",
                              "rounds", "round9", "judgment_space.json")
    out_path = os.path.join(HERE, "j_sample_calls_input.json")
    with open(space_path, "r", encoding="utf-8-sig") as fh:
        space = json.load(fh)
    entries = space["entries"][:100]
    filled = set()
    for entry in entries:
        calls = CALLS.get(entry.get("id"))
        if calls is None:
            continue
        model = entry.setdefault("input_model", {})
        model["calls"] = list(calls)
        model["note"] = "Task 1.4 calls; see rounds/round11/task1/J_SAMPLE_TASK1.md"
        filled.add(entry["id"])
    missing = sorted(set(CALLS) - filled)
    if missing:
        print("[build_calls_input] ERROR: ids not in first 100 entries: %s" % missing,
              file=sys.stderr)
        return 1
    payload = {key: value for key, value in space.items() if key != "entries"}
    payload["entries"] = entries
    payload["note"] = ("Task 1.4 working copy: first 100 entries of round9 "
                       "judgment_space.json with input_model.calls filled for the six "
                       "DIFFERENT entries (JS-IF-017/021/076/088/090/097); the round9 "
                       "original stays untouched")
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[build_calls_input] entries=%d with_calls=%d -> %s"
          % (len(entries), len(filled), os.path.relpath(out_path, root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
