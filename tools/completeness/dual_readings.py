#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the two required readings without collapsing them into one number."""

from __future__ import annotations

import argparse
import json
import os


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    with open(args.gate, "r", encoding="utf-8-sig") as fh:
        report = json.load(fh)
    dual = report.get("dual_readings") or {}
    shape = dual.get("shape") or {}
    judgment = dual.get("judgment") or {}
    rules = dual.get("rules") or {}
    canary = dual.get("canary") or {}
    gates = report.get("gates") or {}
    lines = [
        "# Dual Readings", "",
        "| reading | value | status |", "|---|---|---|",
        "| Shape baseline (regression only) | %s; small34 %s; quotation %s; v8 %s | G5 %s |" % (
            shape.get("units"), shape.get("small34"), shape.get("quotation"), shape.get("v8"),
            (gates.get("G5") or {}).get("status")),
        "| Judgment space (C1-C5) | %s/%s covered (%.2f%%); %s DIFF; %s uncovered | G1 %s |" % (
            judgment.get("covered_5tuple"), judgment.get("J_total"),
            judgment.get("coverage_pct", 0.0), judgment.get("semantic_failures"),
            judgment.get("uncovered"), (gates.get("G1") or {}).get("status")),
        "| Rule coverage | %s rules; %s proved; %s open | G4 %s |" % (
            rules.get("total"), rules.get("proved"), rules.get("open"),
            (gates.get("G4") or {}).get("status")),
        "| Canary | %s/%s equal | G6 %s |" % (
            canary.get("equal"), canary.get("total"), (gates.get("G6") or {}).get("status")),
        "", "Overall: **%s**" % report.get("overall"),
        "", "The judgment-space row is an integrated sample, not the full J population."
        if judgment.get("integrated_sample") else "",
        "", "Allowed: %s" % "; ".join(report.get("allowed_claims") or []),
        "", "Forbidden: %s" % "; ".join(report.get("forbidden_claims") or []),
    ]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(line for line in lines if line is not None) + "\n")
    print("[dual] wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
