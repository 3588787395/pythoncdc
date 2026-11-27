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

Revision 1.1.0 -- two measurement-scope defects were repaired in this file
only (the universe, manifest, J space and traces are untouched):

    D1  ONE evaluation scope per construct.  A membership guard
        ``x.opname in ('A', 'B', 'C')`` used to be projected, for the rule of
        member ``'B'``, into ``x.opname == 'B'`` -- while a guard written as
        ``x.opname in NAMED_SET`` was evaluated as the whole guard.  The same
        construct therefore had two semantics.  From 1.1.0 every membership
        guard is evaluated as the guard itself (``observed in {members}``);
        the per-member projection is still measured, but only as a labelled
        diagnostic (``member_projection``) that never decides a status.
    D2  kind accounting.  ``OP_NAMES`` used to mix opcode attributes with IR
        marker attributes, so ``node_type == 'X'`` / ``name == 'X'`` rules were
        reported as ``opcode_eq``.  The attribute sets are now separate and
        every record carries a ``pattern_class`` derived from the rebuilt
        predicate (``opcode_eq``, ``opcode_in_set``, ``opcode_in_named_set``,
        ``ast_marker_eq``, ``ast_marker_in_set``, ``ast_marker_in_named_set``,
        ``isinstance_ast``, ``class_name_eq``, ``region_type``).  The universe
        kind is preserved as ``universe_kind``/``pattern_kind``.

Revision 1.2.0 -- counting policy for guard-only rules (G4_REVIEW_PACKET
adjudication 2).  New ``--counting {b1,b2}`` switch, default ``b1``:

    b1  (default, adjudication 2's recommended reading)  ``proved`` additionally
        requires ``symbol_observed=True``.  A rule that b2 would prove only
        because its whole guard was measured true while the rule's own symbol
        was never observed (``guard_only=True``, ``symbol_observed=False``) is
        downgraded to ``open`` with the new reason code
        ``guard_only_symbol_not_observed``; the would-be status is kept on the
        record as the ``b1_downgrade`` diagnostic (``b2_status``).
    b2  the 1.1.0 counting, bit for bit: guard-only rules stay ``proved`` and
        no record carries ``b1_downgrade``.  ``--counting b2`` exists so the
        old readings stay exactly reproducible.

No measurement semantics changed in 1.2.0: predicate evaluation, witness
collection, ``--also-legacy`` and ``--structural-negative`` are untouched;
b1/b2 only re-classifies rules *after* the measurement.

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

TOOL_VERSION = "1.2.0"
DEFINITION_VERSION = ("G4 proof theory v1.1 (draft, pending review; guard-scope predicates "
                      "and separate IR-marker kinds)")
DEFINITION_DOC = "fresh/gate_g4/G4_PROOF_THEORY.md"
CHECKER_ID = "rule_proof_check/%s" % TOOL_VERSION
SINGLETON = "<singleton>"

# Mirrors tools/completeness/rule_universe.py::OP_NAMES (that file is read-only
# for this tool; the scanner semantics are re-stated here, never imported
# mutably and never altered).  OP_NAMES stays the union so that *which tests
# the scanner rebuilds* is unchanged; the two halves are kept apart so that a
# rebuilt predicate can be classified without mixing opcodes and IR markers
# (defect D2 in fresh/gate_g4/G4_D3_TRIAGE.md §6).
OPCODE_NAMES = {"opname", "opcode"}
IR_MARKER_NAMES = {"name", "kind", "node_type", "node_name"}
OP_NAMES = OPCODE_NAMES | IR_MARKER_NAMES

# Lookup order used to map a rebuilt predicate back to a universe rule: the
# derived class first, then every kind the universe scanner may have declared.
UNIVERSE_MATCH_KINDS = ("opcode_eq", "isinstance_ast", "class_name_eq", "region_type")

GUARD_EQ = "eq"
GUARD_IN_LITERAL = "in_literal"
GUARD_IN_NAME = "in_name"

R_NO_OCCURRENCE = "no_occurrence_in_J"
R_PREDICATE_FALSE = "predicate_false_at_site"
R_NEGATIVE_MISSING = "negative_witness_missing"
R_NOT_LOCATED = "predicate_not_located"
R_UNEVALUABLE = "predicate_unevaluable"
R_SOURCE_DRIFT = "anchor_source_drift"
R_TRACE_MISMATCH = "trace_runtime_disagreement"
R_GUARD_ONLY = "guard_only_symbol_not_observed"
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
    R_GUARD_ONLY: ("b1 conservative counting (G4_REVIEW_PACKET adjudication 2, recommended): "
                   "the predicate was measured true only as the whole guard and the rule's own "
                   "symbol was never observed, so the occurrence is diagnostic evidence, not a proof"),
    R_OTHER: "open for another reason; see notes",
}


