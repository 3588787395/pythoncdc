# -*- coding: utf-8 -*-
"""Print universe rule entries (id, symbol, kind, anchor, scope) for given ids."""
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8-sig"))
want = set(sys.argv[2].split(","))
for r in doc["rules"]:
    if r["rule_id"] in want:
        print(json.dumps({k: r.get(k) for k in (
            "rule_id", "symbol", "kind", "anchor", "anchors", "predicate_scope",
            "predicate", "source_line", "composition", "notes")},
            ensure_ascii=False, indent=1)[:2600])
        print("-" * 70)
