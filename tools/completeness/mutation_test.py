#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AST mutation driver for attack-completeness-claims Task 9.2.

The mutation population is generated from the original source AST, not from
the current test cases or rule list.  Each mutant is compiled, then compared
against the original artifact by semantic_diff.py.

Classification is three-way, following the R7 blocking requirement
(spec.md "R7 code object 阻断"): a code-object difference is DIFFERENT, it is
never a survivor, and only a written equivalence proof turns it into
EQUIVALENT.

  1. a non-empty ``equivalents`` proof            -> EQUIVALENT
     (whether the judge says EQUAL or DIFFERENT with R7-only evidence:
      nested co_code / co_consts spelling / uncalled function body);
  2. no proof and ``DIFFERENT``                    -> KILLED
     (R7 blocks: a code-object difference is kill evidence, not a survivor);
  3. no proof and ``EQUAL``                        -> MISSED;
  4. a proof plus a behaviour-level difference (any R0-R6/LOAD dimension)
     -> FALSE_KILL.  FALSE_KILL is reserved for exactly this case: a proof
     claims equivalence while the judge observed a behaviour-level
     difference, so the kill is a false positive that a reviewer must
     adjudicate.  A proof can never excuse an R1-R6 difference.

INCONCLUSIVE and ERROR are never counted as killed.  Equivalent proofs are
supplied by the reviewer; the tool does not invent them.  No-op mutants are
dropped at generation time: a candidate whose mutated source compiles to the
same code object as the baseline (``return None`` -> ``return``; a
byte-identical source is the special case) is not a mutant, and it is
recorded under ``generator_fixes`` instead of being counted as MISSED.

CLI:
    python -X utf8 tools/completeness/mutation_test.py \
        --case case.json --source subject.py --out mutations.json
    python -X utf8 tools/completeness/mutation_test.py --selftest
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
import types

# `python -I` removes the script directory from sys.path; keep the documented
# `python -I -X utf8 tools/completeness/mutation_test.py ...` invocation working.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import semantic_diff as sd

TOOL_VERSION = "1.1.0"
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


def generate_mutations(tree: ast.AST, operators: set[str] | None = None, *,
                       skip_identity: bool = True,
                       skipped: list | None = None) -> list[dict]:
    """Enumerate mutants; drop no-op mutants before assigning ids.

    A no-op mutant is one whose mutated source compiles to the *same code
    object* as the baseline under the semantic_diff comparison (co_code,
    co_consts, names, signature, exception table — the registered ignorable
    fields excluded).  Byte-identical source is the special case of this; the
    observed G3 case is ``return None`` -> ``return``, whose source text
    differs but whose compiled code object is identical.  Such a candidate is
    not a mutant: it never receives a ``mutation_id``, and it is appended to
    *skipped* (when given) with ``reason="identity_no_op"`` so the caller can
    report it as a generator fix instead of a survivor.
    """
    wanted = set(OPERATORS if operators is None else operators)
    baseline_text = ast.unparse(tree) + "\n" if skip_identity else None
    baseline_identity = _compiled_identity(tree) if skip_identity else None
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
        candidate = {
            "operator": operator,
            "description": description,
            "lineno": getattr(node, "lineno", None),
            "col_offset": getattr(node, "col_offset", None),
            "path": [[field, index] for field, index in path],
            "payload": payload,
        }
        if skip_identity:
            neutral = False
            text_identical = None
            note = ""
            try:
                clone = copy.deepcopy(tree)
                apply_mutation(clone, candidate)
                ast.fix_missing_locations(clone)
                mutated_identity = _code_identity(compile(clone, "<mutation_test>", "exec"))
                text_identical = (ast.unparse(clone) + "\n") == baseline_text
                if baseline_identity is not None and mutated_identity == baseline_identity:
                    neutral = True
                    note = ("mutated source compiles to the same code object as the baseline; "
                            "source text %s" % ("is identical" if text_identical else "differs"))
            except BaseException:
                neutral = False
            if neutral:
                record = {"mutation_id": None, **candidate,
                          "reason": "identity_no_op",
                          "text_identical": bool(text_identical),
                          "note": note}
                if skipped is not None:
                    skipped.append(record)
                continue
        mutations.append({"mutation_id": "M%04d" % (len(mutations) + 1), **candidate})
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


def _mutation_text(tree: ast.AST, mutation: dict) -> str:
    """Mutated source produced from *tree*, without touching the caller's tree."""
    clone = copy.deepcopy(tree)
    apply_mutation(clone, mutation)
    ast.fix_missing_locations(clone)
    return ast.unparse(clone) + "\n"