# --------------------------------------------------------------------------- #
# Ruling 4 (ROW4 stage 3, 裁决四): explicit per-rule structural-negative
# exemptions.
#
# Ruling 4 admits two airtight structural patterns:
#
#   (i) chain tail: the predicate is the chain tail of a fully enumerated
#       dominating guard (every evaluation that reaches it is true);
#  (ii) true-bound compiler guarantee: the opcode is emitted by the CPython
#       compiler into every 3.11+ module code object (RESUME first;
#       LOAD_CONST None; RETURN_VALUE last), so every decompile run that
#       produces any evaluation at all has already measured the rule true,
#       and a false-only run (the strict 4.1(3) negative) cannot exist in
#       any Python-3.11+ J space.
#
# Registration is per rule (never per category) and must carry:
#   * positive witness evidence: the J entry id that measured the predicate
#     true, plus the minimum number of true evaluations it produced;
#   * the structural evidence: for pattern (i) the dominating guard's full
#     member enumeration and the elif ladder (line -> member) with the
#     chain-tail position; for pattern (ii) the compiler guarantees and the
#     measured run coverage (runs-with-true vs runs-false-only);
#   * a rationale naming why a strict negative is structurally impossible.
#
# Like --structural-negative itself, the exemption is adjudication-only and
# zero-perturbation: it never changes a measurement, never fabricates an
# occurrence, and never mints a negative witness; it only reclassifies the
# verdict, and only when the measured evidence matches the registration
# (positive witness entry is a measured true owner, the measured true
# evaluations meet the registered minimum, and the anchor matches).  The G4
# output counts exempted proved rules separately from strict proved rules.
# --------------------------------------------------------------------------- #
STRUCTURAL_NEGATIVE_EXEMPTIONS = {
    "RULE-a310f7ea600b": {
        "symbol": "PREP_RERAISE_STAR",
        "positive_witness_entry": "JS-EXCEPTSTAR-001",
        "min_true_evaluations": 6,
        "anchor": "core/cfg/ast_generator_v2.py:23499",
        "dominating_guard": {
            "file": "core/cfg/ast_generator_v2.py",
            "guard_line": 23464,
            "guard_kind": "opcode_in_literal",
            "guard_members": [
                "PUSH_EXC_INFO", "WITH_EXCEPT_START", "POP_EXCEPT", "RERAISE",
                "CHECK_EXC_MATCH", "CHECK_EG_MATCH", "PREP_RERAISE_STAR",
            ],
            "elif_ladder": [
                [23467, "PUSH_EXC_INFO"],
                [23475, "WITH_EXCEPT_START"],
                [23480, "POP_EXCEPT"],
                [23484, "RERAISE"],
                [23489, "CHECK_EXC_MATCH"],
                [23494, "CHECK_EG_MATCH"],
                [23499, "PREP_RERAISE_STAR"],
            ],
            "elif_chain_tail_line": 23499,
        },
        "rationale": (
            "The predicate `opname == 'PREP_RERAISE_STAR'` (agv2 L23499) is the chain tail "
            "of the elif ladder under the dominating seven-member guard at agv2 L23464 "
            "('[R215-STAGE2-A1]'): reaching the tail requires opname to be in the guard set "
            "and different from all six preceding elif members, so every evaluation of the "
            "predicate is true and a strict negative occurrence is structurally impossible "
            "(measured: 6 true evaluations, 0 false). The registered positive witness "
            "JS-EXCEPTSTAR-001 (except* raise-star host) measured the predicate true; the "
            "ruling was accepted in r216 (ROW4 裁决四, 249-basis proved 145 = 144 strict + "
            "1 structural exemption)."
        ),
    },
    # ---- pattern (ii): true-bound compiler guarantee (ROW4 stage 3 Phase B,
    # r217 adjudication) ----------------------------------------------- #
    "RULE-2b6f0dcd703d": {
        "symbol": "RETURN_VALUE",
        "pattern": "true_bound_compiler_guarantee",
        "positive_witness_entry": "JS-B1-N22E",
        "min_true_evaluations": 319,
        "anchor": "core/cfg/ast_generator_v2.py:1895",
        "structural_evidence": {
            "compiler_guarantee": (
                "Every CPython 3.11+ module code object ends with "
                "'LOAD_CONST None; RETURN_VALUE' (implicit return None); the "
                "pyc root is exactly such a module code object."
            ),
            "measured_v4": {
                "runs_with_true": 163, "runs_false_only": 0,
                "true_evaluations": 319, "false_evaluations": 173,
                "anchors_located": 151, "anchors_declared": 151,
            },
        },
        "rationale": (
            "RETURN_VALUE (agv2 L1895, 'elif opname in (RETURN_VALUE, "
            "RETURN_CONST)') is true-bound: the CPython compiler emits "
            "'LOAD_CONST None; RETURN_VALUE' at the tail of every module code "
            "object, both decompile pipelines process the pyc root code object "
            "first, and the dispatch ladders containing this rule's anchors "
            "see those instructions, so every run that evaluates any anchor at "
            "all has already measured the rule true (v4: 163/163 runs true, 0 "
            "false-only runs; all 173 false evaluations fall inside true-owning "
            "runs).  A strict 4.1(3) negative requires a false-only run, which "
            "no Python-3.11+ J space can contain.  Positive witness "
            "JS-B1-N22E (n22_getlen, explicit returns) measured the rule true."
        ),
    },
    "RULE-e7701666d7b5": {
        "symbol": "RESUME",
        "pattern": "true_bound_compiler_guarantee",
        "positive_witness_entry": "JS-B1-N22P",
        "min_true_evaluations": 318,
        "anchor": "core/cfg/ast_generator_v2.py:2680",
        "structural_evidence": {
            "compiler_guarantee": (
                "Every CPython 3.11+ code object begins with RESUME; the pyc "
                "root module code object is the first thing both decompile "
                "pipelines process."
            ),
            "measured_v4": {
                "runs_with_true": 163, "runs_false_only": 0,
                "true_evaluations": 318, "false_evaluations": 163,
                "anchors_located": 167, "anchors_declared": 167,
            },
        },
        "rationale": (
            "RESUME (agv2 L2680, 'elif opname == RESUME') is true-bound: every "
            "CPython 3.11+ code object starts with RESUME, so the very first "
            "instruction the analyzers process TRUEs the rule's anchor ladders "
            "in every run (v4: 163/163 runs true, 0 false-only runs; all 163 "
            "false evaluations fall inside true-owning runs).  A strict "
            "4.1(3) negative requires a false-only run, which no "
            "Python-3.11+ J space can contain.  Positive witness JS-B1-N22P "
            "(n22_pjbi) measured the rule true."
        ),
    },
    "RULE-ed5bec7d7a05": {
        "symbol": "LOAD_CONST",
        "pattern": "true_bound_compiler_guarantee",
        "positive_witness_entry": "JS-B1-N22T",
        "min_true_evaluations": 261,
        "anchor": "core/cfg/ast_generator_v2.py:1080",
        "structural_evidence": {
            "compiler_guarantee": (
                "Every CPython 3.11+ module code object ends with "
                "'LOAD_CONST None; RETURN_VALUE' (implicit return None), so a "
                "LOAD_CONST instruction is present in every pyc root even for "
                "an otherwise empty module."
            ),
            "measured_v4": {
                "runs_with_true": 163, "runs_false_only": 0,
                "true_evaluations": 261, "false_evaluations": 167,
                "anchors_located": 94, "anchors_declared": 94,
            },
        },
        "rationale": (
            "LOAD_CONST (agv2 L1080, \"if opname in ('LOAD_CONST', "
            "'LOAD_CONSTANT')\") is true-bound: the compiler's implicit "
            "'return None' emits 'LOAD_CONST None' into every module code "
            "object, both decompile pipelines process the pyc root code object, "
            "and the dispatch ladders containing this rule's anchors see that "
            "instruction, so every run that evaluates any anchor at all has "
            "already measured the rule true (v4: 163/163 runs true, 0 "
            "false-only runs; all 167 false evaluations fall inside "
            "true-owning runs).  A strict 4.1(3) negative requires a "
            "false-only run, which no Python-3.11+ J space can contain.  "
            "Positive witness JS-B1-N22T (n22_spec_tuple, const-laden "
            "f-string) measured the rule true."
        ),
    },
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


def _marker_test(leaf) -> bool:
    """True when the guard's subject attribute is an IR marker, not an opcode."""
    return leaf in IR_MARKER_NAMES


def _guard_tests(test):
    """Rebuild the rule predicates carried by one ``if`` condition.

    Returns one spec per universe rule that this condition can carry.  One
    scope is used for every membership guard (defect D1): the rebuilt
    predicate is the *whole* guard, whether the members are written inline
    (``x.opname in ('A', 'B')``) or named (``x.opname in NAMED_SET``).  The
    per-member projection ``x.opname == 'A'`` is returned separately as
    ``projection`` and is only ever a diagnostic.

    A spec is a dict with:
        symbol         the universe ``symbol`` this rule is keyed by
        pattern_class  the derived predicate class (D2 accounting)
        guard          ``eq`` / ``in_literal`` / ``in_name``
        members        tuple of literal members, or None when not literal
        projection     ``ast.Compare`` for ``subject == symbol`` or None
        node           the AST node to compile as the rule predicate
    """
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return []
    left, op, right = test.left, test.ops[0], test.comparators[0]
    leaf = _op_name(left)
    if leaf not in OP_NAMES:
        return []
    marker = _marker_test(leaf)
    if isinstance(op, ast.Eq) and _str_constant(right):
        return [{"symbol": _str_constant(right),
                 "pattern_class": "ast_marker_eq" if marker else "opcode_eq",
                 "guard": GUARD_EQ, "members": None, "projection": None,
                 "node": test}]
    if isinstance(op, ast.In):
        container = right
        if isinstance(container, (ast.Tuple, ast.List, ast.Set)):
            members = tuple(v for v in (_str_constant(x) for x in container.elts) if v)
            if not members:
                return []
            out = []
            for member in members:
                projection = ast.Compare(left=left, ops=[ast.Eq()],
                                         comparators=[ast.Constant(value=member)])
                ast.copy_location(projection, test)
                out.append({"symbol": member,
                            "pattern_class": ("ast_marker_in_set" if marker
                                              else "opcode_in_set"),
                            "guard": GUARD_IN_LITERAL, "members": members,
                            "projection": projection, "node": test})
            return out
        if isinstance(container, (ast.Name, ast.Attribute)):
            return [{"symbol": ast.unparse(container),
                     "pattern_class": ("ast_marker_in_named_set" if marker
                                       else "opcode_in_named_set"),
                     "guard": GUARD_IN_NAME, "members": None, "projection": None,
                     "node": test}]
    return []


def _opcode_tests(test):
    """Backwards-compatible view: the symbols only (kept for older importers)."""
    return [spec["symbol"] for spec in _guard_tests(test)]


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
                 "expr_src", "expected_value", "compiled", "subject_compiled",
                 "pattern_class", "guard", "members", "projection_src",
                 "projection_compiled")

    def __init__(self, rule_id, kind, symbol, file, line, ast_path, expr_src,
                 expected_value, compiled, subject_compiled,
                 pattern_class=None, guard=GUARD_EQ, members=None,
                 projection_src=None, projection_compiled=None):
        self.uid = -1
        self.rule_id = rule_id
        self.kind = kind                              # universe (matched) kind
        self.symbol = symbol
        self.file = file
        self.line = line
        self.ast_path = ast_path
        self.expr_src = expr_src
        self.expected_value = expected_value
        self.compiled = compiled
        self.subject_compiled = subject_compiled
        self.pattern_class = pattern_class or kind
        self.guard = guard
        self.members = members
        self.projection_src = projection_src
        self.projection_compiled = projection_compiled

    # -- read-only views used by the records -------------------------------- #
    @property
    def predicate_scope(self) -> str:
        if self.members:
            return "guard"
        if self.guard == GUARD_IN_NAME:
            return "guard"
        return "member"


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

    def lookup(kind, symbol, line):
        for key_kind in (kind,) + UNIVERSE_MATCH_KINDS:
            rid = rule_by_position.get((filename, line, key_kind, symbol))
            if rid is not None:
                return rid, key_kind
        return None, None

    def emit(kind, symbol, line, ast_path, node, expr_src, expected_value, subject,
             pattern_class=None, guard=GUARD_EQ, members=None,
             projection=None, projection_src=None):
        rid, matched_kind = lookup(kind, symbol, line)
        if rid is None:
            unmapped.append({"file": filename, "line": line, "kind": kind,
                             "symbol": symbol, "ast_path": ast_path})
            return
        try:
            compiled = _compile(node, filename)
            subject_compiled = _compile(subject, filename)
            projection_compiled = _compile(projection, filename) if projection is not None else None
        except BaseException as exc:
            unmapped.append({"file": filename, "line": line, "kind": kind,
                             "symbol": symbol, "ast_path": ast_path,
                             "error": "%s: %s" % (type(exc).__name__, exc)})
            return
        cand = Candidate(rid, matched_kind, symbol, filename, line, ast_path,
                         expr_src, expected_value, compiled, subject_compiled,
                         pattern_class=pattern_class or kind, guard=guard,
                         members=members, projection_src=projection_src,
                         projection_compiled=projection_compiled)
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
                     ast.unparse(call), "isinstance(ast.%s)" % symbol, subject,
                     pattern_class="isinstance_ast")
                count += 1
            for symbol in _class_name_tests(test):
                emit("class_name_eq", symbol, line, path_text, test,
                     ast.unparse(test), "class name == '%s'" % symbol, test.left,
                     pattern_class="class_name_eq")
                count += 1
            for spec in _guard_tests(test):
                symbol = spec["symbol"]
                left = test.left
                node_src = spec["node"]
                if spec["guard"] == GUARD_EQ:
                    expected = "== '%s'" % symbol
                elif spec["guard"] == GUARD_IN_LITERAL:
                    expected = "in (%s)" % ", ".join("'%s'" % m for m in spec["members"])
                else:
                    expected = "in %s" % ast.unparse(test.comparators[0])
                projection = spec["projection"]
                emit("opcode_eq", symbol, line, path_text, node_src,
                     ast.unparse(node_src), expected, left,
                     pattern_class=spec["pattern_class"], guard=spec["guard"],
                     members=spec["members"], projection=projection,
                     projection_src=(ast.unparse(projection)
                                     if projection is not None else None))
                count += 1
        elif isinstance(node, ast.Assign):
            for symbol in _region_assignment(node):
                emit("region_type", symbol, node.lineno, _path_text(segs),
                     node.value, ast.unparse(node), "region_type %s" % symbol, node.value,
                     pattern_class="region_type")
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
        # -- D1 diagnostic: the per-member projection, measured but never -- #
        # -- used for a status (see the class docstring) ------------------- #
        self.projection_evaluations = collections.Counter()
        self.projection_true = collections.Counter()
        self.projection_false = collections.Counter()
        self.guard_true_projection_false = collections.Counter()
        self.run_projection_true = collections.Counter()
        self.pyc_projection_true = {}                 # pyc -> set(rule_id)
        # per-candidate truth, so a rule with several anchors is judged on the
        # candidate that actually fired (a rule can mix a member equality and a
        # membership guard at different anchors)
        self.cand_true = collections.Counter()        # uid -> true evaluations
        self.cand_projection_true = collections.Counter()  # uid -> projection true

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
    def _evidence(self, cand, frame, local_ns, verdict, projection=None):
        observed = "<not captured>"
        member_note = "n/a"
        try:
            subject = eval(cand.subject_compiled, frame.f_globals, local_ns)
            if isinstance(subject, type):
                observed = "type=%s" % getattr(subject, "__name__", "?")
            else:
                observed = "type=%s value=%s" % (type(subject).__name__, short_repr(subject))
            if cand.members:
                if isinstance(subject, str):
                    member_note = ("matched_member=%r" % subject
                                   if subject in cand.members
                                   else "subject_not_in_guard_members")
                else:
                    member_note = "subject_not_a_string"
            elif cand.guard == GUARD_IN_NAME:
                member_note = "named_set_member_of_%s" % cand.symbol
        except BaseException as exc:
            observed = "<subject unevaluable: %s>" % type(exc).__name__
        return (cand.uid, frame.f_code.co_name, frame.f_code.co_firstlineno,
                frame.f_lasti, verdict, observed, member_note, projection)

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
        # One scope for every guard (D1): ``value`` is the guard itself.  The
        # per-member projection is measured only when the guard is true -- it
        # cannot be true when the guard is false -- and is labelled diagnostic.
        projection = None
        if value and cand.projection_compiled is not None:
            self.projection_evaluations[rid] += 1
            try:
                projection = bool(eval(cand.projection_compiled, frame.f_globals, local_ns))
            except BaseException:
                projection = None
            if projection is True:
                self.projection_true[rid] += 1
                self.run_projection_true[rid] += 1
                self.cand_projection_true[cand.uid] += 1
            elif projection is False:
                self.projection_false[rid] += 1
                self.guard_true_projection_false[rid] += 1
        if value:
            self.evaluations_true[rid] += 1
            self.run_true[rid] += 1
            self.cand_true[cand.uid] += 1
            if rid not in self.run_true_ev:
                self.run_true_ev[rid] = self._evidence(cand, frame, local_ns, "true",
                                                       projection)
        else:
            self.evaluations_false[rid] += 1
            self.run_false[rid] += 1
            if rid not in self.run_false_ev:
                self.run_false_ev[rid] = self._evidence(cand, frame, local_ns, "false",
                                                        projection)
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
        self.run_projection_true = collections.Counter()

    def end_run(self):
        pyc = self.current_pyc
        self.pyc_true[pyc] = {rid for rid, n in self.run_true.items() if n}
        self.pyc_true_evidence[pyc] = dict(self.run_true_ev)
        self.pyc_false_evidence[pyc] = dict(self.run_false_ev)
        self.pyc_false_counts[pyc] = {rid: n for rid, n in self.run_false.items() if n}
        self.pyc_projection_true[pyc] = {rid for rid, n in self.run_projection_true.items() if n}
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


