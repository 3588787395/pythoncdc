# -*- coding: utf-8 -*-
"""PATCH_R21-89_region_ast_generator.py -- [R21-88] `47d44ec51fa325c5` -> [R21-89] candidate.

Generator-only, built from the [R21-88] candidate bytes (base sha16 pinned below).  Two anchored
edits: (1) one call inserted at the end of `_r2188_and_prefix_or_tail`, (2) the new method
`_r2189_fold_window_guards`.  The pinned [R21-77-F5] analyzer `996a1b1acf143458` is unchanged.

Idempotent: re-reads the base bytes and reproduces the identical candidate sha16.  Absolute paths
only.  UTF-8 BOM + all-CRLF preserved; asserts zero CR-CR-LF, zero bare LF, py_compile clean.
"""
import hashlib
import py_compile

BASE = r'D:/Temp/r115/backup/gen_r2188_47d44ec51fa325c5.py'
OUT = r'D:/Temp/r115/out/cand_r2189.py'
EXPECT_BASE = '47d44ec51fa325c5'

CALL_ANCHOR = [
    "            _or_expr = {'type': 'BoolOp', 'op': 'or', 'values': [_and_expr, _c]}",
    "            return self._convert_lambda_function_objects(_or_expr)",
]
CALL_NEW = [
    "            _or_expr = {'type': 'BoolOp', 'op': 'or', 'values': [_and_expr, _c]}",
    "            # [R21-89] fold-window guard completion, identification time, before the",
    "            # arm/else walks of this same statement start.",
    "            self._r2189_fold_window_guards(region, _arm_blocks, _e, _r2188_else,",
    "                                           bool(_r2188_chain))",
    "            return self._convert_lambda_function_objects(_or_expr)",
]
DEF_ANCHOR = ["    def _r4701_and_lift_or_tail(self, region, cond_block, expr):"]

