"""L5 evidence-layer audit: shared form / scale feature extraction.

Two *measurement planes* are kept strictly separated, because their availability
differs and that asymmetry is itself an evidence-layer finding:

* **bytecode plane** -- works on any CPython-3.11 ``.pyc``.
  Applicable to the 402 certified corpus artifacts (the input the product
  actually faced) and to every probe that only survives as ``.pyc``.
  This is the plane the *judge* observes, so it is the fair comparison basis.
  Forms that bytecode cannot decide are listed in ``PLANE_LIMITS`` and are
  measured on the source plane instead.

* **source plane** -- works on ``.py`` via :mod:`ast`.
  Applicable to probe *sources* (authoritative: the probe author writes them).
  For the corpus it is applicable only to the **product output** (``*OK.py``),
  because 397/402 original sources were deleted.  Product output is a *lower
  bound* proxy for the original source (the product can drop forms - see
  ATTACK_L4_RUNTIME B202/B203/B208 - but does not invent them), and it is
  flagged as such wherever it is used.

The detectors are validated by ``l5_selftest.py`` against synthetic samples
with known ground truth; the self-test result is part of the evidence.

Read-only: this module never writes anything by itself.
"""

from __future__ import annotations

import ast
import dis
import importlib.util
import marshal
from typing import Any, Dict, Iterable, List, Optional, Tuple

PY311_MAGIC = importlib.util.MAGIC_NUMBER

CO_VARARGS = 0x04
CO_VARKEYWORDS = 0x08
CO_GENERATOR = 0x20
CO_COROUTINE = 0x80
CO_NESTED = 0x10

MAKE_FUNCTION_ANNOTATIONS = 0x04

# --- form vocabulary -------------------------------------------------------
FORMS: Tuple[str, ...] = (
    "annotation",
    "fstring",
    "dataclass",
    "async_def",
    "except_star",
    "pep604_union",
    "closure",
    "decorator",
    "decorator_chain",
    "generator",
    "lambda",
    "match_stmt",
    "comprehension",
    "try_except",
    "try_finally",
    "with_stmt",
    "global_stmt",
    "nonlocal_stmt",
    "class_def",
    "nested_def",
    "assert_stmt",
    "del_stmt",
    "slice_step",
    "star_call",
    "walrus",
    "async_for",
    "yield_from",
    "boolop_chain",
    "chain_compare",
    "ifexp",
    "deep_nest_d3",
    "deep_nest_d5",
)

# forms decidable on the bytecode plane (see PLANE_LIMITS for the caveats)
BYTECODE_DECIDABLE = (
    "fstring", "dataclass", "async_def", "except_star", "closure", "decorator",
    "decorator_chain", "generator", "lambda", "match_stmt", "comprehension",
    "try_except", "try_finally", "with_stmt", "global_stmt",
    "class_def", "nested_def", "assert_stmt", "slice_step", "star_call",
    "walrus", "async_for", "yield_from", "boolop_chain",
)

# documented limits of the bytecode plane (form -> why it is not decidable)
PLANE_LIMITS = {
    "match_stmt": "literal-only `case` patterns compile to COMPARE_OP/POP_JUMP "
                  "without any MATCH_* opcode -> bytecode sees only structural "
                  "patterns (sequence/mapping/class); literal cases invisible",
    "ifexp": "ternary and if-statement share the same bytecode shape -> not decidable",
    "chain_compare": "chained comparison shares JUMP_IF_FALSE_OR_POP with BoolOp -> "
                     "only separable heuristically (previous opcode != COMPARE_OP)",
    "pep604_union": "PEP 604 `X | Y` is a plain NB_OR on type objects -> not decidable",
    "annotation": "MAKE_FUNCTION flag 0x04 / SETUP_ANNOTATIONS only cover "
                  "function+class+module annotations; local variable annotations "
                  "are not evaluated at runtime -> invisible",
    "del_stmt": "DELETE_* opcodes also emitted by the compiler for except* handler "
                "variable cleanup -> bytecode over-counts user `del`",
    "walrus": "the walrus compiles to `COPY 1` + STORE, which is also used to "
              "copy a closure cell -> the bytecode detector excludes the "
              "LOAD_CLOSURE+COPY shape, but a `COPY 1` before a STORE inside a "
              "match subject is still ambiguous",
    "boolop_chain": "bytecode sees only value-position short-circuits "
                     "(JUMP_IF_*_OR_POP); a BoolOp in test position compiles to "
                     "POP_JUMP_IF_FALSE and is indistinguishable from a plain "
                     "if -> bytecode under-counts (use the source plane)",
    "nonlocal_stmt": "`nonlocal x` compiles exactly like a closure capture "
                     "(cell var) -> bytecode-invisible; source plane only",
}

