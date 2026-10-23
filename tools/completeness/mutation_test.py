#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AST mutation driver for attack-completeness-claims Task 9.2.

The mutation population is generated from the original source AST, not from
the current test cases or rule list.  Each mutant is compiled, then compared
against the original artifact by semantic_diff.py.  A survivor is MISSED
unless an explicit equivalence proof is supplied; a proven-equivalent mutant
that is reported DIFFERENT is FALSE_KILL.  INCONCLUSIVE and ERROR are never
counted as killed.

Equivalent proofs are case-relative or semantic claims supplied by the
reviewer.  The tool does not invent them.  A proof may cover a mutant whose
only observed difference is code metadata (co_code/co_consts and friends):
the mutation is then EQUIVALENT at the behavior level, while any R1-R6 or
non-code metadata difference remains FALSE_KILL.

CLI:
    python -X utf8 tools/completeness/mutation_test.py \
        --case case.json --source subject.py --out mutations.json
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import shutil
import sys
import tempfile

import semantic_diff as sd

TOOL_VERSION = "1.0.0"
BINOP_SWAP = {
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.Div: ast.Mult,
    ast.FloorDiv: ast.Mult, ast.Mod: ast.Mult, ast.Pow: ast.Mult,
    ast.LShift: ast.RShift, ast.RShift: ast.LShift, ast.BitOr: ast.BitAnd,
    ast.BitAnd: ast.BitOr, ast.BitXor: ast.BitOr, ast.MatMult: ast.Mult,
}
CMP_SWAP = {
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}
AUG_SWAP = {
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv,
    ast.Div: ast.Mult, ast.FloorDiv: ast.Mult, ast.Mod: ast.Mult,
    ast.BitOr: ast.BitAnd, ast.BitAnd: ast.BitOr, ast.BitXor: ast.BitOr,
}
UNARY_SWAP = {ast.USub: ast.UAdd, ast.UAdd: ast.USub, ast.Invert: ast.Not}
OPERATORS = ("binop", "compare", "augassign", "unaryop", "boolop", "constant", "return", "if", "while")


def _walk(node: ast.AST, path=()):
    yield node, path
    for field, value in ast.iter_fields(node):
        if isinstance(value, list):
            for index, child in enumerate(value):
                if isinstance(child, ast.AST):
                    yield from _walk(child, path + ((field, index),))
        elif isinstance(value, ast.AST):
            yield from _walk(value, path + ((field, None),))


def _get_node(tree: ast.AST, path: list) -> ast.AST:
    node = tree
    for field, index in path:
        value = getattr(node, field)
        node = value if index is None else value[index]
    return node


def _alt_name(cls) -> str:
    return cls.__name__