NEW_METHOD = r'''    def _r2189_fold_window_guards(self, region, arm_blocks, e_block, inherited_else,
                                  chain_inherited):
        """[R21-89] complete the tests a fold-window walks but never declares.

        An `(A and B) or C` fold rewrites THIS statement's own arm window (and, when the
        tail leg carries an else list, the chain continuation it inherits from it).  A block
        B inside one of those two lists can be a bare condition block: it holds one whole
        boolean test and its last instruction is the conditional jump over its body, while
        the bottom-up reduction declared no region for it and instead recorded the test as
        an `elif_conditions` entry of a LEG region that this fold has just consumed (the
        leg's test was lifted into the folded expression, so that region is never generated
        and never walks its own elif list).  The branch walk `_process_if_blocks` then sends
        B to `_generate_block_statements`, which drops the test as jump scaffolding and
        emits no statement: the guard disappears, its body is hoisted one level, and the
        continuation -- claimed as the `else` of the nested region built at B's fall-through
        block -- re-renders as a mis-attached `else:`.  Measured faces on the `@`-chain: the
        swallowed `if now_date != self.first_run_date:` guard inside the arm, and the
        ladder leg `check_trading_time(...)` of the inherited continuation rendered as a
        bare `else:`.

        Identification-time re-declaration (the claim MOVES; nothing is copied, re-marked or
        re-printed, and this runs before the statement's own walks begin):

          (1) B and its list-successor F are consecutive members of one of the fold's own
              window lists; B is not any region's entry or condition_block;
          (2) B's last instruction (after the resident cleanup-noise filter) is a forward
              conditional jump of IF_FALSE polarity whose target T is a block at-or-after B
              and a member of the same list; `NONE_CHECK_OPS` excluded, `CONDITIONAL_JUMP_OPS`
              required -- the same polarity/opcode-class conjuncts as
              `_r2188_and_prefix_or_tail` conjunct (2)-(3) and `_r4701_and_lift_or_tail`;
          (3) B is TEST-PURE: no non-jump instruction of B belongs to a statement-forming
              opcode class (STORE_*/DELETE_*/RETURN/RAISE/JUMP_*/FOR_ITER/SETUP_*/YIELD*/
              IMPORT_*/MAKE_FUNCTION/BREAK/CONTINUE/DUP_*/UNPACK/POP_*/append-family/SEND/
              async/exception machinery), i.e. B carries no leading statement of its own --
              a block with statements stays with the resident pre-statement extraction;
          (4) F is a successor of B (its fall-through) and lies after B, and no other
              successor of B besides T enters the window; the window win = list
              members with offset in (B, T) is non-empty and contains F.

        Then a new IfRegion N is declared for B: entry=condition_block=B,
        then_blocks=win, merge_block=T.  Regions whose entry lies in win are re-parented to
        N (the [R21-88] re-parent semantics, child list sorted by entry) so nested regions
        stay single abstract nodes referenced by entry (principles 3/4), and N.parent is the
        folded region, so the resident `get_entry_region_for_block` -> `_nested_if_entry_generate`
        -> `_generate_region` -> `_generate_if` path emits the guard as one If node.  The
        stale claim is removed in the same step: B is dropped from every region's
        `elif_conditions` (with its parallel `elif_bodies` entry), which is also what lifts
        the resident `_generate_if` refusal `region.entry in r.elif_conditions` -- a refusal
        that is sound while the claimant still emits and dead once the fold has lifted that
        claimant's test.

        Continuation handling, decided by the window's own successor edges (no threshold, no
        magnitude trigger):
          (a) some block of win has T as a successor (the body flows INTO T): T is where the
              parent sequence resumes.  T is left in the list for the parent walk, and any
              region R with entry in win that claims `else_blocks == [T]` and nothing else
              loses that claim (else_blocks := [], T dropped from R.blocks, R.merge_block :=
              T): T is B's own jump target reached from every path of B's body, so it is
              postdominator code, never an else arm.
          (b) no block of win flows into T and every successor of win outside win lies at-or-
              after T: T is B's alternative arm.  The arm claim MOVES with the blocks that
              follow it: N.else_blocks = the list members at-or-after T and those members
              leave the parent list (unique membership: they are now N's, and N is emitted by
              the very walk that used to hold them), which is what lets the single-arm ladder
              render as an `elif` leg of the folded statement instead of a bare `else:` body.

        Any window or block failing (1)-(4), and every region that never reaches this fold,
        is left exactly as [R21-88] declared it, so the product stays byte-identical.
        """
        try:
            _noise = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PRECALL', 'KW_NAMES',
                      'COPY_FREE_VARS', 'MAKE_CELL')
            _stmt_prefix = ('STORE_', 'DELETE_', 'RETURN', 'RAISE', 'JUMP_', 'FOR_ITER',
                            'SETUP_', 'YIELD', 'IMPORT_', 'MAKE_FUNCTION', 'BREAK',
                            'CONTINUE', 'DUP_', 'UNPACK', 'POP_', 'LIST_APPEND',
                            'MAP_ADD', 'SET_ADD', 'CALL_INTRINSIC', 'SEND', 'GET_AITER',
                            'GET_ANEXT', 'BEFORE_ASYNC_WITH', 'BEFORE_WITH',
                            'WITH_EXCEPT_START', 'LOAD_BUILD_CLASS', 'END_FOR',
                            'PUSH_EXC_INFO')
            _regions = self.region_analyzer.regions
            if e_block is None:
                return
            _owned = set()
            for _q in _regions:
                for _eb in (getattr(_q, 'entry', None), getattr(_q, 'condition_block', None)):
                    if _eb is not None:
                        _owned.add(_eb)
            _wins = [('arm', list(arm_blocks or []))]
            if chain_inherited:
                _wins.append(('else', list(inherited_else or [])))
            _decl = []
            for _tag, _L in _wins:
                if len(_L) < 3:
                    continue
                for _k in range(len(_L) - 1):
                    _b, _f = _L[_k], _L[_k + 1]
                    if (_b is None or _f is None or _b in _owned
                            or _b in self.generated_blocks
                            or _f.start_offset <= _b.start_offset):
                        continue
                    _ins = [x for x in (_b.instructions or [])
                            if getattr(x, 'opname', None) not in _noise]
                    if len(_ins) < 2:
                        continue
                    _li = _ins[-1]
                    if ('IF_FALSE' not in str(_li.opname)
                            or _li.opname in NONE_CHECK_OPS
                            or _li.opname not in CONDITIONAL_JUMP_OPS
                            or getattr(_li, 'argval', None) is None
                            or any(str(x.opname).startswith(_stmt_prefix) or
                                   x.opname in NONE_CHECK_OPS for x in _ins[:-1])):
                        continue
                    _t = self.cfg.get_block_by_offset(_li.argval)
                    if _t is None or _t.start_offset <= _b.start_offset or _t not in _L:
                        continue
                    _sucs = [s for s in (getattr(_b, 'successors', None) or [])
                             if s is not None]
                    if _f not in _sucs:
                        continue
                    # the window is entered only through F: no other successor of B (besides
                    # its jump target T) lands inside (F, T) -- e.g. a function-tail edge
                    # outside the window does not disqualify the block
                    if any(s is not _f and s is not _t and s is not _b
                           and _f.start_offset <= s.start_offset < _t.start_offset
                           for s in _sucs):
                        continue
                    _win = [x for x in _L if x is not None and x is not _b and x is not _t
                            and _f.start_offset <= x.start_offset < _t.start_offset]
                    if not _win or _f not in _win:
                        continue
                    _flows_in = any(_t is _s for _w in _win
                                    for _s in (getattr(_w, 'successors', None) or []))
                    _arm_tail = []
                    if not _flows_in:
                        _outside = [_s for _w in _win for _s in (getattr(_w, 'successors', None) or [])
                                    if _s is not None and _s not in _win and _s is not _b]
                        if not _outside or any(
                                s.start_offset < _t.start_offset for s in _outside):
                            continue
                        _arm_tail = [x for x in _L if x is not None
                                     and x.start_offset >= _t.start_offset]
                        if not _arm_tail or _t not in _arm_tail:
                            continue
                    _decl.append((_tag, _L, _b, list(_win), _t, _flows_in, _arm_tail))
                    _owned.add(_b)
            for _tag, _L, _b, _win, _t, _flows_in, _arm_tail in _decl:
                try:
                    _ws = set(_win)
                    _n = IfRegion(region_type=RegionType.IF, entry=_b, condition_block=_b,
                                  then_blocks=list(_win),
                                  else_blocks=([] if _flows_in else list(_arm_tail)),
                                  merge_block=_t,
                                  blocks=(set([_b]) | _ws
                                          if _flows_in else (set([_b]) | _ws | set(_arm_tail))))
                    _n.parent = region
                    _regions.append(_n)
                    for _q in _regions:
                        if _q is _n or _q.entry is None or _q.entry not in _ws:
                            # only the guard's OWN window is re-parented: the claimed arm
                            # tail is already referenced by its region entries, and moving
                            # an entry-tail region (or its BoolOp/chained-compare child) out
                            # from under its own parent would break that region's condition
                            # extraction (measured: the leg's `A and B` test disappeared)
                            continue
                        _old = getattr(_q, 'parent', None)
                        if _old is not None and isinstance(getattr(_old, 'children', None), list):
                            try:
                                _old.children.remove(_q)
                            except Exception:
                                pass
                        _q.parent = _n
                        if isinstance(getattr(_n, 'children', None), list):
                            _n.children.append(_q)
                    if isinstance(getattr(_n, 'children', None), list):
                        try:
                            _n.children.sort(key=lambda x: (x.entry.start_offset
                                                            if x.entry is not None else -1))
                        except Exception:
                            pass
                    for _q in _regions:
                        _ec = list(getattr(_q, 'elif_conditions', None) or [])
                        if not _ec or _b not in _ec:
                            continue
                        _idx = _ec.index(_b)
                        _eb = list(getattr(_q, 'elif_bodies', None) or [])
                        _q.elif_conditions = [x for _j, x in enumerate(_ec) if _j != _idx]
                        if _idx < len(_eb):
                            _q.elif_bodies = [x for _j, x in enumerate(_eb) if _j != _idx]
                    if not _flows_in:
                        # No list surgery: the parent list keeps referencing win/T because
                        # the resident dispatch gate requires the nested region's blocks to
                        # be members of the walked list; those members are then covered by
                        # N's own post-generation claim and skipped by the parent pass, so
                        # each block still has exactly one emitter (principle 2).
                        continue
                    for _q in _regions:
                        if (not isinstance(_q, IfRegion) or _q is _n or _q.entry is None
                                or _q.entry not in _ws):
                            continue
                        if list(getattr(_q, 'else_blocks', None) or []) != [_t]:
                            continue
                        _q.else_blocks = []
                        _qb = getattr(_q, 'blocks', None)
                        _q.blocks = ([x for x in _qb if x is not _t] if isinstance(_qb, list)
                                     else (set(_qb or []) - {_t}))
                        _q.merge_block = _t
                except Exception:
                    continue
        except Exception:
            return
'''