SOURCE_PREFERRED = ("pep604_union", "chain_compare", "ifexp", "try_finally",
                    "del_stmt", "match_stmt", "nonlocal_stmt", "annotation")


# --- bytecode helpers ------------------------------------------------------


def load_pyc_code(path: str) -> Optional[Any]:
    """Return the top-level code object of a 3.11 ``.pyc`` (or ``None``)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(16)
            if len(head) < 16 or head[:4] != PY311_MAGIC:
                return None
            return marshal.load(fh)
    except Exception:
        return None


def iter_code(code: Any) -> Iterable[Any]:
    """Yield every code object reachable from ``code`` (self + nested)."""
    stack = [code]
    seen = 0
    while stack:
        cur = stack.pop()
        seen += 1
        yield cur
        for const in getattr(cur, "co_consts", ()):
            if hasattr(const, "co_code"):
                stack.append(const)
        if seen > 200000:
            return


def _ops(code: Any) -> List[Any]:
    return list(dis.get_instructions(code))


def _has_opcode(code: Any, names: Iterable[str]) -> bool:
    opc = dis.opmap
    want = {opc[n] for n in names if n in opc}
    if not want:
        return False
    return any(ins.opcode in want for ins in _ops(code))


def _parse_exception_table(tbl: bytes) -> List[Tuple[int, int, int, int]]:
    """CPython 3.11 exception-table walker -> (start, end, target, depth).

    Format (3.11, ``Objects/exception_table.c``): four varints per entry --
    start, length, target, depth -- where a varint is a sequence of 6-bit
    groups, **most significant group first**, the continuation flag being
    ``0x40``.  The depth varint packs ``depth << 1 | lasti``.

    This is byte-for-byte the same decoding the *judge* uses: the attached
    ``pylingual`` ruler parses exception tables with
    ``xdis.bytecode.parse_exception_table``.  ``l5_selftest.py`` cross-checks
    this implementation against ``xdis`` on every sample.
    """
    it = iter(tbl)
    out: List[Tuple[int, int, int, int]] = []

    def varint() -> int:
        b = next(it)
        val = b & 63
        while b & 64:
            val <<= 6
            b = next(it)
            val |= b & 63
        return val

    while True:
        try:
            start = varint() * 2
            length = varint() * 2
            end = start + length
            target = varint() * 2
            dl = varint()
        except StopIteration:
            break
        depth = dl >> 1
        out.append((start, end, target, depth))
    return out


def _exc_entries(code: Any) -> List[Tuple[int, int, int, int]]:
    tbl = getattr(code, "co_exceptiontable", b"")
    return _parse_exception_table(tbl) if tbl else []


def _exc_table_depth(code: Any) -> int:
    entries = _exc_entries(code)
    if not entries:
        return 0
    offs = sorted({e[0] for e in entries} | {e[1] for e in entries})
    best = 0
    for off in offs:
        best = max(best, sum(1 for e in entries if e[0] <= off < e[1]))
    return best


def _classify_handlers(code: Any) -> Dict[str, int]:
    """Classify the exception handling of one code object.

    CPython 3.11 encodes three different things in the exception table: a real
    ``except`` handler, a ``finally`` copy, and the implicit cleanup of ``with``
    / ``async for``.  The classification rules (all validated by
    ``l5_selftest.py``):

    * typed / starred except -> ``CHECK_EXC_MATCH`` / ``CHECK_EG_MATCH``
      (emitted **only** by except handlers)
    * bare ``except:``         -> ``PUSH_EXC_INFO`` immediately followed by
      ``POP_TOP`` (the exception object is popped, not matched)
    * cleanup                  -> handler region contains ``WITH_EXCEPT_START``
      or ``END_ASYNC_FOR``
    * finally copy             -> handler region contains ``RERAISE`` with no
      ``POP_EXCEPT`` before it, no cleanup / match marker, no ``DELETE_FAST`` /
      ``DELETE_NAME`` (that is the compiler's exception-variable epilogue) and
      at least one body opcode (``CALL`` / ``LOAD_GLOBAL`` / ...) so that the
      epilogue is not mistaken for a finally body
    """
    entries = _exc_entries(code)
    out = {"protected": 0, "except": 0, "finally": 0, "cleanup": 0}
    if not entries:
        return out
    out["protected"] = 1
    insns = _ops(code)
    names = [i.opname for i in insns]
    nset = set(names)
    if "CHECK_EXC_MATCH" in nset or "CHECK_EG_MATCH" in nset:
        out["except"] = 1
    for i, ins in enumerate(insns):
        if ins.opname != "PUSH_EXC_INFO":
            continue
        j = i + 1
        while j < len(insns) and insns[j].opname in ("NOP", "CACHE"):
            j += 1
        if j < len(insns) and insns[j].opname == "POP_TOP":
            out["except"] = 1
    targets = sorted({e[2] for e in entries})
    for i, t in enumerate(targets):
        end = targets[i + 1] if i + 1 < len(targets) else None
        region = [ins.opname for ins in insns
                  if ins.offset >= t and (end is None or ins.offset < end)]
        rset = set(region)
        if "WITH_EXCEPT_START" in rset or "END_ASYNC_FOR" in rset:
            out["cleanup"] += 1
            continue
        if "RERAISE" in region:
            first_raise = region.index("RERAISE")
            body_ops = {"CALL", "LOAD_GLOBAL", "LOAD_ATTR", "LOAD_METHOD",
                        "STORE_ATTR", "STORE_SUBSCR", "IMPORT_NAME",
                        "BINARY_SUBSCR", "POP_TOP"}
            if ("POP_EXCEPT" not in region[:first_raise]
                    and "CHECK_EXC_MATCH" not in rset
                    and "CHECK_EG_MATCH" not in rset
                    and "DELETE_FAST" not in rset
                    and "DELETE_NAME" not in rset
                    and (body_ops & rset)):
                out["finally"] += 1
    return out


def _count_blocks(code: Any) -> int:
    """Approximate basic-block count (jump targets + post-terminator)."""
    insns = _ops(code)
    leaders = set()
    for ins in insns:
        if ins.opcode in dis.hasjabs or ins.opcode in dis.hasjrel:
            if isinstance(ins.argval, int):
                leaders.add(ins.argval)
    for i, ins in enumerate(insns):
        if ins.opname in ("RETURN_VALUE", "RAISE_VARARGS", "RERAISE"):
            if i + 1 < len(insns):
                leaders.add(insns[i + 1].offset)
    return len(leaders) + 1


def _decorated_pairs(code: Any) -> Tuple[int, int]:
    """(decorated_defs, decorator_chain_defs) heuristic on bytecode.

    ``MAKE_FUNCTION`` followed (ignoring NOP/CACHE/RESUME/PRECALL and the
    class-name LOAD_CONST) by one or more ``CALL`` instructions means the
    freshly built function/class is decorated.  A class body is built through
    ``LOAD_BUILD_CLASS`` and its trailing ``__build_class__`` call must not be
    counted as a decorator, so for class bodies one CALL is subtracted.
    """
    insns = _ops(code)
    skip = ("NOP", "CACHE", "RESUME", "PRECALL", "LOAD_CONST", "PUSH_NULL")
    dec = 0
    chain = 0
    for i, ins in enumerate(insns):
        if ins.opname != "MAKE_FUNCTION":
            continue
        is_class = any(insns[j].opname == "LOAD_BUILD_CLASS"
                       for j in range(max(0, i - 4), i))
        calls = 0
        j = i + 1
        while j < len(insns) and insns[j].opname in skip:
            j += 1
        while j < len(insns) and insns[j].opname == "CALL":
            calls += 1
            j += 1
            while j < len(insns) and insns[j].opname in skip:
                j += 1
        if is_class:
            calls = max(0, calls - 1)
        if calls >= 1:
            dec += 1
            if calls >= 2:
                chain += 1
    return dec, chain


def _boolop_count(code: Any) -> int:
    """Short-circuit BoolOp count, excluding chained-comparison look-alikes."""
    insns = _ops(code)
    n = 0
    for i, ins in enumerate(insns):
        if ins.opname not in ("JUMP_IF_FALSE_OR_POP", "JUMP_IF_TRUE_OR_POP"):
            continue
        prev = insns[i - 1].opname if i > 0 else ""
        if prev == "COMPARE_OP":
            continue
        n += 1
    return n


def _walrus_count(code: Any) -> int:
    """Named-expression count: ``COPY 1`` immediately followed by a STORE.

    ``COPY 1`` is also used to copy a closure cell (``LOAD_CLOSURE; COPY 1;
    STORE_NAME``) -> that shape is excluded.
    """
    insns = _ops(code)
    n = 0
    for i, ins in enumerate(insns):
        if ins.opname == "COPY" and ins.argval == 1:
            nxt = insns[i + 1].opname if i + 1 < len(insns) else ""
            prev = insns[i - 1].opname if i > 0 else ""
            if nxt.startswith("STORE_") and prev != "LOAD_CLOSURE":
                n += 1
    return n


def _nonlocal_count(code: Any) -> int:
    """``nonlocal`` is bytecode-invisible (same shape as a closure capture).

    Kept as an explicit zero so the two planes cannot silently disagree; the
    source plane is the only one that can decide it.
    """
    return 0


def bytecode_features(code: Any) -> Dict[str, Any]:
    """Bytecode-plane feature vector + scale proxies for one module."""
    feats: Dict[str, int] = {f: 0 for f in FORMS}
    max_instr = 0
    max_blocks = 0
    max_exc_depth = 0
    max_exc_entries = 0
    n_code = 0
    n_func = 0
    dec_total = 0
    chain_total = 0
    max_instr_func = 0

    for co in iter_code(code):
        n_code += 1
        insns = _ops(co)
        max_instr = max(max_instr, len(insns))
        max_blocks = max(max_blocks, _count_blocks(co))
        max_exc_depth = max(max_exc_depth, _exc_table_depth(co))
        max_exc_entries = max(max_exc_entries, len(_exc_entries(co)))

        flags = getattr(co, "co_flags", 0)
        names = set(getattr(co, "co_names", ()))
        cname = getattr(co, "co_name", "")
        qual = getattr(co, "co_qualname", "") or cname

        if flags & CO_GENERATOR:
            feats["generator"] += 1
        if flags & CO_COROUTINE:
            feats["async_def"] += 1
        if (getattr(co, "co_freevars", ())
                and not cname.startswith("<")):
            # a genuine closure capture by a *function* scope; comprehension
            # code objects and the implicit `__class__` cell are excluded so
            # that the bytecode plane stays comparable with the source plane
            feats["closure"] += 1
        if cname == "<lambda>":
            feats["lambda"] += 1
        if cname in ("<listcomp>", "<setcomp>", "<dictcomp>", "<genexpr>"):
            feats["comprehension"] += 1
        if cname not in ("<module>", "<lambda>") and not cname.startswith("<"):
            n_func += 1
            max_instr_func = max(max_instr_func, len(insns))
        if flags & CO_VARARGS or flags & CO_VARKEYWORDS:
            feats["star_call"] += 1
        if (flags & CO_NESTED) and "." in qual and not cname.startswith("<"):
            # real nested function (comprehension code objects carry CO_NESTED
            # too, but their co_name is <listcomp>/<dictcomp>/<genexpr>)
            feats["nested_def"] += 1

        if _has_opcode(co, ("FORMAT_VALUE",)):
            feats["fstring"] += 1
        if "dataclass" in names or "__dataclass_fields__" in names:
            feats["dataclass"] += 1
        if _has_opcode(co, ("CHECK_EG_MATCH",)):
            feats["except_star"] += 1
        if _has_opcode(co, ("GET_AITER",)):
            feats["async_for"] += 1
        if _has_opcode(co, ("BEFORE_WITH",)):
            feats["with_stmt"] += 1
        if _has_opcode(co, ("LOAD_ASSERTION_ERROR",)):
            feats["assert_stmt"] += 1
        if _has_opcode(co, ("DELETE_FAST", "DELETE_NAME", "DELETE_GLOBAL", "DELETE_DEREF")):
            feats["del_stmt"] += 1
        if _has_opcode(co, ("LOAD_BUILD_CLASS",)):
            feats["class_def"] += 1
        if _has_opcode(co, ("MATCH_CLASS", "MATCH_SEQUENCE", "MATCH_MAPPING", "MATCH_KEYS",
                            "MATCH_KV", "MATCH_AS", "MATCH_OR", "MATCH_LAST")):
            feats["match_stmt"] += 1
        if _has_opcode(co, ("CALL_FUNCTION_EX",)):
            feats["star_call"] += 1
        if _has_opcode(co, ("STORE_GLOBAL", "DELETE_GLOBAL")):
            feats["global_stmt"] += 1
        if _has_opcode(co, ("GET_YIELD_FROM_ITER",)):
            feats["yield_from"] += 1
        if _has_opcode(co, ("SETUP_ANNOTATIONS",)):
            feats["annotation"] += 1
        if "__annotations__" in names:
            feats["annotation"] += 1
        for ins in insns:
            if ins.opname == "MAKE_FUNCTION" and isinstance(ins.argval, int) \
                    and (ins.argval & MAKE_FUNCTION_ANNOTATIONS):
                feats["annotation"] += 1
                break
        for ins in insns:
            if ins.opname == "BUILD_SLICE" and isinstance(ins.argval, int) and ins.argval >= 3:
                feats["slice_step"] += 1
                break
        handlers = _classify_handlers(co)
        if handlers["except"]:
            feats["try_except"] += 1
        if handlers["finally"]:
            feats["try_finally"] += 1
        feats["boolop_chain"] += _boolop_count(co)
        feats["walrus"] += _walrus_count(co)

        dec, chain = _decorated_pairs(co)
        dec_total += dec
        chain_total += chain

    feats["decorator"] = dec_total
    feats["decorator_chain"] = chain_total
    feats["nonlocal_stmt"] = _nonlocal_count(code)
    return {
        "features": feats,
        "n_code_objects": n_code,
        "n_functions": n_func,
        "max_code_instr": max_instr,
        "max_func_instr": max_instr_func,
        "max_code_blocks": max_blocks,
        "max_exc_table_depth": max_exc_depth,
        "max_exc_entries": max_exc_entries,
    }


# --- source plane ----------------------------------------------------------


class _AstScan(ast.NodeVisitor):
    def __init__(self) -> None:
        self.features: Dict[str, int] = {f: 0 for f in FORMS}
        self.max_func_stmts = 0
        self.max_nest_depth = 0
        self.max_expr_width = 0
        self.n_funcs = 0
        self.n_classes = 0
        self.total_stmts = 0
        self.n_lines = 0
        self._in_function = False
        self._bound_stack: List[set] = []
        self._funcs: List[ast.AST] = []

    # helpers
    def _bump(self, name: str, n: int = 1) -> None:
        self.features[name] = self.features.get(name, 0) + n

    @staticmethod
    def _stmt_count(body: List[ast.stmt]) -> int:
        n = 0
        for s in body:
            n += 1
            for field in ("body", "orelse", "finalbody", "handlers"):
                sub = getattr(s, field, None)
                if isinstance(sub, list):
                    n += _AstScan._stmt_count(sub)
        return n

    @staticmethod
    def _stmt_depth(node: ast.stmt, d: int = 1) -> int:
        best = d
        for field in ("body", "orelse", "finalbody"):
            sub = getattr(node, field, None)
            if isinstance(sub, list):
                for s in sub:
                    best = max(best, _AstScan._stmt_depth(s, d + 1))
        for h in getattr(node, "handlers", []) or []:
            best = max(best, _AstScan._stmt_depth(h, d + 1))
        return best

    @staticmethod
    def _bound_names(body: List[ast.stmt]) -> set:
        out = set()
        for node in ast.walk(ast.Module(body=list(body), type_ignores=[])):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                out.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(node.name)
            elif isinstance(node, ast.arg):
                out.add(node.arg)
        return out

    @staticmethod
    def _loaded_names(body: List[ast.stmt]) -> set:
        out = set()
        for node in ast.walk(ast.Module(body=list(body), type_ignores=[])):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                out.add(node.id)
        return out

    # visitors
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node, is_async=True)

    def _function(self, node, is_async: bool) -> None:
        self.n_funcs += 1
        if is_async:
            self._bump("async_def")
        if node.decorator_list:
            self._bump("decorator")
            if len(node.decorator_list) >= 2:
                self._bump("decorator_chain")
        if node.returns is not None:
            self._bump("annotation")
        allargs = (list(node.args.posonlyargs) + list(node.args.args)
                   + list(node.args.kwonlyargs))
        if node.args.vararg is not None:
            allargs.append(node.args.vararg)
        if node.args.kwarg is not None:
            allargs.append(node.args.kwarg)
        for a in allargs:
            if a.annotation is not None:
                self._bump("annotation")
        if self._in_function:
            self._bump("nested_def")
        if any(isinstance(x, (ast.Yield, ast.YieldFrom)) for x in ast.walk(node)):
            self._bump("generator")
        # closure: nested function reading a name bound by an enclosing function
        if self._bound_stack:
            outer = set().union(*self._bound_stack)
            if self._loaded_names(node.body) & outer:
                self._bump("closure")
        self.max_func_stmts = max(self.max_func_stmts, self._stmt_count(node.body))
        d = max((self._stmt_depth(s) for s in node.body), default=0)
        self.max_nest_depth = max(self.max_nest_depth, d)
        if d >= 3:
            self._bump("deep_nest_d3")
        if d >= 5:
            self._bump("deep_nest_d5")
        # annotations are part of the function's own syntax -> visit them
        for dnode in node.decorator_list:
            self.visit(dnode)
        for a in allargs:
            if a.annotation is not None:
                self.visit(a.annotation)
        if node.returns is not None:
            self.visit(node.returns)
        self._bound_stack.append(self._bound_names(node.body))
        inner = self._in_function
        self._in_function = True
        for s in node.body:
            self.visit(s)
        self._in_function = inner
        self._bound_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.n_classes += 1
        self._bump("class_def")
        if node.decorator_list:
            self._bump("decorator")
            if len(node.decorator_list) >= 2:
                self._bump("decorator_chain")
        for b in node.bases:
            self.visit(b)
        for s in node.body:
            self.visit(s)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._bump("lambda")
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        self._bump("fstring")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._bump("annotation")
        self.generic_visit(node)

    def visit_Match(self, node) -> None:
        self._bump("match_stmt")
        self.generic_visit(node)

    def visit_Try(self, node) -> None:
        if node.handlers:
            self._bump("try_except")
        if node.finalbody:
            self._bump("try_finally")
        self.generic_visit(node)

    def visit_TryStar(self, node) -> None:
        self._bump("try_except")
        self._bump("except_star")
        self.generic_visit(node)

    def visit_With(self, node) -> None:
        self._bump("with_stmt")
        self.generic_visit(node)

    def visit_AsyncWith(self, node) -> None:
        self._bump("with_stmt")
        self._bump("async_for")
        self.generic_visit(node)

    def visit_AsyncFor(self, node) -> None:
        self._bump("async_for")
        self.generic_visit(node)

    def visit_Global(self, node) -> None:
        self._bump("global_stmt")
        self.generic_visit(node)

    def visit_Nonlocal(self, node) -> None:
        self._bump("nonlocal_stmt")
        self.generic_visit(node)

    def visit_Assert(self, node) -> None:
        self._bump("assert_stmt")
        self.generic_visit(node)

    def visit_Delete(self, node) -> None:
        self._bump("del_stmt")
        self.generic_visit(node)

    def visit_YieldFrom(self, node) -> None:
        self._bump("yield_from")
        self.generic_visit(node)

    def visit_NamedExpr(self, node) -> None:
        self._bump("walrus")
        self.generic_visit(node)

    def visit_BoolOp(self, node) -> None:
        self._bump("boolop_chain")
        if len(node.values) >= 3:
            self._bump("boolop_chain")
        self.generic_visit(node)

    def visit_Compare(self, node) -> None:
        if len(node.ops) >= 2:
            self._bump("chain_compare")
        self.generic_visit(node)

    def visit_IfExp(self, node) -> None:
        self._bump("ifexp")
        self.generic_visit(node)

    def visit_BinOp(self, node) -> None:
        if isinstance(node.op, ast.BitOr):
            self._bump("pep604_union")
        self.generic_visit(node)

    def visit_Subscript(self, node) -> None:
        sl = node.slice
        if isinstance(sl, ast.Slice) and sl.step is not None:
            self._bump("slice_step")
        self.generic_visit(node)

    def visit_Call(self, node) -> None:
        if any(isinstance(a, ast.Starred) for a in node.args):
            self._bump("star_call")
        for kw in node.keywords:
            if kw.arg is None:
                self._bump("star_call")
        self.generic_visit(node)

    def visit_ListComp(self, node) -> None:
        self._bump("comprehension")

    def visit_SetComp(self, node) -> None:
        self._bump("comprehension")

    def visit_DictComp(self, node) -> None:
        self._bump("comprehension")

    def visit_GeneratorExp(self, node) -> None:
        self._bump("comprehension")
        self._bump("generator")

    def generic_visit(self, node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            self.visit(child)


def source_features(src: str) -> Dict[str, Any]:
    """Source-plane feature vector + scale metrics for one ``.py`` text."""
    tree = ast.parse(src)
    sc = _AstScan()
    sc.visit(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for d in node.decorator_list:
                nm = getattr(d, "id", None) or getattr(d, "attr", None)
                if nm == "dataclass":
                    sc.features["dataclass"] += 1
        if isinstance(node, ast.Call):
            nm = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if nm == "dataclass":
                sc.features["dataclass"] += 1
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            sc.features["annotation"] += 1
    sc.total_stmts = sum(1 for n in ast.walk(tree) if isinstance(n, ast.stmt))
    for node in tree.body:
        sc.max_nest_depth = max(sc.max_nest_depth, sc._stmt_depth(node))
    for node in ast.walk(tree):
        if isinstance(node, ast.expr):
            sc.max_expr_width = max(sc.max_expr_width, sum(1 for _ in ast.walk(node)))
    return {
        "features": sc.features,
        "n_funcs": sc.n_funcs,
        "n_classes": sc.n_classes,
        "max_func_stmts": sc.max_func_stmts,
        "max_nest_depth": sc.max_nest_depth,
        "max_expr_width": sc.max_expr_width,
        "total_stmts": sc.total_stmts,
        "n_lines": src.count("\n") + 1,
    }


# --- aggregation -----------------------------------------------------------


def presence(feat_map: Dict[str, int]) -> Dict[str, int]:
    return {k: (1 if v > 0 else 0) for k, v in feat_map.items()}


def percentile(sorted_vals: List[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


def _dist(vals: List[float]) -> Dict[str, Any]:
    if not vals:
        return {"n": 0}
    s = sorted(float(v) for v in vals)
    return {
        "n": len(s),
        "min": s[0],
        "p50": percentile(s, 0.50),
        "p90": percentile(s, 0.90),
        "p99": percentile(s, 0.99),
        "max": s[-1],
        "mean": round(sum(s) / len(s), 2),
    }


def summarize(records: List[Dict[str, Any]], plane: str = "bytecode") -> Dict[str, Any]:
    """Aggregate per-file records into a distribution summary."""
    n = len(records)
    out: Dict[str, Any] = {"n": n, "plane": plane}
    pres = {f: 0 for f in FORMS}
    occ = {f: 0 for f in FORMS}
    for r in records:
        blob = r.get(plane) or {}
        feats = blob.get("features", {})
        for k, v in feats.items():
            if k not in pres:
                continue
            if v > 0:
                pres[k] += 1
            occ[k] += v
    out["presence"] = pres
    out["occurrence"] = occ
    out["presence_pct"] = {k: (round(100.0 * v / n, 2) if n else 0.0) for k, v in pres.items()}
    out["occurrence_per_file_mean"] = {k: (round(v / n, 3) if n else 0.0) for k, v in occ.items()}
    if plane == "bytecode":
        for metric in ("max_code_instr", "max_func_instr", "max_code_blocks",
                       "max_exc_table_depth", "max_exc_entries", "n_code_objects",
                       "n_functions"):
            out[metric] = _dist([r["bytecode"][metric] for r in records
                                  if r.get("bytecode")])
    else:
        for metric in ("max_func_stmts", "max_nest_depth", "max_expr_width",
                       "total_stmts", "n_lines", "n_funcs", "n_classes"):
            out[metric] = _dist([r["source"][metric] for r in records
                                  if r.get("source")])
    return out