def _const_identity(value):
    """Structure-preserving identity token for one code-object constant."""
    if isinstance(value, types.CodeType):
        return ("code", _code_identity(value))
    if isinstance(value, tuple):
        return ("tuple", tuple(_const_identity(item) for item in value))
    if isinstance(value, frozenset):
        return ("frozenset", tuple(sorted((repr(_const_identity(item)) for item in value))))
    if isinstance(value, list):
        return ("list", tuple(_const_identity(item) for item in value))
    return (type(value).__name__, repr(value))


def _code_identity(code: types.CodeType):
    """Identity token for a code object under the semantic_diff comparison.

    The registered ignorable fields (co_filename / co_firstlineno /
    co_linetable) are deliberately left out, so two sources that differ only
    in layout compare equal here, exactly as semantic_diff would compare them.
    """
    fields = ("co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals",
              "co_stacksize", "co_flags", "co_names", "co_varnames", "co_freevars",
              "co_cellvars", "co_code", "co_exceptiontable", "co_qualname")
    token = [(name, getattr(code, name, None)) for name in fields]
    token.append(("co_consts", tuple(_const_identity(value) for value in code.co_consts)))
    return tuple(token)


def _compiled_identity(tree: ast.AST):
    """Code-object identity of *tree*, or None when it does not compile."""
    try:
        return _code_identity(compile(tree, "<mutation_test>", "exec"))
    except BaseException:
        return None


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


IGNORABLE_CODE_FIELDS = frozenset(("co_filename", "co_firstlineno", "co_linetable"))


def _code_metadata_only(diffs: list) -> bool:
    """True only when every difference is registered metadata noise.

    Diagnostic helper kept for the G3 ruler-fix probes; classification no
    longer branches on it (the three-way rule treats any DIFFERENT without a
    proof as KILLED).  Nested code objects are compared field by field by
    ``semantic_diff``; a path under ``co_consts.v[i]`` is a real
    function/comprehension body difference, not metadata-only.  The three
    registered fields (co_filename / co_firstlineno / co_linetable) stay
    ignorable at any depth.
    """
    if not diffs:
        return False
    for item in diffs:
        if item.get("dimension") != "R7":
            return False
        path = str(item.get("path", ""))
        if not path.startswith("$.metadata.code."):
            return False
        relative = path[len("$.metadata.code."):]
        leaf = relative.rsplit(".", 1)[-1]
        if leaf in IGNORABLE_CODE_FIELDS:
            continue
        if relative.startswith("co_consts.v[") or ".co_consts.v[" in relative:
            return False
    return True


def _r7_only(diffs: list) -> bool:
    """True when every observed difference is R7 (code-object/signature layer).

    R7 blocking still makes such a comparison DIFFERENT.  An equivalents proof
    is accepted on R7-only evidence because a proof speaks about observable
    behaviour, and R7 differences (nested co_code / co_consts spelling /
    uncalled function body) need not change it.  Any R0-R6/LOAD difference is
    behaviour-level evidence and a proof may not silence it.
    """
    if not diffs:
        return False
    for item in diffs:
        if not isinstance(item, dict) or item.get("dimension") != "R7":
            return False
    return True