def _constant_value(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value + 1.0
    if isinstance(value, str):
        return value + "_mut"
    if isinstance(value, bytes):
        return value + b"_mut"
    if isinstance(value, complex):
        return value + 1j
    if value is None:
        return 0
    return None


def generate_mutations(tree: ast.AST, operators: set[str] | None = None) -> list[dict]:
    wanted = set(OPERATORS if operators is None else operators)
    mutations: list[dict] = []
    for node, path in _walk(tree):
        item = None
        if isinstance(node, ast.BinOp) and "binop" in wanted:
            alt = BINOP_SWAP.get(type(node.op))
            if alt:
                item = ("binop", type(node.op).__name__ + " -> " + _alt_name(alt),
                        {"op": _alt_name(alt)})
        elif isinstance(node, ast.Compare) and "compare" in wanted and node.ops:
            alt = CMP_SWAP.get(type(node.ops[0]))
            if alt:
                item = ("compare", type(node.ops[0]).__name__ + " -> " + _alt_name(alt),
                        {"op": _alt_name(alt)})
        elif isinstance(node, ast.AugAssign) and "augassign" in wanted:
            alt = AUG_SWAP.get(type(node.op))
            if alt:
                item = ("augassign", type(node.op).__name__ + " -> " + _alt_name(alt),
                        {"op": _alt_name(alt)})
        elif isinstance(node, ast.UnaryOp) and "unaryop" in wanted:
            alt = UNARY_SWAP.get(type(node.op))
            if alt:
                item = ("unaryop", type(node.op).__name__ + " -> " + _alt_name(alt),
                        {"op": _alt_name(alt)})
        elif isinstance(node, ast.BoolOp) and "boolop" in wanted:
            alt = ast.Or if isinstance(node.op, ast.And) else ast.And
            item = ("boolop", type(node.op).__name__ + " -> " + _alt_name(alt),
                    {"op": _alt_name(alt)})
        elif isinstance(node, ast.Constant) and "constant" in wanted:
            new_value = _constant_value(node.value)
            if new_value is not None or node.value is not None:
                item = ("constant", "%r -> %r" % (node.value, new_value),
                        {"value": new_value})
        elif isinstance(node, ast.Return) and "return" in wanted and node.value is not None:
            item = ("return", "return value -> return None", {"value": None})
        elif isinstance(node, ast.If) and "if" in wanted:
            item = ("if", "if test -> if not test", {"negate": True})
        elif isinstance(node, ast.While) and "while" in wanted:
            item = ("while", "while test -> while not test", {"negate": True})
        if item is None:
            continue
        operator, description, payload = item
        mutations.append({
            "mutation_id": "M%04d" % (len(mutations) + 1),
            "operator": operator,
            "description": description,
            "lineno": getattr(node, "lineno", None),
            "col_offset": getattr(node, "col_offset", None),
            "path": [[field, index] for field, index in path],
            "payload": payload,
        })
    return mutations


def apply_mutation(tree: ast.AST, mutation: dict) -> ast.AST:
    node = _get_node(tree, mutation["path"])
    payload = mutation["payload"]
    if mutation["operator"] in ("binop", "compare", "augassign", "unaryop", "boolop"):
        cls = getattr(ast, payload["op"])
        if mutation["operator"] == "compare":
            node.ops[0] = cls()
        else:
            node.op = cls()
    elif mutation["operator"] == "constant":
        node.value = payload["value"]
    elif mutation["operator"] == "return":
        node.value = None
    elif mutation["operator"] in ("if", "while"):
        replacement = ast.UnaryOp(op=ast.Not(), operand=node.test)
        ast.copy_location(replacement, node.test)
        ast.fix_missing_locations(replacement)
        node.test = replacement
    else:
        raise ValueError("unknown mutation operator: %r" % mutation["operator"])
    return tree


def mutation_source(source: str, mutation: dict) -> str:
    tree = ast.parse(source)
    apply_mutation(tree, mutation)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _code_metadata_only(diffs: list) -> bool:
    return bool(diffs) and all(
        item.get("dimension") == "R7" and str(item.get("path", "")).startswith("$.metadata.code.")
        for item in diffs
    )


def _load_equivalents(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("equivalents file must be a JSON object")
    out = {}
    for key, value in data.items():
        if not isinstance(value, dict) or not str(value.get("proof", "")).strip():
            raise ValueError("equivalent %s needs a non-empty proof" % key)
        out[key] = value
    return out


def run_mutations(case: dict, source_path: str, *, max_mutants: int = 100,
                  operators: set[str] | None = None,
                  equivalents: dict | None = None,
                  workdir: str | None = None) -> dict:
    equivalents = equivalents or {}
    with open(source_path, "r", encoding="utf-8-sig") as fh:
        source = fh.read()
    tree = ast.parse(source, filename=source_path)
    all_mutations = generate_mutations(tree, operators)
    selected = all_mutations[:max_mutants]
    report = {
        "tool": "mutation_test", "version": TOOL_VERSION,
        "case_id": case.get("case_id") or case.get("id") or "case",
        "source": source_path, "generated": len(all_mutations),
        "selected": len(selected), "operators": sorted(operators or OPERATORS),
        "baseline": None, "summary": {}, "mutants": [],
    }
    if not selected:
        report["status"] = "NO_MUTANTS"
        return report
    temporary = workdir or tempfile.mkdtemp(prefix="mutation_test_")
    created = workdir is None
    os.makedirs(temporary, exist_ok=True)
    try:
        baseline_path = os.path.join(temporary, "baseline.py")
        _write(baseline_path, ast.unparse(tree) + "\n")
        baseline_case = copy.deepcopy(case)
        baseline_case["case_id"] = report["case_id"] + "-baseline"
        baseline_case["product"] = {"source": baseline_path}
        baseline = sd.compare_case(baseline_case)
        report["baseline"] = baseline
        if baseline.get("status") != sd.EQUAL:
            report["status"] = "ABORTED_BASELINE"
            return report
        counts = {"KILLED": 0, "MISSED": 0, "EQUIVALENT": 0, "FALSE_KILL": 0,
                  "INCONCLUSIVE": 0, "ERROR": 0}
        for mutation in selected:
            mid = mutation["mutation_id"]
            path = os.path.join(temporary, "mutant-%s.py" % mid)
            try:
                _write(path, mutation_source(source, mutation))
            except BaseException as exc:
                record = dict(mutation)
                record.update({"status": "ERROR", "semantic_status": "GENERATION_ERROR",
                               "error": "%s: %s" % (type(exc).__name__, exc)})
                counts["ERROR"] += 1
                report["mutants"].append(record)
                continue
            mutant_case = copy.deepcopy(case)
            mutant_case["case_id"] = report["case_id"] + "-" + mid
            mutant_case["product"] = {"source": path}
            result = sd.compare_case(mutant_case)
            semantic = result.get("status")
            proof = equivalents.get(mid)
            diffs = result.get("diffs", [])
            if semantic == sd.DIFFERENT:
                if _code_metadata_only(diffs):
                    status = "EQUIVALENT" if proof else "MISSED"
                else:
                    status = "FALSE_KILL" if proof else "KILLED"
            elif semantic == sd.EQUAL:
                status = "EQUIVALENT" if proof else "MISSED"
            elif semantic == sd.INCONCLUSIVE:
                status = "INCONCLUSIVE"
            else:
                status = "ERROR"
            counts[status] += 1
            record = dict(mutation)
            record.update({
                "status": status, "semantic_status": semantic,
                "diffs": diffs,
                "inconclusive": result.get("inconclusive", []),
                "errors": result.get("errors", []),
            })
            if proof:
                record["equivalence_proof"] = proof
                if status == "EQUIVALENT" and semantic == sd.DIFFERENT:
                    record["equivalence_note"] = "only code metadata differs"
            report["mutants"].append(record)
        killed = counts["KILLED"]
        missed = counts["MISSED"]
        equivalent = counts["EQUIVALENT"]
        false_kill = counts["FALSE_KILL"]
        denominator = killed + missed
        report["summary"] = {
            **counts,
            "evaluated": len(selected),
            "mutation_score": (killed / denominator) if denominator else None,
            "missed_rate": (missed / denominator) if denominator else None,
            "equivalent_proven": equivalent,
            "false_kill_rate": (false_kill / len(selected)) if selected else None,
        }
        report["status"] = "COMPLETE"
        return report
    finally:
        if created:
            shutil.rmtree(temporary, ignore_errors=True)


def _resolve(path: str, base: str) -> str:
    return os.path.abspath(os.path.join(base, path)) if not os.path.isabs(path) else path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--source")
    parser.add_argument("--equivalents")
    parser.add_argument("--out")
    parser.add_argument("--max-mutants", type=int, default=100)
    parser.add_argument("--operators", help="comma-separated subset of " + ",".join(OPERATORS))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--allow-missed", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    with open(args.case, "r", encoding="utf-8-sig") as fh:
        case = json.load(fh)
    base = os.path.dirname(os.path.abspath(args.case))
    case["_base"] = base
    source = args.source
    if not source:
        source = (case.get("source") or case.get("original", {}).get("source"))
    if not source:
        parser.error("--source is required when the original target has no source")
    source = _resolve(source, base)
    operators = set(item.strip() for item in args.operators.split(",") if item.strip()) if args.operators else None
    equivalents = _load_equivalents(args.equivalents)
    if args.list:
        with open(source, "r", encoding="utf-8-sig") as fh:
            tree = ast.parse(fh.read(), filename=source)
        mutations = generate_mutations(tree, operators)[:args.max_mutants]
        print(json.dumps({"source": source, "count": len(mutations),
                          "mutations": mutations}, ensure_ascii=False, indent=1))
        return 0
    report = run_mutations(case, source, max_mutants=args.max_mutants,
                           operators=operators, equivalents=equivalents)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(json.dumps({"tool": "mutation_test", "status": report["status"],
                          "summary": report.get("summary", {})}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    if report["status"] != "COMPLETE":
        return 3
    summary = report["summary"]
    if summary["ERROR"] or summary["FALSE_KILL"]:
        return 3
    if summary["INCONCLUSIVE"]:
        return 2
    if summary["MISSED"] and not args.allow_missed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
