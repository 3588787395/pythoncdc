#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G4 rule proof / composition checker -- v1 DRAFT definition.

This tool implements the *draft* existence semantics written down in
``fresh/gate_g4/G4_PROOF_THEORY.md``.  It does NOT prove rule semantic
correctness.  What it establishes, per rule, is only this:

    the rule predicate (the ``isinstance(...)`` / ``== '<const>'`` /
    ``in <set>`` test that the universe scanner recorded for that rule) is
    *true at a concrete, executed occurrence* of that rule's anchor inside the
    region reduction pipeline, and *false* at another executed occurrence of
    the same anchor inside a different J entry.

Nothing here may be read as "the rule is correct".

Inputs (read-only):

    --universe   universe_v2.json      independent rule universe (the denominator)
    --manifest   manifest_v2.json      rule -> obligation mapping (all open in v2)
    --jspace     judgment_space.json   J: the entry space the witnesses must live in
    --traces     traces_v2.json        per-entry executed rule anchors
    --out        proof record JSON     this tool's own artifact

Outputs:

    --out             proof records, one object per universe rule
    --manifest-out    default ``<out dir>/manifest_proved_v1.json``: a *candidate*
                      manifest for review.  manifest_v2.json is never touched.
    --json            optional compact copy of counts + records + rehearsal

Measurement method: the region pipeline is executed once per distinct J pyc
with ``sys.settrace`` installed, but a frame is only line-traced when its code
object actually contains one of the universe anchor lines.  At such a line the
predicate rebuilt from the rule's declared ``kind`` + ``symbol`` is evaluated
with ``eval`` against that live frame's globals/locals, so ``observed_value``
and the true/false verdict come from the real run, not from source reading.
No rule id, name whitelist, constant whitelist, numeric depth cap or absolute
offset ever decides a predicate: the offset only appears inside the
``occurrence_id`` identity string.

CLI:

    python -X utf8 tools/completeness/rule_proof_check.py \
        --universe fresh/gate_gap/universe_v2.json \
        --manifest fresh/gate_gap/manifest_v2.json \
        --jspace  fresh/gate_gap/judgment_space.json \
        --traces  fresh/gate_gap/traces_v2.json \
        --out     fresh/gate_g4/proof_records_v1.json
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import marshal
import os
import sys
import time

TOOL_VERSION = "1.0.0"
DEFINITION_VERSION = "G4 proof theory v1 (draft, pending review)"
DEFINITION_DOC = "fresh/gate_g4/G4_PROOF_THEORY.md"
CHECKER_ID = "rule_proof_check/%s" % TOOL_VERSION
SINGLETON = "<singleton>"

# Mirrors tools/completeness/rule_universe.py::OP_NAMES (that file is read-only
# for this tool; the scanner semantics are re-stated here, never imported
# mutably and never altered).
OP_NAMES = {"opname", "opcode", "name", "kind", "node_type", "node_name"}

R_NO_OCCURRENCE = "no_occurrence_in_J"
R_PREDICATE_FALSE = "predicate_false_at_site"
R_NEGATIVE_MISSING = "negative_witness_missing"
R_NOT_LOCATED = "predicate_not_located"
R_UNEVALUABLE = "predicate_unevaluable"
R_SOURCE_DRIFT = "anchor_source_drift"
R_TRACE_MISMATCH = "trace_runtime_disagreement"
R_OTHER = "other"