def run_measurement(universe, jspace, verbose=True, also_legacy=False):
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
    candidates_by_rule = collections.defaultdict(list)
    located = collections.Counter()
    for cand in candidates:
        candidates_by_line[(cand.file, cand.line)].append(cand)
        candidates_by_rule[cand.rule_id].append(cand)
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
    partial_failures = {}
    run_timing = {}
    runs = 0

    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.ast_converter import CFGASTConverter
    from core.cfg.code_generator import CFGCodeGenerator

    generate_ast_v2 = None
    if also_legacy:
        # ``core/cfg/__init__.py`` exports the v2 generator as ``generate_ast`` /
        # ``ASTGenerator`` and ``decompile(use_region=False)`` runs it, so it is a
        # shipped entry of the same package.  Measured only when asked for.
        from core.cfg.ast_generator_v2 import generate_ast_v2 as _gen_v2

        generate_ast_v2 = _gen_v2
    pipelines = ["region"] + (["legacy_v2"] if generate_ast_v2 is not None else [])
    expected_pipelines = len(pipelines)

    for pyc in sorted(entries_by_pyc):
        if not os.path.isfile(pyc):
            run_failures[pyc] = "pyc_missing"
            continue
        started = time.perf_counter()
        failures = []
        try:
            with open(pyc, "rb") as fh:
                fh.read(16)
                code = marshal.load(fh)
            meas.begin_run(pyc)
            try:
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
            except BaseException as exc:
                failures.append("region: %s: %s" % (type(exc).__name__, exc))
            if generate_ast_v2 is not None:
                try:
                    sys.settrace(meas.global_trace)
                    try:
                        ast_dict_v2 = generate_ast_v2(build_cfg(code))
                        py_ast_v2 = CFGASTConverter().convert(ast_dict_v2)
                        CFGCodeGenerator().generate(py_ast_v2)
                    finally:
                        sys.settrace(None)
                except BaseException as exc:
                    failures.append("legacy_v2: %s: %s" % (type(exc).__name__, exc))
            meas.end_run()
            runs += 1
            if len(failures) >= expected_pipelines:
                run_failures[pyc] = "; ".join(failures)
            elif failures:
                partial_failures[pyc] = "; ".join(failures)
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
        "candidates_by_rule": candidates_by_rule,
        "located": located,
        "unmapped": unmapped,
        "parse_errors": parse_errors,
        "meas": meas,
        "entries_by_pyc": entries_by_pyc,
        "entry_by_id": entry_by_id,
        "run_failures": run_failures,
        "partial_failures": partial_failures,
        "pipelines": pipelines,
        "run_timing": run_timing,
        "runs": runs,
        "anchor_files": anchor_files,
    }