def h16(data):
    return hashlib.sha256(data).hexdigest()[:16]


raw = open(BASE, 'rb').read()
assert h16(raw) == EXPECT_BASE, 'base sha16 %s != %s' % (h16(raw), EXPECT_BASE)
assert raw[:3] == b'\xef\xbb\xbf', 'base lacks BOM'
text = raw[3:].decode('utf-8')
assert '\r' not in text.replace('\r\n', ''), 'base has stray CR'
lines = text.split('\r\n')
assert '\n' not in ''.join(lines), 'base has bare LF'


def find_block(seq, anchor):
    hits = [i for i in range(len(seq) - len(anchor) + 1) if seq[i:i + len(anchor)] == anchor]
    assert len(hits) == 1, 'anchor hits=%d for %r' % (len(hits), anchor[0])
    return hits[0]


assert '    def _r2189_fold_window_guards(self' not in lines, 'already patched'
i0 = find_block(lines, CALL_ANCHOR)
i1 = find_block(lines, DEF_ANCHOR)
assert i0 < i1, 'call anchor not before def anchor'

new = (lines[:i0] + CALL_NEW + lines[i0 + len(CALL_ANCHOR):i1]
       + NEW_METHOD.replace('\r\n', '\n').split('\n') + lines[i1:])
out_text = '\r\n'.join(new)
assert '\r\r\n' not in out_text and '\n' not in out_text.replace('\r\n', '')
blob = b'\xef\xbb\xbf' + out_text.encode('utf-8')
open(OUT, 'wb').write(blob)
py_compile.compile(OUT, doraise=True, cfile=OUT + 'c')
print('[patch] base=%s -> candidate=%s bytes=%d lines=%d' % (
    EXPECT_BASE, h16(blob), len(blob), len(new)))