REASON_TEXT = {
    R_NO_OCCURRENCE: ("no J entry executes any anchor of this rule, so no occurrence, no "
                      "observed value and no witness exist"),
    R_PREDICATE_FALSE: ("the anchor executes but the predicate never evaluates true at any "
                        "executed occurrence in J"),
    R_NEGATIVE_MISSING: ("positive occurrence measured, but no other J entry reaches the site "
                         "with a strictly false predicate"),
    R_NOT_LOCATED: "the declared predicate could not be rebuilt from the source at the anchor",
    R_UNEVALUABLE: "every evaluation of the predicate raised, so no truth value was measured",
    R_SOURCE_DRIFT: "the universe source_sha256 for this rule's file no longer matches the tree",
    R_TRACE_MISMATCH: "traces_v2 reports the rule as hit by an entry, but the runtime never evaluated its site",
    R_OTHER: "open for another reason; see notes",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def canonical(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(data) -> str:
    return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_TEXT_SHA_CACHE = {}


def text_sha256(path) -> str:
    """The universe scanner hashed the *decoded* source text, not the raw bytes."""
    cached = _TEXT_SHA_CACHE.get(path)
    if cached is not None:
        return cached
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        value = hashlib.sha256(fh.read().encode("utf-8")).hexdigest()
    _TEXT_SHA_CACHE[path] = value
    return value


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def norm(p) -> str:
    p = str(p).replace("\\", "/")
    i = p.find("core/")
    return p[i:] if i >= 0 else p


def write_json(path, data, indent=1):
    if not path:
        return
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")


def short_repr(value, limit=160) -> str:
    """Display only.  Never a predicate, never a completeness decision."""
    try:
        text = repr(value)
    except BaseException:
        return "<unreprable %s>" % type(value).__name__
    if len(text) > limit:
        text = text[:limit] + "...<truncated for display>"
    return text


# --------------------------------------------------------------------------- #
# predicate location: mirrors rule_universe.py's scanner shapes
# --------------------------------------------------------------------------- #
def _ast_attr(node):
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "ast"):
        return node.attr
    return None


def _op_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _str_constant(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _isinstance_arg_types(test):
    if not isinstance(test, ast.Call) or len(test.args) < 2:
        return []
    func = test.func
    if not (isinstance(func, ast.Name) and func.id == "isinstance"):
        return []
    arg = test.args[1]
    nodes = arg.elts if isinstance(arg, ast.Tuple) else [arg]
    out = []
    for item in nodes:
        name = _ast_attr(item)
        if name:
            out.append((name, item))
    return out


def _class_name_tests(test):
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return []
    left, op, right = test.left, test.ops[0], test.comparators[0]
    if not isinstance(op, ast.Eq):
        return []
    needle = _str_constant(right)
    if not needle:
        return []
    blob = ast.dump(left)
    if "__class__" in blob and "__name__" in blob:
        return [needle]
    if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "type":
        if left.args and ast.dump(left.args[0]).find("__class__") >= 0:
            return [needle]
    return []


def _opcode_tests(test):
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return []
    left, op, right = test.left, test.ops[0], test.comparators[0]
    if _op_name(left) not in OP_NAMES:
        return []
    if isinstance(op, ast.Eq) and _str_constant(right):
        return [_str_constant(right)]
    if isinstance(op, ast.In):
        container = right
        if isinstance(container, (ast.Tuple, ast.List, ast.Set)):
            return [v for v in (_str_constant(x) for x in container.elts) if v]
        if isinstance(container, (ast.Name, ast.Attribute)):
            return [ast.unparse(container)]
    return []


def _region_assignment(node):
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return []
    target = node.targets[0]
    if not isinstance(target, ast.Name) or "region" not in target.id.lower():
        return []
    value = node.value
    if not isinstance(value, (ast.Tuple, ast.List, ast.Set)):
        return []
    out = []
    for item in value.elts:
        name = _ast_attr(item)
        if name:
            out.append(name)
        else:
            text = _str_constant(item)
            if text:
                out.append(text)
    return out


def _walk_with_path(node, segs=()):
    yield node, segs
    for name, value in ast.iter_fields(node):
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, ast.AST):
                    yield from _walk_with_path(item, segs + ((name, i),))
        elif isinstance(value, ast.AST):
            yield from _walk_with_path(value, segs + ((name, None),))


def _path_text(segs) -> str:
    out = ["Module"]
    for name, index in segs:
        out.append("." + name)
        if index is not None:
            out.append("[%d]" % index)
    return "".join(out)


class Candidate(object):
    """One rebuildable rule predicate at one declared anchor line."""

    __slots__ = ("uid", "rule_id", "kind", "symbol", "file", "line", "ast_path",
                 "expr_src", "expected_value", "compiled", "subject_compiled")

    def __init__(self, rule_id, kind, symbol, file, line, ast_path, expr_src,
                 expected_value, compiled, subject_compiled):
        self.uid = -1
        self.rule_id = rule_id
        self.kind = kind
        self.symbol = symbol
        self.file = file
        self.line = line
        self.ast_path = ast_path
        self.expr_src = expr_src
        self.expected_value = expected_value
        self.compiled = compiled
        self.subject_compiled = subject_compiled


def _compile(node, filename):
    expr = ast.Expression(body=node)
    ast.fix_missing_locations(expr)
    return compile(expr, filename, "eval")


def _scan_file(path, rule_by_position, candidates, unmapped):
    """Rebuild every universe predicate declared for ``path``.

    ``rule_by_position`` maps (file, line, kind, symbol) -> rule_id.
    Returns the number of predicates rebuilt.
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        source = fh.read()
    tree = ast.parse(source, filename=path)
    filename = path.replace("\\", "/")

    def emit(kind, symbol, line, ast_path, node, expr_src, expected_value, subject):
        rid = rule_by_position.get((filename, line, kind, symbol))
        if rid is None:
            unmapped.append({"file": filename, "line": line, "kind": kind,
                             "symbol": symbol, "ast_path": ast_path})
            return
        try:
            compiled = _compile(node, filename)
            subject_compiled = _compile(subject, filename)
        except BaseException as exc:
            unmapped.append({"file": filename, "line": line, "kind": kind,
                             "symbol": symbol, "ast_path": ast_path,
                             "error": "%s: %s" % (type(exc).__name__, exc)})
            return
        cand = Candidate(rid, kind, symbol, filename, line, ast_path,
                         expr_src, expected_value, compiled, subject_compiled)
        cand.uid = len(candidates)
        candidates.append(cand)

    count = 0
    for node, segs in _walk_with_path(tree):
        if isinstance(node, ast.If):
            line = node.lineno
            path_text = _path_text(segs) + ".test"
            test = node.test
            for symbol, type_node in _isinstance_arg_types(test):
                subject = test.args[0]
                call = ast.Call(func=ast.Name(id="isinstance", ctx=ast.Load()),
                                args=[subject, type_node], keywords=[])
                ast.copy_location(call, test)
                emit("isinstance_ast", symbol, line, path_text, call,
                     ast.unparse(call), "isinstance(ast.%s)" % symbol, subject)
                count += 1
            for symbol in _class_name_tests(test):
                emit("class_name_eq", symbol, line, path_text, test,
                     ast.unparse(test), "class name == '%s'" % symbol, test.left)
                count += 1
            for symbol in _opcode_tests(test):
                left = test.left
                if isinstance(test.ops[0], ast.Eq):
                    expr, expected = test, "== '%s'" % symbol
                elif isinstance(test.comparators[0], (ast.Tuple, ast.List, ast.Set)):
                    expr = ast.Compare(left=left, ops=[ast.Eq()],
                                       comparators=[ast.Constant(value=symbol)])
                    ast.copy_location(expr, test)
                    expected = "== '%s'" % symbol
                else:
                    expr, expected = test, "in %s" % ast.unparse(test.comparators[0])
                emit("opcode_eq", symbol, line, path_text, expr,
                     ast.unparse(expr), expected, left)
                count += 1
        elif isinstance(node, ast.Assign):
            for symbol in _region_assignment(node):
                emit("region_type", symbol, node.lineno, _path_text(segs),
                     node.value, ast.unparse(node), "region_type %s" % symbol, node.value)
                count += 1
    return count


# --------------------------------------------------------------------------- #
# runtime measurement
# --------------------------------------------------------------------------- #
class Measurer(object):
    """Evaluates rule predicates on live frames, once per distinct J pyc."""

    def __init__(self, candidates_by_line, candidates):
        self.candidates = candidates
        self.line_index = candidates_by_line          # (file, line) -> [Candidate]
        self.anchors_by_file = collections.defaultdict(set)
        for (f, line) in self.line_index:
            self.anchors_by_file[f].add(line)
        self.code_cache = {}
        # counters
        self.evaluations = collections.Counter()
        self.evaluations_true = collections.Counter()
        self.evaluations_false = collections.Counter()
        self.errors = collections.Counter()
        self.error_text = {}
        self.true_runs_of_rule = collections.Counter()
        self.false_runs_of_rule = collections.Counter()
        self.pyc_true = {}                            # pyc -> set(rule_id measured true)
        self.pyc_false_evidence = {}                  # pyc -> {rule_id: evidence tuple}
        self.pyc_true_evidence = {}                   # pyc -> {rule_id: evidence tuple}
        self.pyc_false_counts = {}                    # pyc -> {rule_id: n}
        self.run_resolved = set()
        self.current_pyc = None
        self.run_true = collections.Counter()
        self.run_false = collections.Counter()
        self.run_true_ev = {}
        self.run_false_ev = {}

    # -- trace plumbing ---------------------------------------------------- #
    def _code_map(self, code):
        slot = id(code)
        cached = self.code_cache.get(slot)
        if cached is not None:
            return cached[1]
        out = None
        try:
            file = norm(code.co_filename)
            anchors = self.anchors_by_file.get(file)
            if anchors:
                lines = set()
                for _start, _end, line in code.co_lines():
                    if line is not None:
                        lines.add(line)
                common = lines & anchors
                if common:
                    out = (file, common)
        except BaseException:
            out = None
        self.code_cache[slot] = (code, out)          # strong ref: prevents id reuse
        return out

    def global_trace(self, frame, event, arg):
        if event != "call":
            return None
        if self._code_map(frame.f_code) is None:
            return None
        return self.local_trace

    def local_trace(self, frame, event, arg):
        if event != "line":
            return self.local_trace
        cands = self.line_index.get((norm(frame.f_code.co_filename), frame.f_lineno))
        if not cands:
            return self.local_trace
        local_ns = None
        for cand in cands:
            rid = cand.rule_id
            if rid in self.run_resolved:
                continue
            if local_ns is None:
                local_ns = frame.f_locals
            self._evaluate(cand, frame, local_ns)
        return self.local_trace

    # -- evaluation -------------------------------------------------------- #
    def _evidence(self, cand, frame, local_ns, verdict):
        observed = "<not captured>"
        try:
            subject = eval(cand.subject_compiled, frame.f_globals, local_ns)
            if isinstance(subject, type):
                observed = "type=%s" % getattr(subject, "__name__", "?")
            else:
                observed = "type=%s value=%s" % (type(subject).__name__, short_repr(subject))
        except BaseException as exc:
            observed = "<subject unevaluable: %s>" % type(exc).__name__
        return (cand.uid, frame.f_code.co_name, frame.f_code.co_firstlineno,
                frame.f_lasti, verdict, observed)

    def _evaluate(self, cand, frame, local_ns):
        rid = cand.rule_id
        self.evaluations[rid] += 1
        try:
            value = bool(eval(cand.compiled, frame.f_globals, local_ns))
        except BaseException as exc:
            self.errors[rid] += 1
            if rid not in self.error_text:
                self.error_text[rid] = "%s: %s" % (type(exc).__name__, exc)
            return
        if value:
            self.evaluations_true[rid] += 1
            self.run_true[rid] += 1
            if rid not in self.run_true_ev:
                self.run_true_ev[rid] = self._evidence(cand, frame, local_ns, "true")
        else:
            self.evaluations_false[rid] += 1
            self.run_false[rid] += 1
            if rid not in self.run_false_ev:
                self.run_false_ev[rid] = self._evidence(cand, frame, local_ns, "false")
        if self.run_true[rid] and self.run_false[rid]:
            self.run_resolved.add(rid)

    # -- run control ------------------------------------------------------- #
    def begin_run(self, pyc):
        self.current_pyc = pyc
        self.run_resolved = set()
        self.run_true = collections.Counter()
        self.run_false = collections.Counter()
        self.run_true_ev = {}
        self.run_false_ev = {}

    def end_run(self):
        pyc = self.current_pyc
        self.pyc_true[pyc] = {rid for rid, n in self.run_true.items() if n}
        self.pyc_true_evidence[pyc] = dict(self.run_true_ev)
        self.pyc_false_evidence[pyc] = dict(self.run_false_ev)
        self.pyc_false_counts[pyc] = {rid: n for rid, n in self.run_false.items() if n}
        for rid in self.pyc_true[pyc]:
            self.true_runs_of_rule[rid] += 1
        for rid, n in self.pyc_false_counts[pyc].items():
            if rid not in self.pyc_true[pyc]:
                self.false_runs_of_rule[rid] += 1


# --------------------------------------------------------------------------- #
# measurement driver
# --------------------------------------------------------------------------- #
def build_rule_index(universe):
    by_key = {}
    by_position = {}
    for rule in universe.get("rules") or []:
        by_key[(rule.get("kind"), rule.get("symbol"))] = rule
        anchors = list(rule.get("anchors") or [])
        if rule.get("anchor"):
            anchors.append(rule["anchor"])
        seen = set()
        for anchor in anchors:
            text = str(anchor)
            f, _, line = text.rpartition(":")
            try:
                line_no = int(line)
            except ValueError:
                continue
            f = f.replace("\\", "/")
            if (f, line_no) in seen:
                continue
            seen.add((f, line_no))
            by_position[(f, line_no, rule.get("kind"), rule.get("symbol"))] = rule["rule_id"]
    return by_key, by_position


def run_measurement(universe, jspace, verbose=True):
    _by_key, by_position = build_rule_index(universe)
    rules = universe.get("rules") or []
    rule_by_id = {r["rule_id"]: r for r in rules}

    anchor_files = sorted({f for (f, _l, _k, _s) in by_position})
    candidates = []
    unmapped = []
    parse_errors = {}
    for path in anchor_files:
        try:
            _scan_file(path, by_position, candidates, unmapped)
        except BaseException as exc:
            parse_errors[path] = "%s: %s" % (type(exc).__name__, exc)
    candidates_by_line = collections.defaultdict(list)
    located = collections.Counter()
    for cand in candidates:
        candidates_by_line[(cand.file, cand.line)].append(cand)
        located[cand.rule_id] += 1

    entries = jspace.get("entries") or []
    entries_by_pyc = collections.OrderedDict()
    for entry in entries:
        pyc = str(entry.get("pyc") or "").replace("\\", "/")
        if pyc:
            entries_by_pyc.setdefault(pyc, []).append(entry)
    entry_by_id = {e["id"]: e for e in entries if e.get("id")}

    meas = Measurer(candidates_by_line, candidates)
    run_failures = {}
    run_timing = {}
    runs = 0

    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    for pyc in sorted(entries_by_pyc):
        if not os.path.isfile(pyc):
            run_failures[pyc] = "pyc_missing"
            continue
        started = time.perf_counter()
        try:
            with open(pyc, "rb") as fh:
                fh.read(16)
                code = marshal.load(fh)
            meas.begin_run(pyc)
            sys.settrace(meas.global_trace)
            try:
                cfg = build_cfg(code)
                gen = RegionASTGenerator(
                    cfg, top_level_code=code if code.co_name == "<module>" else None)
                ast_dict = gen.generate()
                py_ast = CFGASTConverter().convert(ast_dict)
                CFGCodeGenerator().generate(py_ast)
            finally:
                sys.settrace(None)
            meas.end_run()
            runs += 1
        except BaseException as exc:
            sys.settrace(None)
            run_failures[pyc] = "%s: %s" % (type(exc).__name__, exc)
        run_timing[pyc] = round(time.perf_counter() - started, 3)
        if verbose and runs and runs % 25 == 0:
            print("[rule_proof_check] runs=%d/%d rules_located=%d/%d"
                  % (runs, len(entries_by_pyc), len(located), len(rules)), flush=True)

    return {
        "rule_by_id": rule_by_id,
        "candidates": candidates,
        "located": located,
        "unmapped": unmapped,
        "parse_errors": parse_errors,
        "meas": meas,
        "entries_by_pyc": entries_by_pyc,
        "entry_by_id": entry_by_id,
        "run_failures": run_failures,
        "run_timing": run_timing,
        "runs": runs,
        "anchor_files": anchor_files,
    }


# --------------------------------------------------------------------------- #
# records
# --------------------------------------------------------------------------- #
def _evidence_dict(cand, evidence, predicate_result):
    uid, code_name, code_first, lasti, verdict, observed = evidence
    return {
        "file": cand.file,
        "line": cand.line,
        "ast_path": cand.ast_path,
        "code_object": code_name,
        "code_firstlineno": code_first,
        "bytecode_offset": lasti,
        "predicate": cand.expr_src,
        "predicate_result": predicate_result,
        "observed_value": observed,
        "expected_value": cand.expected_value,
    }


def _occurrence_id(entry_id, ev):
    return "%s|%s:%d|%s|%s@%d" % (entry_id, ev["file"], ev["line"], ev["ast_path"],
                                  ev["code_object"], ev["bytecode_offset"])


def build_records(universe, ctx):
    rules = universe.get("rules") or []
    meas = ctx["meas"]
    candidates = ctx["candidates"]
    entries_by_pyc = ctx["entries_by_pyc"]
    entry_by_id = ctx["entry_by_id"]
    universe_files_sha = ctx["universe_files_sha"]
    trace_hits = ctx["trace_hits"]

    records = []
    for rule in rules:
        rid = rule["rule_id"]
        kind = rule.get("kind")
        symbol = rule.get("symbol")
        reasons = []
        notes = []

        drift_files = []
        for f in (rule.get("source_files") or []):
            declared = universe_files_sha.get(f)
            if declared and declared != text_sha256(f):
                drift_files.append(f)
        drift_files = sorted(set(drift_files))

        evals = meas.evaluations.get(rid, 0)
        located = ctx["located"].get(rid, 0)
        if not located:
            reasons.append(R_NOT_LOCATED)
        if evals and meas.errors.get(rid, 0) >= evals:
            reasons.append(R_UNEVALUABLE)
        trace_entries = sorted(trace_hits.get(rid) or [])
        if trace_entries and not evals:
            reasons.append(R_TRACE_MISMATCH)

        # ---- positive occurrence ---------------------------------------- #
        raise_pyc = None
        for pyc in sorted(meas.pyc_true):
            if rid in meas.pyc_true[pyc]:
                raise_pyc = pyc
                break
        positive = None
        proof = None
        pos_ev = None
        if raise_pyc is not None:
            evidence = meas.pyc_true_evidence.get(raise_pyc, {}).get(rid)
            cand = candidates[evidence[0]] if evidence else None
            if cand is not None:
                pos_ev = _evidence_dict(cand, evidence, "true")
                owners = sorted(e["id"] for e in entries_by_pyc.get(raise_pyc, []))
                positive = owners[0]
                occurrence_id = _occurrence_id(positive, pos_ev)
                hash_input = "|".join([
                    rid, str(rule.get("anchor", "")), occurrence_id, str(kind),
                    pos_ev["observed_value"], pos_ev["expected_value"]])
                proof = {
                    "proof_id": hashlib.sha256(hash_input.encode("utf-8")).hexdigest(),
                    "checker_version": CHECKER_ID,
                    "definition_version": DEFINITION_VERSION,
                    "definition_doc": DEFINITION_DOC,
                    "hash_input_format": ("rule_id|anchor|occurrence_id|predicate_kind|"
                                          "observed_value|expected_value"),
                    "hash_input": hash_input,
                    "rule_id": rid,
                    "anchor": rule.get("anchor", ""),
                    "occurrence_id": occurrence_id,
                    "predicate_kind": kind,
                    "observed_value": pos_ev["observed_value"],
                    "expected_value": pos_ev["expected_value"],
                    "review": None,
                }

        # ---- semantic domain: every J entry owning a measured occurrence -- #
        domain_hosts = set()
        domain_depths = set()
        domain_entries = set()
        for pyc, true_set in meas.pyc_true.items():
            if rid not in true_set:
                continue
            for member in entries_by_pyc.get(pyc, []):
                label = member.get("expected_label") or {}
                if label.get("host"):
                    domain_hosts.add(label["host"])
                if label.get("depth"):
                    domain_depths.add(label["depth"])
                domain_entries.add(member["id"])

        # ---- composition: measured co-occurrence in the same entry run --- #
        # No measured occurrence => no composition at all (never a fabricated
        # co-occurrence, and never a singleton marker without a firing).
        composition = []
        composition_meta = {"source": "measured_true_same_entry", "singleton": False,
                            "cooccurring_rules": 0,
                            "note": "empty: this rule was never measured true, so it has no occurrence to co-occur in"}
        if raise_pyc is not None:
            others = sorted(meas.pyc_true.get(raise_pyc, set()) - {rid})
            if others:
                composition = others
                composition_meta = {"source": "measured_true_same_entry",
                                    "singleton": False,
                                    "cooccurring_rules": len(others)}
            else:
                composition = [SINGLETON]
                composition_meta = {"source": "measured_true_same_entry",
                                    "singleton": True, "cooccurring_rules": 0}
                notes.append("composition_singleton")

        # ---- negative witness ------------------------------------------- #
        def _rank_entries(require_all_false):
            ranked = []
            for pyc in sorted(meas.pyc_false_counts):
                if rid not in meas.pyc_false_counts[pyc]:
                    continue
                if pyc == raise_pyc:
                    continue
                if require_all_false and rid in meas.pyc_true.get(pyc, set()):
                    continue
                for member in sorted(entries_by_pyc.get(pyc, []), key=lambda e: e["id"]):
                    label = member.get("expected_label") or {}
                    form = label.get("form") or member.get("form")
                    host = label.get("host") or member.get("host")
                    if pos_form is not None and pos_host is not None and form == pos_form and host == pos_host:
                        rank = 0
                    elif pos_form is not None and form == pos_form:
                        rank = 1
                    else:
                        rank = 2
                    ranked.append((rank, member["id"], pyc))
            ranked.sort()
            return ranked

        negative = None
        neg_pick = None
        neg_ev = None
        weak_negative = None
        weak_pick = None
        weak_ev = None
        pos_entry = entry_by_id.get(positive) if positive else None
        pos_form = (pos_entry or {}).get("form")
        pos_host = (pos_entry or {}).get("host")
        if positive is not None:
            ranked = _rank_entries(require_all_false=True)
            if ranked:
                rank, negative, neg_pyc = ranked[0]
                neg_pick = ("same_form_host", "same_form", "any")[rank]
                n_evidence = meas.pyc_false_evidence.get(neg_pyc, {}).get(rid)
                if n_evidence is not None:
                    n_cand = candidates[n_evidence[0]]
                    neg_ev = _evidence_dict(n_cand, n_evidence, "false")
                    neg_ev["selection"] = neg_pick
            if neg_ev is None:
                # weaker, labelled fallback: the rule also fires somewhere in that
                # entry's run, but at least one evaluation at the site is false.
                weak = _rank_entries(require_all_false=False)
                if weak:
                    rank, weak_negative, weak_pyc = weak[0]
                    weak_pick = ("same_form_host", "same_form", "any")[rank]
                    w_evidence = meas.pyc_false_evidence.get(weak_pyc, {}).get(rid)
                    if w_evidence is not None:
                        w_cand = candidates[w_evidence[0]]
                        weak_ev = _evidence_dict(w_cand, w_evidence, "false")
                        weak_ev["selection"] = weak_pick
                        weak_ev["weak"] = True
                        notes.append("weak_negative_available")

        # ---- status ------------------------------------------------------ #
        if proof is not None and negative is not None and domain_hosts and domain_depths:
            status = "proved"
            if drift_files:
                notes.append("file_drifted_but_declared_anchor_resolved")
        else:
            status = "open"
            if not evals:
                reasons.append(R_NO_OCCURRENCE)
            elif proof is None:
                reasons.append(R_PREDICATE_FALSE)
            elif negative is None:
                reasons.append(R_NEGATIVE_MISSING)
            else:
                reasons.append(R_OTHER)
            if drift_files:
                reasons.append(R_SOURCE_DRIFT)

        witnesses = {"positive": [positive] if positive else [],
                     "negative": [negative] if negative else []}
        reason_texts = [{"code": code, "text": REASON_TEXT.get(code, code)} for code in reasons]

        records.append({
            "rule_id": rid,
            "status": status,
            "pattern_kind": kind,
            "symbol": symbol,
            "pattern": rule.get("pattern"),
            "anchor": rule.get("anchor"),
            "anchors": rule.get("anchors") or [],
            "proof": proof,
            "witnesses": witnesses,
            "witness_evidence": {"positive": pos_ev, "negative": neg_ev,
                                 "negative_selection": neg_pick,
                                 "weak_negative": weak_ev,
                                 "weak_negative_selection": weak_pick,
                                 "weak_negative_witness": weak_negative},
            "composition": composition,
            "composition_meta": composition_meta,
            "semantic_domain": {
                "hosts": sorted(domain_hosts),
                "depths": sorted(domain_depths),
                "entries": len(domain_entries),
                "source": ("expected_label.host/depth of every J entry whose run measured "
                           "this rule true"),
            },
            "reasons": reason_texts,
            "notes": notes,
            "measurement": {
                "predicate_evaluations": evals,
                "true_evaluations": meas.evaluations_true.get(rid, 0),
                "false_evaluations": meas.evaluations_false.get(rid, 0),
                "error_evaluations": meas.errors.get(rid, 0),
                "first_error": meas.error_text.get(rid),
                "pyc_runs_reaching_site": (meas.true_runs_of_rule.get(rid, 0)
                                           + meas.false_runs_of_rule.get(rid, 0)),
                "pyc_runs_with_true": meas.true_runs_of_rule.get(rid, 0),
                "pyc_runs_false_only": meas.false_runs_of_rule.get(rid, 0),
                "trace_hit_entries": len(trace_entries),
                "anchors_located": located,
                "anchors_declared": len(set(
                    str(a) for a in ((rule.get("anchors") or []) or [rule.get("anchor")]))),
            },
            "source_drift_files": drift_files,
        })
    return records


def summarise(records, universe, ctx):
    total = len(universe.get("rules") or [])
    by_status = collections.Counter(r["status"] for r in records)
    reason_counts = collections.Counter()
    open_flags = collections.Counter()
    for rec in records:
        if rec["status"] == "proved":
            continue
        codes = [x["code"] for x in rec["reasons"]]
        for code in codes:
            open_flags[code] += 1
        if R_NOT_LOCATED in codes:
            primary = R_NOT_LOCATED
        elif R_NO_OCCURRENCE in codes:
            primary = R_NO_OCCURRENCE
        elif R_PREDICATE_FALSE in codes:
            primary = R_PREDICATE_FALSE
        elif R_NEGATIVE_MISSING in codes:
            primary = R_NEGATIVE_MISSING
        else:
            primary = R_OTHER
        reason_counts[primary] += 1

    # trace/runtime agreement, per pyc run (diagnostic only, never a decision)
    trace_by_pyc = ctx.get("trace_by_pyc") or {}
    trace_only = 0
    measured_only = 0
    runs_with_measured_only = 0
    for pyc, true_set in ctx["meas"].pyc_true.items():
        traced = trace_by_pyc.get(pyc, set())
        extra = true_set - traced
        missing = traced - true_set
        trace_only += len(missing)
        measured_only += len(extra)
        if extra:
            runs_with_measured_only += 1

    return {
        "total_rules": total,
        "proved": by_status.get("proved", 0),
        "open": by_status.get("open", 0),
        "open_reasons": dict(sorted(reason_counts.items())),
        "open_reason_flags": dict(sorted(open_flags.items())),
        "proved_with_singleton_composition": sum(
            1 for r in records if r["status"] == "proved" and r["composition_meta"]["singleton"]),
        "positive_witnesses": sum(1 for r in records if r["witnesses"]["positive"]),
        "negative_witnesses": sum(1 for r in records if r["witnesses"]["negative"]),
        "open_with_partial_positive_occurrence": sum(
            1 for r in records if r["status"] == "open" and r["proof"] is not None),
        "rules_without_any_occurrence": sum(
            1 for r in records if r["measurement"]["predicate_evaluations"] == 0),
        "rules_with_measured_true": sum(
            1 for r in records if r["measurement"]["true_evaluations"] > 0),
        "rules_with_false_only_site": sum(
            1 for r in records if r["measurement"]["predicate_evaluations"] > 0
            and r["measurement"]["true_evaluations"] == 0),
        "negative_witness_fallback_same_form": sum(
            1 for r in records if r["witness_evidence"]["negative_selection"] == "same_form"),
        "negative_witness_fallback_any": sum(
            1 for r in records if r["witness_evidence"]["negative_selection"] == "any"),
        "negative_witness_weak_only": sum(
            1 for r in records if r["status"] == "open"
            and r["witness_evidence"]["weak_negative"] is not None),
        "proved_if_weak_negative_accepted": sum(
            1 for r in records if r["status"] == "proved"
            or (r["proof"] is not None and r["witness_evidence"]["weak_negative"] is not None)),
        "rules_with_site_reached_but_never_true": sum(
            1 for r in records if any(x["code"] == R_PREDICATE_FALSE for x in r["reasons"])),
        "rules_with_source_drift": sum(1 for r in records if r["source_drift_files"]),
        "rules_not_located": sum(1 for r in records if not r["measurement"]["anchors_located"]),
        "proved_by_kind": dict(collections.Counter(
            r["pattern_kind"] for r in records if r["status"] == "proved")),
        "open_by_kind": dict(collections.Counter(
            r["pattern_kind"] for r in records if r["status"] == "open")),
        "proved_with_some_stale_anchor": sum(
            1 for r in records if r["status"] == "proved"
            and r["measurement"]["anchors_located"] < r["measurement"]["anchors_declared"]),
        "trace_runtime": {
            "traced_rules_never_measured_true": trace_only,
            "measured_true_rules_not_in_traces": measured_only,
            "runs_with_measured_true_outside_traces": runs_with_measured_only,
        },
    }


def patch_manifest(manifest, records):
    out = json.loads(json.dumps(manifest))
    by_id = {r["rule_id"]: r for r in records}
    for item in out.get("rules") or []:
        rid = item.get("universe_id") or item.get("rule_id")
        rec = by_id.get(rid)
        if rec is None:
            continue
        item["witnesses"] = {"positive": list(rec["witnesses"]["positive"]),
                             "negative": list(rec["witnesses"]["negative"])}
        item["semantic_domain"] = {
            "hosts": list(rec["semantic_domain"]["hosts"]),
            "depths": list(rec["semantic_domain"]["depths"]),
            "note": "measured by rule_proof_check (v1 draft) from the owning J entries",
        }
        item["composition"] = list(rec["composition"])
        item["composition_meta"] = rec["composition_meta"]
        # Invariant kept on purpose: a rule that is not proved never carries a
        # proof_id in the manifest, so nobody can flip status by hand and get a
        # "ready" count for free.  A measured positive occurrence of an open rule
        # is still preserved below, as evidence for review.
        if rec["status"] == "proved" and rec["proof"]:
            item["proof"] = {
                "proof_id": rec["proof"]["proof_id"],
                "checker_version": rec["proof"]["checker_version"],
                "definition_version": rec["proof"]["definition_version"],
                "occurrence_id": rec["proof"]["occurrence_id"],
                "counterexample_bound": None,
                "review": None,
            }
            item["v1_draft"] = {"checker": CHECKER_ID,
                                "definition": DEFINITION_VERSION,
                                "reasons": [x["code"] for x in rec["reasons"]],
                                "notes": rec["notes"]}
        else:
            item["proof"] = {"proof_id": None, "checker_version": CHECKER_ID,
                             "counterexample_bound": None, "review": None}
            item["v1_draft"] = {"checker": CHECKER_ID,
                                "definition": DEFINITION_VERSION,
                                "reasons": [x["code"] for x in rec["reasons"]],
                                "notes": rec["notes"],
                                "partial_positive_occurrence": (
                                    None if not rec["proof"] else {
                                        "occurrence_id": rec["proof"]["occurrence_id"],
                                        "observed_value": rec["proof"]["observed_value"],
                                        "expected_value": rec["proof"]["expected_value"],
                                        "candidate_proof_id": rec["proof"]["proof_id"],
                                        "why_not_proved": "no strict negative witness; this is "
                                                          "evidence only, not a proof",
                                    })}
        item["status"] = rec["status"]
    out["v1_candidate"] = {
        "produced_by": CHECKER_ID,
        "definition": DEFINITION_VERSION,
        "definition_doc": DEFINITION_DOC,
        "status": "CANDIDATE for review -- manifest_v2.json is untouched; G4 is NOT claimed",
        "base_manifest_sha256": digest(manifest),
    }
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def repo_root(start):
    cur = os.path.abspath(start)
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot locate repo root (no core/cfg above %s)" % start)
        cur = parent
    return cur


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G4 rule proof / composition checker (v1 draft)")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--jspace", required=True)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest-out", default="")
    parser.add_argument("--json", default="")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)

    # resolve every path before changing directory, so relative arguments are
    # interpreted against the caller's cwd
    args.universe = os.path.abspath(args.universe)
    args.manifest = os.path.abspath(args.manifest)
    args.jspace = os.path.abspath(args.jspace)
    args.traces = os.path.abspath(args.traces)
    args.out = os.path.abspath(args.out)
    if args.manifest_out:
        args.manifest_out = os.path.abspath(args.manifest_out)
    if args.json:
        args.json = os.path.abspath(args.json)

    root = repo_root(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    os.chdir(root)

    universe = load(args.universe)
    manifest = load(args.manifest)
    jspace = load(args.jspace)
    traces = load(args.traces)

    trace_hits = collections.defaultdict(list)
    trace_by_pyc = collections.defaultdict(set)
    rule_pyc = {}
    for entry in jspace.get("entries") or []:
        if entry.get("id"):
            rule_pyc[entry["id"]] = str(entry.get("pyc") or "").replace("\\", "/")
    for item in traces.get("records") or []:
        eid = item.get("entry_id") or item.get("id")
        if not eid:
            continue
        rule_ids = item.get("rule_ids") or []
        pyc = rule_pyc.get(eid, "")
        if pyc:
            trace_by_pyc[pyc].update(rule_ids)
        for rid in rule_ids:
            trace_hits[rid].append(eid)

    universe_files_sha = {}
    for meta in universe.get("files") or []:
        path = meta.get("path")
        if path:
            universe_files_sha[str(path).replace("\\", "/")] = meta.get("sha256")

    input_meta = {
        "universe": {"path": os.path.abspath(args.universe).replace("\\", "/"),
                     "sha256": file_sha256(args.universe),
                     "total_rules": universe.get("total_rules")},
        "manifest": {"path": os.path.abspath(args.manifest).replace("\\", "/"),
                     "sha256": file_sha256(args.manifest)},
        "jspace": {"path": os.path.abspath(args.jspace).replace("\\", "/"),
                   "sha256": file_sha256(args.jspace),
                   "entries": len(jspace.get("entries") or [])},
        "traces": {"path": os.path.abspath(args.traces).replace("\\", "/"),
                   "sha256": file_sha256(args.traces),
                   "records": len(traces.get("records") or [])},
    }

    started = time.perf_counter()
    n_pyc = len({p for p in rule_pyc.values() if p})
    if not args.quiet:
        print("[rule_proof_check] rebuilding predicates, then %d distinct J pyc runs ..." % n_pyc,
              flush=True)
    ctx = run_measurement(universe, jspace, verbose=not args.quiet)
    ctx["trace_hits"] = trace_hits
    ctx["trace_by_pyc"] = trace_by_pyc
    ctx["universe_files_sha"] = universe_files_sha
    ctx["input_meta"] = input_meta

    records = build_records(universe, ctx)
    counts = summarise(records, universe, ctx)
    candidate_manifest = patch_manifest(manifest, records)

    preview = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import rule_manifest
        result = dict(rule_manifest.check(universe, candidate_manifest, jspace, traces))
        empty_cov_rules = sorted(rid for rid, cov in (result.pop("coverage", {}) or {}).items()
                                 if not cov)
        result["empty_cov_rules"] = empty_cov_rules
        result["note"] = ("REHEARSAL ONLY: rule_manifest.check() executed in-process against the "
                          "candidate manifest. This is a projection, not a G4 PASS.")
        preview = result
    except BaseException as exc:
        preview = {"error": "%s: %s" % (type(exc).__name__, exc)}

    payload = {
        "tool": "rule_proof_check",
        "version": TOOL_VERSION,
        "checker_id": CHECKER_ID,
        "definition": {
            "version": DEFINITION_VERSION,
            "doc": DEFINITION_DOC,
            "status": "draft_for_review",
            "proves": ("the rule predicate holds at a measured, executed occurrence of the rule's "
                       "anchor, and fails at another measured, executed occurrence in another J entry"),
            "does_not_prove": [
                "rule semantic correctness",
                "that the rule's effect/output is the intended one",
                "anything about rules with no occurrence (the empty_cov set)",
                "semantic interaction correctness of a composition",
            ],
            "proof_id": ("sha256(rule_id|anchor|occurrence_id|predicate_kind|"
                         "observed_value|expected_value)"),
            "occurrence_id": "entry_id|file:line|ast_path|code_object@bytecode_offset",
            "composition": ("rules measured true in the same J entry / same region-reduction run; "
                            "['<singleton>'] (labelled) when no co-occurrence was measured"),
            "negative_witness": ("another J entry whose run reaches the same anchor site and whose "
                                 "predicate is strictly false there"),
        },
        "inputs": input_meta,
        "runs": {
            "distinct_pyc_runs": ctx["runs"],
            "distinct_j_entries": len(ctx["entry_by_id"]),
            "run_failures": ctx["run_failures"],
            "runtime_seconds": round(sum(ctx["run_timing"].values()), 1),
            "candidates_located": len(ctx["candidates"]),
            "unmapped_source_predicates": len(ctx["unmapped"]),
            "unmapped_examples": ctx["unmapped"][:10],
            "parse_errors": ctx["parse_errors"],
            "anchor_files": ctx["anchor_files"],
        },
        "counts": counts,
        "g4_check_rehearsal": preview,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "rules": records,
    }

    write_json(args.out, payload)
    manifest_out = args.manifest_out or os.path.join(
        os.path.dirname(os.path.abspath(args.out)), "manifest_proved_v1.json")
    write_json(manifest_out, candidate_manifest)
    if args.json:
        write_json(args.json, {
            "counts": counts,
            "runs": payload["runs"],
            "g4_check_rehearsal": preview,
            "records": [{"rule_id": r["rule_id"], "status": r["status"],
                         "reasons": [x["code"] for x in r["reasons"]],
                         "notes": r["notes"]} for r in records]})

    print("[rule_proof_check] total=%d proved=%d open=%d open_reasons=%s"
          % (counts["total_rules"], counts["proved"], counts["open"],
             json.dumps(counts["open_reasons"], ensure_ascii=False, sort_keys=True)))
    print("[rule_proof_check] witness_pos=%d witness_neg=%d no_occurrence=%d "
          "singleton_composition=%d drift_rules=%d weak_negative_only=%d "
          "proved_if_weak=%d runtime=%.1fs"
          % (counts["positive_witnesses"], counts["negative_witnesses"],
             counts["rules_without_any_occurrence"],
             counts["proved_with_singleton_composition"],
             counts["rules_with_source_drift"],
             counts["negative_witness_weak_only"],
             counts["proved_if_weak_negative_accepted"],
             payload["elapsed_seconds"]))
    if preview and "error" not in preview:
        print("[rule_proof_check] REHEARSAL rule_manifest --check: proved=%d ready=%d not_ready=%d "
              "empty_cov=%d G4=%s reason=%s"
              % (preview.get("proved"), preview.get("ready_proved"),
                 preview.get("not_ready_proved"), preview.get("empty_cov"),
                 preview.get("g4"), preview.get("reason")))
    print("[rule_proof_check] wrote %s" % args.out)
    print("[rule_proof_check] wrote %s" % manifest_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