def classify(semantic_status: str | None, proof: dict | None, diffs: list) -> str:
    """Three-way classification with R7 blocking (see module docstring).

    1. proof present                          -> EQUIVALENT
    2. no proof and DIFFERENT                 -> KILLED
    3. no proof and EQUAL                     -> MISSED
    4. proof present plus a non-R7 difference -> FALSE_KILL
    """
    if semantic_status == sd.DIFFERENT:
        if not proof:
            return "KILLED"
        return "EQUIVALENT" if _r7_only(diffs) else "FALSE_KILL"
    if semantic_status == sd.EQUAL:
        return "EQUIVALENT" if proof else "MISSED"
    if semantic_status == sd.INCONCLUSIVE:
        return "INCONCLUSIVE"
    return "ERROR"


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
                  workdir: str | None = None,
                  skip_identity: bool = True) -> dict:
    equivalents = equivalents or {}
    with open(source_path, "r", encoding="utf-8-sig") as fh:
        source = fh.read()
    tree = ast.parse(source, filename=source_path)
    identity_skipped: list[dict] = []
    all_mutations = generate_mutations(tree, operators, skip_identity=skip_identity,
                                      skipped=identity_skipped)
    selected = all_mutations[:max_mutants]
    report = {
        "tool": "mutation_test", "version": TOOL_VERSION,
        "case_id": case.get("case_id") or case.get("id") or "case",
        "source": source_path, "generated": len(all_mutations),
        "generated_raw": len(all_mutations) + len(identity_skipped),
        "selected": len(selected), "operators": sorted(operators or OPERATORS),
        "classification": "three-way (proof->EQUIVALENT; no proof+DIFFERENT->KILLED; "
                          "no proof+EQUAL->MISSED; proof+non-R7->FALSE_KILL)",
        "generator_fixes": identity_skipped,
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
            status = classify(semantic, proof, diffs)
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
                    record["equivalence_note"] = (
                        "R7-only differences; behaviour equivalence is the reviewer's proof")
                elif status == "FALSE_KILL":
                    record["equivalence_note"] = (
                        "proof present but the judge observed a non-R7 difference: "
                        "a proof cannot excuse behaviour-level evidence")
            report["mutants"].append(record)
        killed = counts["KILLED"]
        missed = counts["MISSED"]
        equivalent = counts["EQUIVALENT"]
        false_kill = counts["FALSE_KILL"]
        denominator = killed + missed
        report["summary"] = {
            **counts,
            "evaluated": len(selected),
            "identity_skipped": len(identity_skipped),
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


def _selftest_write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def selftest() -> dict:
    """Three-direction self-test of the classification rule.

    1. proof present, R7-only DIFFERENT -> EQUIVALENT;
    2. no proof, DIFFERENT            -> KILLED;
    3. proof present, non-R7 DIFFERENT-> FALSE_KILL (a proof cannot excuse
       behaviour-level evidence);
    plus the generator fix: an identity mutant is dropped at generation, and
    would be MISSED (no proof, EQUAL) if it were still generated.
    """
    root = tempfile.mkdtemp(prefix="mutation_selftest_")
    checks: dict[str, bool] = {}
    evidence: dict[str, object] = {}
    try:
        # ---- direction 1/2: same subject, R7-only difference -------------
        # x * 1 -> x // 1 keeps every observed value for int input, so the
        # judge reports DIFFERENT on R7 co_code only.
        eq_root = os.path.join(root, "eq")
        os.makedirs(eq_root)
        eq_subject = os.path.join(eq_root, "subject.py")
        _selftest_write(eq_subject, "def f(x):\n    return x * 1\n")
        eq_case = {
            "case_id": "selftest-equivalent",
            "original": {"source": eq_subject},
            "entrypoint": "function:f",
            "calls": [{"args": [5]}, {"args": [-3]}, {"args": [0]}],
            "_base": eq_root,
        }
        with open(eq_subject, "r", encoding="utf-8") as fh:
            listed = generate_mutations(ast.parse(fh.read()))
        mult = [item for item in listed
                if item["operator"] == "binop" and item["description"].startswith("Mult")]
        if not mult:
            raise RuntimeError("selftest subject produced no Mult mutation")
        mult_id = mult[0]["mutation_id"]
        unproven = run_mutations(eq_case, eq_subject, max_mutants=50)
        proven = run_mutations(
            eq_case, eq_subject, max_mutants=50,
            equivalents={mult_id: {
                "proof": "case domain is int; x * 1 and x // 1 return x for every "
                         "observed argument, so no R1-R6 difference can exist"}})
        unproven_by_id = {item["mutation_id"]: item for item in unproven["mutants"]}
        proven_by_id = {item["mutation_id"]: item for item in proven["mutants"]}
        checks["direction1_proof_r7_only_different_is_equivalent"] = (
            proven_by_id.get(mult_id, {}).get("semantic_status") == sd.DIFFERENT
            and proven_by_id.get(mult_id, {}).get("status") == "EQUIVALENT"
            and all(d.get("dimension") == "R7"
                    for d in proven_by_id.get(mult_id, {}).get("diffs", [])))
        checks["direction2_no_proof_different_is_killed"] = (
            unproven_by_id.get(mult_id, {}).get("semantic_status") == sd.DIFFERENT
            and unproven_by_id.get(mult_id, {}).get("status") == "KILLED")
        evidence["direction1_2"] = {
            "mutation": mult[0]["description"],
            "unproven": {k: unproven_by_id.get(mult_id, {}).get(k)
                         for k in ("status", "semantic_status")},
            "proven": {k: proven_by_id.get(mult_id, {}).get(k)
                       for k in ("status", "semantic_status")},
        }

        # ---- direction 3: proof cannot excuse a real behaviour change ----
        fk_root = os.path.join(root, "fk")
        os.makedirs(fk_root)
        fk_subject = os.path.join(fk_root, "subject.py")
        _selftest_write(fk_subject, "def sub(a, b):\n    return a - b\n")
        fk_case = {
            "case_id": "selftest-false-kill",
            "original": {"source": fk_subject},
            "entrypoint": "function:sub",
            "calls": [{"args": [5, 3]}, {"args": [1, 4]}],
            "_base": fk_root,
        }
        with open(fk_subject, "r", encoding="utf-8") as fh:
            fk_listed = generate_mutations(ast.parse(fh.read()))
        sub_mut = [item for item in fk_listed
                   if item["operator"] == "binop" and item["description"].startswith("Sub")]
        if not sub_mut:
            raise RuntimeError("selftest subject produced no Sub mutation")
        sub_id = sub_mut[0]["mutation_id"]
        false_kill = run_mutations(
            fk_case, fk_subject, max_mutants=50,
            equivalents={sub_id: {
                "proof": "deliberately wrong proof for the self-test: this claim is "
                         "refuted by the observed R1 return-value difference"}})
        fk_by_id = {item["mutation_id"]: item for item in false_kill["mutants"]}
        row = fk_by_id.get(sub_id, {})
        checks["direction3_proof_plus_non_r7_is_false_kill"] = (
            row.get("semantic_status") == sd.DIFFERENT
            and row.get("status") == "FALSE_KILL"
            and any(d.get("dimension") != "R7" for d in row.get("diffs", [])))
        evidence["direction3"] = {
            "mutation": sub_mut[0]["description"],
            "status": row.get("status"), "semantic_status": row.get("semantic_status"),
            "dimensions": sorted({d.get("dimension") for d in row.get("diffs", [])}),
        }

        # ---- generator fix: identity mutant is not a mutant --------------
        id_root = os.path.join(root, "identity")
        os.makedirs(id_root)
        id_subject = os.path.join(id_root, "subject.py")
        _selftest_write(id_subject, "def f():\n    return None\n")
        id_case = {
            "case_id": "selftest-identity",
            "original": {"source": id_subject},
            "entrypoint": "function:f",
            "calls": [{"args": []}],
            "_base": id_root,
        }
        fixed = run_mutations(id_case, id_subject, max_mutants=50)
        kept = run_mutations(id_case, id_subject, max_mutants=50, skip_identity=False)
        kept_identity = [item for item in kept["mutants"]
                         if item.get("semantic_status") == sd.EQUAL]
        kept_status = sorted({item["status"] for item in kept_identity})
        fixes = fixed.get("generator_fixes") or []
        checks["generator_drops_identity_mutant"] = (
            fixed["summary"].get("identity_skipped") == 1
            and len(fixes) == 1
            and fixes[0]["reason"] == "identity_no_op"
            and fixes[0]["text_identical"] is False
            and not [item for item in fixed["mutants"]
                     if item.get("semantic_status") == sd.EQUAL])
        checks["identity_mutant_would_be_missed"] = (
            len(kept_identity) == 1 and kept_status == ["MISSED"])
        evidence["identity"] = {
            "subject": "def f(): return None",
            "skipped": fixed["summary"].get("identity_skipped"),
            "source_text_identical": fixes[0]["text_identical"] if fixes else None,
            "note": fixes[0]["note"] if fixes else None,
            "status_with_generator_fix": "not a mutant",
            "status_when_forced": kept_status,
        }

        # ---- no DIFFERENT mutant may be reported as MISSED ---------------
        checks["no_different_mutant_is_missed"] = all(
            not (item.get("semantic_status") == sd.DIFFERENT and item.get("status") == "MISSED")
            for report in (unproven, proven, false_kill, kept)
            for item in report["mutants"])
        payload = {
            "tool": "mutation_test_selftest", "version": TOOL_VERSION,
            "rule": "three-way (proof->EQUIVALENT; no proof+DIFFERENT->KILLED; "
                    "no proof+EQUAL->MISSED; proof+non-R7->FALSE_KILL)",
            "checks": checks, "passed": all(checks.values()),
            "evidence": evidence,
            "summaries": {"unproven": unproven["summary"], "proven": proven["summary"],
                          "false_kill": false_kill["summary"], "identity_fixed": fixed["summary"],
                          "identity_forced": kept["summary"]},
        }
        return payload
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=False)
    parser.add_argument("--source")
    parser.add_argument("--equivalents")
    parser.add_argument("--out")
    parser.add_argument("--max-mutants", type=int, default=100)
    parser.add_argument("--operators", help="comma-separated subset of " + ",".join(OPERATORS))
    parser.add_argument("--keep-identity", action="store_true",
                        help="keep identity mutants (reproduces the pre-fix readings)")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--allow-missed", action="store_true")
    parser.add_argument("--selftest", action="store_true",
                        help="run the three-direction classification self-test")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    if args.selftest:
        payload = selftest()
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if payload["passed"] else 1
    if not args.case:
        parser.error("--case is required (or use --selftest)")
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
    skip_identity = not args.keep_identity
    if args.list:
        with open(source, "r", encoding="utf-8-sig") as fh:
            tree = ast.parse(fh.read(), filename=source)
        skipped: list[dict] = []
        mutations = generate_mutations(tree, operators, skip_identity=skip_identity,
                                       skipped=skipped)[:args.max_mutants]
        print(json.dumps({"source": source, "count": len(mutations),
                          "identity_skipped": len(skipped),
                          "mutations": mutations}, ensure_ascii=False, indent=1))
        return 0
    report = run_mutations(case, source, max_mutants=args.max_mutants,
                           operators=operators, equivalents=equivalents,
                           skip_identity=skip_identity)
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