# --------------------------------------------------------------------------- #
# records
# --------------------------------------------------------------------------- #
def _evidence_dict(cand, evidence, predicate_result, counting="b1"):
    (uid, code_name, code_first, lasti, verdict, observed,
     member_note, projection) = evidence
    out = {
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
        "pattern_class": cand.pattern_class,
        "predicate_scope": cand.predicate_scope,
        "guard_observed": member_note,
    }
    if cand.projection_src is not None:
        out["member_projection"] = {
            "predicate": cand.projection_src,
            "result": projection,
            "note": ("diagnostic only: this projection never decides predicate truth; under "
                     "b1 counting the rule-level symbol_observed it feeds additionally gates "
                     "proved (checker 1.2.0, adjudication 2)" if counting == "b1" else
                     "diagnostic only: the rule's status never depends on this "
                     "projection (checker 1.1.0, defect D1)"),
        }
    return out


def _occurrence_id(entry_id, ev):
    return "%s|%s:%d|%s|%s@%d" % (entry_id, ev["file"], ev["line"], ev["ast_path"],
                                  ev["code_object"], ev["bytecode_offset"])


def build_records(universe, ctx, structural_negative=False, counting="b1"):
    rules = universe.get("rules") or []
    meas = ctx["meas"]
    candidates = ctx["candidates"]
    entries_by_pyc = ctx["entries_by_pyc"]
    entry_by_id = ctx["entry_by_id"]
    universe_files_sha = ctx["universe_files_sha"]
    trace_hits = ctx["trace_hits"]
    candidates_by_rule = ctx.get("candidates_by_rule") or {}

    records = []
    for rule in rules:
        rid = rule["rule_id"]
        kind = rule.get("kind")
        symbol = rule.get("symbol")
        reasons = []
        notes = []

        # ---- how the predicate was rebuilt (D2 accounting) --------------- #
        rule_cands = candidates_by_rule.get(rid) or []
        classes = sorted({c.pattern_class for c in rule_cands})
        if not rule_cands:
            pattern_class = "not_located"
        elif len(classes) == 1:
            pattern_class = classes[0]
        else:
            pattern_class = "mixed:" + ",".join(classes)
        scopes = sorted({c.predicate_scope for c in rule_cands})
        predicate_scope = scopes[0] if len(scopes) == 1 else ("mixed:" + ",".join(scopes)
                                                              if scopes else "not_located")
        guard_members = None
        guard_name = None
        guard_kind = None
        projection_src = None
        for cand in rule_cands:
            if cand.members and guard_members is None:
                guard_members = list(cand.members)
            if cand.guard == GUARD_IN_NAME and guard_name is None:
                guard_name = cand.symbol
            if cand.guard != GUARD_EQ and guard_kind is None:
                guard_kind = cand.guard
            if cand.projection_src and projection_src is None:
                projection_src = cand.projection_src
        guard_info = None
        if guard_kind is not None:
            guard_info = {
                "kind": guard_kind,
                "members": guard_members,
                "name": guard_name,
                "member_count": len(guard_members) if guard_members else None,
                "note": ("one scope for the whole guard (checker 1.1.0): the rule predicate is "
                         "the guard as written, not the single member"),
            }

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

        # ---- D1 diagnostic: did the rule's own symbol ever match? --------- #
        # Measured per candidate, never decisive.  A guard-scope rule can be true
        # while its own symbol was never the member that matched; that is the
        # difference between "the guard line reached a handled branch" and
        # "this opcode/IR value was handled".
        projection_true = meas.projection_true.get(rid, 0)
        projection_runs = sum(1 for pyc in meas.pyc_projection_true
                              if rid in meas.pyc_projection_true[pyc])
        member_match = any(meas.cand_true.get(c.uid, 0)
                           for c in rule_cands if c.predicate_scope == "member")
        member_projection_match = any(meas.cand_projection_true.get(c.uid, 0)
                                      for c in rule_cands if c.projection_compiled is not None)
        named_set_match = any(meas.cand_true.get(c.uid, 0)
                              for c in rule_cands if c.guard == GUARD_IN_NAME
                              and c.members is None and c.projection_compiled is None)
        symbol_observed = bool(member_match or member_projection_match or named_set_match)
        member_projection = None
        if projection_src is not None:
            member_projection = {
                "predicate": projection_src,
                "evaluations_at_true_guard": meas.projection_evaluations.get(rid, 0),
                "true": projection_true,
                "false_at_true_guard": meas.guard_true_projection_false.get(rid, 0),
                "pyc_runs_with_true": projection_runs,
                "symbol_observed": symbol_observed,
                "note": ("diagnostic only (checker 1.2.0): measured when the guard was true; the "
                         "projection never decides predicate truth, but under b1 counting the "
                         "rule-level symbol_observed it feeds gates proved (adjudication 2)"
                         if counting == "b1" else
                         "diagnostic only (checker 1.1.0): measured when the guard was true, "
                         "never used to decide a status"),
            }

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
                pos_ev = _evidence_dict(cand, evidence, "true", counting=counting)
                owners = sorted(e["id"] for e in entries_by_pyc.get(raise_pyc, []))
                positive = owners[0]
                occurrence_id = _occurrence_id(positive, pos_ev)
                hash_input = "|".join([
                    rid, str(rule.get("anchor", "")), occurrence_id, str(pattern_class),
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
                    "predicate_class": pattern_class,
                    "predicate_scope": predicate_scope,
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
                    neg_ev = _evidence_dict(n_cand, n_evidence, "false", counting=counting)
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
                        weak_ev = _evidence_dict(w_cand, w_evidence, "false", counting=counting)
                        weak_ev["selection"] = weak_pick
                        weak_ev["weak"] = True
                        notes.append("weak_negative_available")

        # ---- structural negative witness (opt-in, S-neg) ------------------ #
        # G4_PROOF_THEORY 4.1(3) additionally demands that the whole run be
        # false-only.  An anchor inside a loop / a repeatedly executed branch can
        # never satisfy that even when it *does* evaluate false in another pyc, so
        # with --structural-negative a real counterexample occurrence is accepted:
        #   (a) e- is a different J pyc than e+            [kills same-run entries]
        #   (b) e- reached the *same* declared anchor (file, line, ast_path)
        #   (c) the predicate measured FALSE there       [a real refutation]
        # It is recorded as witness_evidence.negative_selection =
        # "same_anchor_diff_pyc" plus structural_negative=true, never as a 4.1
        # strict witness, and only when no strict witness exists.
        structural = None
        if (negative is None and structural_negative and weak_ev is not None
                and pos_ev is not None):
            same_anchor = (weak_ev.get("file") == pos_ev.get("file")
                           and weak_ev.get("line") == pos_ev.get("line")
                           and weak_ev.get("ast_path") == pos_ev.get("ast_path"))
            if same_anchor:
                structural = dict(weak_ev)
                structural["selection"] = "same_anchor_diff_pyc"
                structural["structural_negative"] = True
                structural["note"] = ("structural counterexample: same declared anchor, "
                                      "different J pyc, measured false there")
                structural.pop("weak", None)
                negative = weak_negative
                neg_pick = "same_anchor_diff_pyc"
                neg_ev = structural
                notes.append("structural_negative_same_anchor_diff_pyc")

        # ---- ruling 4: explicit structural-negative exemption -------------- #
        # Registered per rule in STRUCTURAL_NEGATIVE_EXEMPTIONS above.  Applies
        # only when the strict negative is missing, the positive occurrence is
        # measured, and the measured evidence matches the registration.  Like
        # the structural-negative fallback this is adjudication-only and
        # zero-perturbation: measurements are unchanged and no negative
        # witness is minted; only the verdict classification changes.
        structural_negative_exemption = None
        if (negative is None and structural_negative and proof is not None
                and rid in STRUCTURAL_NEGATIVE_EXEMPTIONS):
            ex = STRUCTURAL_NEGATIVE_EXEMPTIONS[rid]
            owners_of_true = set()
            for t_pyc, t_set in meas.pyc_true.items():
                if rid in t_set:
                    owners_of_true.update(
                        e["id"] for e in entries_by_pyc.get(t_pyc, []) if e.get("id"))
            pos_bound = ex["positive_witness_entry"] in owners_of_true
            true_bound = meas.evaluations_true.get(rid, 0) >= ex["min_true_evaluations"]
            anchor_bound = str(rule.get("anchor") or "") == ex["anchor"]
            if pos_bound and true_bound and anchor_bound:
                structural_negative_exemption = {
                    "registered": dict(ex),
                    "verified": {
                        "positive_witness_is_measured_owner": pos_bound,
                        "true_evaluations_measured": meas.evaluations_true.get(rid, 0),
                        "anchor_matches_registration": anchor_bound,
                        "strict_negative_witness": None,
                    },
                    "note": ("ruling 4 (ROW4 stage 3): the registered dominating guard "
                             "enumerates every member and puts this predicate at the chain "
                             "tail, so any evaluation that reaches it is true and a strict "
                             "negative occurrence is structurally impossible; the measured "
                             "positive witness satisfies the registered evidence binding. "
                             "Measurements are unchanged, only the verdict is classified."),
                }
                notes.append("structural_negative_exemption_applied")
            else:
                notes.append("structural_negative_exemption_registered_not_applied")

        # ---- status ------------------------------------------------------ #
        # "guard_only": the rule's predicate is the whole guard, it was measured
        # true, but the rule's own symbol was never the member that matched.
        # This is the label a reviewer needs for the dead-name families (the
        # exclusion candidates in fresh/gate_g4/g4_exclude_candidates.json).
        guard_only = (projection_src is not None and not symbol_observed
                      and meas.evaluations_true.get(rid, 0) > 0)
        if guard_only:
            notes.append("guard_true_without_symbol_observed")
        if (proof is not None
                and (negative is not None
                     or structural_negative_exemption is not None)
                and domain_hosts and domain_depths):
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

        # ---- counting policy (adjudication 2, G4_REVIEW_PACKET) ------------ #
        # b1 (default since 1.2.0): "proved" additionally requires that the
        # rule's own symbol was observed.  A rule that b2 proves only through
        # its whole guard being true (guard_only=True, symbol_observed=False)
        # is downgraded to open with reason guard_only_symbol_not_observed;
        # the would-be status stays on the record as a diagnostic
        # (b1_downgrade.b2_status).  b2 keeps the 1.1.0 counting bit for bit,
        # so no record ever carries b1_downgrade under b2.
        b1_downgrade = None
        if counting == "b1" and status == "proved" and not symbol_observed:
            b1_downgrade = {
                "counting": "b1",
                "b2_status": "proved",
                "reason": R_GUARD_ONLY,
                "note": ("G4_REVIEW_PACKET adjudication 2 (B1, recommended): proved requires "
                         "symbol_observed=True; this rule was proved only by its guard being "
                         "true while its own symbol was never observed, so the occurrence is "
                         "diagnostic evidence, not a proof"),
            }
            status = "open"
            reasons.append(R_GUARD_ONLY)
            notes.append("b1_downgraded_from_b2_proved")

        witnesses = {"positive": [positive] if positive else [],
                     "negative": [negative] if negative else []}
        reason_texts = [{"code": code, "text": REASON_TEXT.get(code, code)} for code in reasons]

        record = {
            "rule_id": rid,
            "status": status,
            "pattern_kind": kind,
            "pattern_class": pattern_class,
            "universe_kind": kind,
            "predicate_scope": predicate_scope,
            "guard": guard_info,
            "member_projection": member_projection,
            "symbol_observed": symbol_observed,
            "guard_only": bool(guard_only),
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
        }
        if b1_downgrade is not None:
            record["b1_downgrade"] = b1_downgrade
        if structural_negative_exemption is not None:
            record["structural_negative_exemption"] = structural_negative_exemption
        records.append(record)
    return records


def summarise(records, universe, ctx, counting="b1"):
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
        elif R_GUARD_ONLY in codes:
            primary = R_GUARD_ONLY
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

    summary = {
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
        # ---- D2 accounting: the class actually rebuilt for each rule ------ #
        "pattern_class_counts": dict(sorted(collections.Counter(
            r["pattern_class"] for r in records).items())),
        "proved_by_pattern_class": dict(sorted(collections.Counter(
            r["pattern_class"] for r in records if r["status"] == "proved").items())),
        "open_by_pattern_class": dict(sorted(collections.Counter(
            r["pattern_class"] for r in records if r["status"] == "open").items())),
        "predicate_scope_counts": dict(sorted(collections.Counter(
            r["predicate_scope"] for r in records).items())),
        # ---- D1 accounting: guard-scope truth vs. the member it names ----- #
        "proved_guard_scope": sum(1 for r in records if r["status"] == "proved"
                                  and r["predicate_scope"] == "guard"),
        "proved_guard_true_without_symbol_observed": sum(
            1 for r in records if r["status"] == "proved" and r["guard_only"]),
        "open_guard_true_without_symbol_observed": sum(
            1 for r in records if r["status"] == "open" and r["guard_only"]),
        "rules_with_symbol_observed": sum(1 for r in records if r["symbol_observed"]),
        "rules_guard_true_symbol_never_observed": sum(
            1 for r in records if r["guard_only"]),
        "proved_with_some_stale_anchor": sum(
            1 for r in records if r["status"] == "proved"
            and r["measurement"]["anchors_located"] < r["measurement"]["anchors_declared"]),
        "trace_runtime": {
            "traced_rules_never_measured_true": trace_only,
            "measured_true_rules_not_in_traces": measured_only,
            "runs_with_measured_true_outside_traces": runs_with_measured_only,
        },
    }
    if counting == "b1":
        summary["b1_downgraded_from_b2_proved"] = sum(
            1 for r in records if r.get("b1_downgrade") is not None)
    # ---- ruling 4 (ROW4 stage 3): exempted proved counted separately ------ #
    summary["proved_structural_negative_exemption"] = sum(
        1 for r in records if r.get("structural_negative_exemption") is not None)
    summary["proved_strict"] = sum(
        1 for r in records if r["status"] == "proved"
        and r.get("structural_negative_exemption") is None)
    summary["structural_negative_exemptions"] = [
        r["rule_id"] for r in records if r.get("structural_negative_exemption") is not None]
    return summary


def patch_manifest(manifest, records, counting="b1"):
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
        item["predicate_scope"] = rec["predicate_scope"]
        item["pattern_class"] = rec["pattern_class"]
        item["symbol_observed"] = rec["symbol_observed"]
        if rec["guard"] is not None:
            item["guard"] = rec["guard"]
        if rec["member_projection"] is not None:
            item["member_projection"] = {
                "predicate": rec["member_projection"]["predicate"],
                "true": rec["member_projection"]["true"],
                "false_at_true_guard": rec["member_projection"]["false_at_true_guard"],
                "symbol_observed": rec["member_projection"]["symbol_observed"],
                "note": rec["member_projection"]["note"],
            }
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
            if rec.get("structural_negative_exemption") is not None:
                _ex = rec["structural_negative_exemption"]
                item["structural_negative_exemption"] = {
                    "positive_witness_entry": _ex["registered"]["positive_witness_entry"],
                    "true_evaluations": _ex["verified"]["true_evaluations_measured"],
                    "ruling": "ROW4 stage 3 ruling 4 (structural negative exemption, "
                              "per-rule registration; strict negative structurally impossible)",
                }
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
                                        "why_not_proved": (
                                            "b1 conservative counting (adjudication 2): the "
                                            "rule's own symbol was never observed, so the "
                                            "guard-true occurrence is diagnostic evidence, "
                                            "not a proof"
                                            if rec.get("b1_downgrade") is not None else
                                            "no strict negative witness; this is "
                                            "evidence only, not a proof"),
                                    })}
        item["status"] = rec["status"]
        if rec.get("b1_downgrade") is not None:
            item["b1_downgrade"] = rec["b1_downgrade"]
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
    parser.add_argument(
        "--also-legacy", action="store_true",
        help=("also drive the v2 generator entry of the same package "
              "(core.cfg.generate_ast / decompile(use_region=False)) on every J pyc, "
              "so rules living on that shipped path are measured too (default off)"))
    parser.add_argument(
        "--structural-negative", action="store_true",
        help=("accept, only when no strict 4.1 witness exists, a real counterexample "
              "occurrence at the same declared anchor in a different J pyc "
              "(negative_selection=same_anchor_diff_pyc); recorded and labelled, "
              "never mixed with strict witnesses (default off)"))
    parser.add_argument(
        "--counting", choices=("b1", "b2"), default="b1",
        help=("how guard-only rules count toward 'proved' (G4_REVIEW_PACKET adjudication 2): "
              "b1 (default since 1.2.0) requires symbol_observed=True, so a rule proved only "
              "by its whole guard being true is downgraded to open with reason "
              "guard_only_symbol_not_observed (b1_downgrade keeps the would-be status); "
              "b2 keeps the 1.1.0 counting bit for bit (guard-only rules stay proved) so the "
              "old readings stay exactly reproducible"))
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
    ctx = run_measurement(universe, jspace, verbose=not args.quiet,
                          also_legacy=args.also_legacy)
    ctx["trace_hits"] = trace_hits
    ctx["trace_by_pyc"] = trace_by_pyc
    ctx["universe_files_sha"] = universe_files_sha
    ctx["input_meta"] = input_meta

    records = build_records(universe, ctx,
                            structural_negative=args.structural_negative,
                            counting=args.counting)
    counts = summarise(records, universe, ctx, counting=args.counting)
    candidate_manifest = patch_manifest(manifest, records, counting=args.counting)

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
            "predicate_scope": ("'guard' when the rule's pattern is a membership guard (the "
                                "predicate is the whole guard, one scope per construct since "
                                "1.1.0); 'member' when the pattern is a single equality"),
            "member_projection": (
                ("diagnostic only: the single-member projection of a guard, "
                 "measured at true-guard occurrences; it never decides predicate truth, and "
                 "under b1 counting the rule-level symbol_observed it feeds additionally "
                 "gates proved (adjudication 2)") if args.counting == "b1" else
                ("diagnostic only: the single-member projection of a guard, "
                 "measured at true-guard occurrences; it never decides status "
                 "and it tells whether the rule's own symbol was ever observed")),
        },
        "inputs": input_meta,
        "options": {
            "counting": args.counting,
            "also_legacy": bool(args.also_legacy),
            "structural_negative": bool(args.structural_negative),
            "structural_negative_exemptions_registered": len(STRUCTURAL_NEGATIVE_EXEMPTIONS),
            "pipelines": ctx.get("pipelines") or ["region"],
            "note": (("counting defaults to b1 (G4_REVIEW_PACKET adjudication 2, conservative: "
                      "proved requires symbol_observed=True; --counting b2 reproduces the 1.1.0 "
                      "readings exactly); both measurement options default to off; with them off "
                      "the measurement is the v1 domain (region pipeline only, strict 4.1 "
                      "negative witness only)") if args.counting == "b1" else
                     ("both options default to off; with them off the measurement is the "
                      "v1 domain (region pipeline only, strict 4.1 negative witness only)")),
        },
        "runs": {
            "distinct_pyc_runs": ctx["runs"],
            "distinct_j_entries": len(ctx["entry_by_id"]),
            "run_failures": ctx["run_failures"],
            "partial_run_failures": ctx.get("partial_failures") or {},
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
    if counts.get("proved_structural_negative_exemption"):
        print("[rule_proof_check] structural_negative_exemptions: proved=%d "
              "strict=%d exempted=%d (%s)"
              % (counts["proved"], counts["proved_strict"],
                 counts["proved_structural_negative_exemption"],
                 ", ".join(counts.get("structural_negative_exemptions") or [])))
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
    print("[rule_proof_check] pattern_class=%s"
          % json.dumps(counts["pattern_class_counts"], ensure_ascii=False, sort_keys=True))
    print("[rule_proof_check] proved_by_pattern_class=%s"
          % json.dumps(counts["proved_by_pattern_class"], ensure_ascii=False, sort_keys=True))
    print("[rule_proof_check] scope=%s guard_only_proved=%d guard_only_open=%d "
          "symbol_observed=%d proved_without_symbol_observed=%d"
          % (json.dumps(counts["predicate_scope_counts"], ensure_ascii=False, sort_keys=True),
             counts["proved_guard_true_without_symbol_observed"],
             counts["open_guard_true_without_symbol_observed"],
             counts["rules_with_symbol_observed"],
             counts["proved_guard_true_without_symbol_observed"]))
    if args.counting == "b1":
        print("[rule_proof_check] counting=b1 downgraded_from_b2_proved=%d"
              % counts.get("b1_downgraded_from_b2_proved", 0))
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
