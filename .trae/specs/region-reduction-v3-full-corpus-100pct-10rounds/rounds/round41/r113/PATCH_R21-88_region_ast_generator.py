# -*- coding: utf-8 -*-
r"""PATCH_R21-88_region_ast_generator.py — [R21-86] `59a405837c22a4cb` -> [R21-88] candidate.

FROM:  D:/Temp/r113/backup/gen_r2186_59a405837c22a4cb.py   (sha16 59a405837c22a4cb, the
       campaign's best-known arm generator = [R21-86], itself built from the landed bytes
       566ff5c502276e48 by rounds/round41/r111/PATCH_R21-86_region_ast_generator.py)
TO:    D:/Temp/r113/core/cfg/region_ast_generator.py        (sha16 printed at the end)

[R21-88] SUBSUMES the banked [R21-87] fold (`ed07b60b970e545d`): it re-uses the same
positive-polarity `(A and B) or C` identification criteria verbatim, and changes exactly
ONE decision — what happens at the fold's tail-leg T.  [R21-87] narrows the folded
region to the arm window `[arm, E)` (E = T's other jump target) and re-declares the
merge as E; any elif ladder that E opens is then orphaned (measured row-5: -26
instructions, the `@7582` arm window cutting the `check_trading_time` /
`AFTER_TRADING_END` / `time.sleep(FPS)` tail).  [R21-88] reads the CHAIN-CONTINUATION
fact from region data instead: when T is the condition block of its own IfRegion Tr and
Tr declares a non-empty `else_blocks` list lying entirely at-or-after E, the ladder is
the folded statement's own continuation, and the fold inherits Tr's arm declaration
(then = arm window, else = Tr's else list, merge = Tr's merge), marking only the leg
blocks.  Nothing is un-marked or re-printed; the ladder keeps a single emitter — this
statement's else walk — and the [R21-87] conservation refusal remains for strays that
no Tr else list can hold.  (The pure tail-transfer variant that re-parented strays by
forward reachability from E was built and measured first — row v2: the while-body
parent walk is a block-list snapshot, so the transferred tail orphaned: `212/-282/-33`,
matching [R21-87] row-2's no-guard shape; recorded in MEASURE_R21-88 and rejected.)

The patch is a pure ADDITIVE two-anchor edit of [R21-86] (it touches no [R21-86] line), is
IDEMPOTENT (detects its own insertion and exits without rewriting), and uses ABSOLUTE paths
only.  File invariants asserted after writing: UTF-8 BOM present, 100 % CRLF, zero bare LF,
zero "\r\r\n", `python -X utf8 -m py_compile` clean.

Edit 1 (new resident-scale sibling): insert `_r2188_and_prefix_or_tail` immediately before
  `_r4701_and_lift_or_tail` — the positive-polarity sibling of that landed ruler, same
  family, same evidence class (jump polarity + region/block data only).
Edit 2 (call site): invoke it in `_if_generate_normal` right after the `inline_boolop_chains`
  / `_discover_predicate_and_chain` condition assembly and before the arm walk, i.e. at
  identification time, before the statement is emitted.
"""
import hashlib
import os
import subprocess
import sys

SRC = 'D:/Temp/r113/backup/gen_r2186_59a405837c22a4cb.py'
DST = 'D:/Temp/r113/core/cfg/region_ast_generator.py'
EXPECT_SRC = '59a405837c22a4cb'

ANCHOR_A = "    def _r4701_and_lift_or_tail(self, region, cond_block, expr):"

ANCHOR_B = ("                finally:\r\n"
            "                    _cpg.discard(id(region))\r\n"
            "        self.generated_blocks.add(cond_block)")

METHOD = """    def _r2188_and_prefix_or_tail(self, region, cond_block, condition):
        \"\"\"[R21-88] positive-polarity `(A and B) or C` fold WITH chain-continuation read.

        Same identification as the banked [R21-87] fold (six conjuncts, jump polarity +
        region/block data only — no names, no absolute-offset keys, no counters, no
        magnitude triggers): cond_block ends IF_FALSE -> T (T == region.merge_block,
        region.else_blocks empty); T ends IF_FALSE -> E with exactly one remaining
        successor inside region.then_blocks (the arm); one IfRegion Mr (condition_block
        is entry) between them whose last test leg jumps IF_TRUE -> arm; a predecessor of
        T from inside the Mr leg hands the and-leg's false path to the tail leg; the
        three leg expressions A, B, C rebuild with the resident rulers.

        [R21-88] delta (the difference from [R21-87]): where [R21-87] narrows the fold
        to the arm window and re-declares the merge as E, orphaning any elif ladder
        that E opens (the measured row-5 -26 tail cut), [R21-88] reads the
        CONTINUATION fact from region data: if T is the condition block of its own
        IfRegion Tr and Tr declares a non-empty else arm list starting no earlier
        than E, the ladder belongs to this statement, and the fold inherits Tr's arm
        declaration (then = arm window, else = Tr's else list, merge = Tr's merge),
        marking only the leg blocks.  Ladder blocks stay unclaimed and are emitted
        exactly once by this statement's own else walk.  A stray the Tr else list
        cannot hold keeps the strict [R21-87] conservation refusal (this is what
        makes the [R21-86] released reconnect run render inside the @7164 chain
        instead of being orphaned the way the bare tail-transfer did — measured,
        row v2: -282/-33).  Nothing is marked, un-marked or re-printed after
        emission; one-way dataflow, unique emitter (principle 2), nested regions
        stay abstract nodes (principles 3 and 4).

        Reduction: test = BoolOp(or, [BoolOp(and, [A, B]), C]); region.then_blocks is
        narrowed to the arm window; region.merge_block is re-declared to E; leg test
        blocks and pure-connection blocks between the legs are marked generated_offsets/
        generated_blocks — the same hand-back family as the landed
        _r4701_and_lift_or_tail.  Any conjunct failing => return None and the existing
        path is byte-identical to the base.
        \"\"\"
        try:
            if region is None or cond_block is None:
                return None
            if getattr(region, 'else_blocks', None):
                return None
            _tb = getattr(region, 'then_blocks', None)
            if not _tb:
                return None
            _li = cond_block.get_last_instruction()
            if (_li is None or getattr(_li, 'argval', None) is None
                    or 'IF_FALSE' not in _li.opname
                    or _li.opname in NONE_CHECK_OPS):
                return None
            _t_off = _li.argval
            _t = self.cfg.get_block_by_offset(_t_off)
            if _t is None or _t is not getattr(region, 'merge_block', None):
                return None
            if _t is cond_block or _t_off <= cond_block.start_offset:
                return None
            _ti = _t.get_last_instruction()
            if (_ti is None or getattr(_ti, 'argval', None) is None
                    or 'IF_FALSE' not in _ti.opname
                    or _ti.opname in NONE_CHECK_OPS):
                return None
            _e_off = _ti.argval
            if _e_off == _t_off:
                return None
            _e = self.cfg.get_block_by_offset(_e_off)
            if _e is None:
                return None
            _arm_c = [s for s in (_t.successors or [])
                      if s.start_offset != _e_off and s in _tb]
            if len(_arm_c) != 1:
                return None
            _arm = _arm_c[0]
            _m_c = [s for s in (cond_block.successors or [])
                    if s.start_offset != _t_off
                    and cond_block.start_offset < s.start_offset < _t_off]
            _regions = self.region_analyzer.regions
            _mr = None
            _tr = None
            for _r in _regions:
                if not isinstance(_r, IfRegion):
                    continue
                if _r.entry is _t:
                    _tr = _r
                for _s in _m_c:
                    if _r.entry is _s and getattr(_r, 'condition_block', None) is _s:
                        _mr = _r
            if _mr is None or _tr is None:
                return None
            if getattr(_tr, 'condition_block', None) is not _t:
                return None
            if len(_m_c) != 1:
                return None
            _m = _m_c[0]
            _ccb = list(getattr(_mr, 'chained_compare_blocks', None) or [])
            _leg = [_m] + _ccb
            _lt = max(_leg, key=lambda b: b.start_offset)
            _lti = _lt.get_last_instruction()
            if (_lti is None or getattr(_lti, 'argval', None) is None
                    or 'IF_TRUE' not in _lti.opname
                    or _lti.opname in NONE_CHECK_OPS
                    or _lti.argval != _arm.start_offset):
                return None
            if not any(p is not cond_block and p.start_offset >= _m.start_offset
                       and p.start_offset < _t_off
                       for p in (_t.predecessors or [])):
                return None
            _skip_ops = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
            _a = condition
            if _a is None:
                _a_instrs = [i for i in cond_block.instructions
                             if i.opname not in _skip_ops and i is not _li]
                _a = self.expr_reconstructor.reconstruct(_a_instrs) if _a_instrs else None
            if _a is None:
                return None
            if _ccb and getattr(_mr, 'chained_compare_ops', None):
                _b = self._build_chained_compare_from_region_data(_mr)
            else:
                _b_instrs = [i for i in _lt.instructions
                             if i.opname not in _skip_ops and i is not _lti]
                _b = self.expr_reconstructor.reconstruct(_b_instrs) if _b_instrs else None
            if _b is None:
                return None
            _c_instrs = [i for i in _t.instructions
                         if i.opname not in _skip_ops and i is not _ti]
            _c = self.expr_reconstructor.reconstruct(_c_instrs) if _c_instrs else None
            if _c is None:
                return None
            _cleanup_ops = ('POP_TOP', 'NOP', 'RESUME', 'CACHE', 'JUMP_FORWARD',
                            'EXTENDED_ARG')
            _mark = [_m, _t, _lt] + _ccb
            for _pb in (list(getattr(region, 'blocks', None) or [])
                        + list(getattr(_mr, 'blocks', None) or [])):
                if _pb is None or _pb is _arm or _pb is _e:
                    continue
                if not (_m.start_offset <= _pb.start_offset < _t_off):
                    continue
                if all(i.opname in _cleanup_ops for i in _pb.instructions):
                    _mark.append(_pb)
            _arm_blocks = sorted((b for b in _tb
                                   if _arm.start_offset <= b.start_offset < _e_off),
                                  key=lambda b: b.start_offset)
            if _arm not in _arm_blocks:
                return None
            _r2188_keep = set(_arm_blocks) | set(_mark)
            _r2188_stray = [b for b in _tb if b not in _r2188_keep]
            # [R21-88] chain-continuation read: the tail leg T is itself the condition
            # block of its own IfRegion Tr.  When Tr carries a non-empty else arm list
            # that begins no earlier than this fold's merge E, the ladder E opens is a
            # CONTINUATION of the folded statement, not separate code: the fold
            # inherits Tr's arm declaration — then_blocks = this arm window,
            # else_blocks = Tr's else list, merge_block = Tr's merge.  Leg blocks (T
            # included) are marked; Tr's arm/else blocks are NOT marked, so the ladder
            # is emitted exactly once by this statement's own else walk (principle 2:
            # unique emitter; one-way dataflow at identification time; no un-mark and
            # no re-print).  That removes the [R21-87] row-5 failure mode where the
            # narrow merge:=E orphaned the elif tail (-26 instructions).  When strays
            # exist that no Tr else list can hold, the strict [R21-87] conservation
            # refusal still fires, so a chain that owns code it cannot render never
            # folds.
            _r2188_else = list(getattr(_tr, 'else_blocks', None) or [])
            _r2188_chain = (
                bool(_r2188_else)
                and getattr(_tr, 'condition_block', None) is _t
                and getattr(_tr, 'merge_block', None) is not None
                and all(b in _r2188_keep
                        or (_arm.start_offset <= b.start_offset < _e_off)
                        for b in (getattr(_tr, 'then_blocks', None) or []))
                and all(b is not None and b.start_offset >= _e_off
                        for b in _r2188_else))
            if _r2188_stray and not _r2188_chain:
                return None
            _seen = set()
            for _mb in _mark:
                if _mb in _seen:
                    continue
                _seen.add(_mb)
                self.generated_blocks.add(_mb)
                self.generated_offsets.add(_mb.start_offset)
            region.then_blocks = _arm_blocks
            if _r2188_chain:
                region.else_blocks = _r2188_else
                region.merge_block = _tr.merge_block
                # The inherited ladder becomes part of THIS statement's own block
                # record, so the region's post-generation claim covers it after the
                # else walk emits it exactly once (unique emitter, principle 2).
                _r2188_own = list(getattr(region, 'blocks', None) or [])
                _r2188_owns = set(_r2188_own)
                region.blocks = _r2188_own + [
                    b for b in (getattr(_tr, 'blocks', None) or [])
                    if b is not None and b not in _r2188_owns]
            else:
                region.merge_block = _e
            _and_expr = {'type': 'BoolOp', 'op': 'and', 'values': [_a, _b]}
            _or_expr = {'type': 'BoolOp', 'op': 'or', 'values': [_and_expr, _c]}
            return self._convert_lambda_function_objects(_or_expr)
        except Exception:
            return None

    def _r2188_tail_ownership_prepass(self):
        \"\"\"[R21-88] tail-ownership re-declaration (identification time, before dispatch).

        An or-chain region R whose arm declaration was over-extended by the bottom-up
        reduction lists, in its own then_blocks, the very statements that follow the
        folded chain in the dispatching parent sequence (code at or after the fold
        merge E). The fold then cannot honour its arm-window conservation and refuses,
        keeping the nested or-chain scaffolding alive. This pre-pass re-declares
        ownership once, before anything is emitted:

          (a) R matches the _r2188_and_prefix_or_tail shape conjuncts (1)-(5) —
              jump polarity + region data only (R.else_blocks empty; cond leg ends
              IF_FALSE->T == R.merge_block; T ends IF_FALSE->E, E != T; exactly one
              other T-successor in R.then_blocks (the arm); exactly one Mr leg
              region between, whose last test jumps IF_TRUE->arm);
          (b) every R.then_blocks member at-or-after E is forward-reachable from E
              through successor edges without crossing a window or leg block — the
              reachability walk's domain floor is the E-offset, the region-data
              statement of “code after this statement” (no magnitude comparison, no
              absolute-offset key);
          (c) a dispatching parent P exists: the nearest region.parent-chain ancestor
              whose blocks/body_blocks/then_blocks/else_blocks contain R.entry.
        Then the tail blocks are removed from R.then_blocks/R.blocks and inserted —
        positionally, into the same list that holds R.entry and into P.blocks — and
        every region whose entry was transferred is re-parented to P. Membership stays
        unique throughout (blocks move, never duplicate); nothing has been claimed or
        emitted yet at pre-pass time, so no un-mark, no re-print, one-way dataflow.
        Any R failing (a)/(b)/(c) is left untouched and the product is byte-identical
        to [R21-86].
        \"\"\"
        try:
            _regions = self.region_analyzer.regions
        except Exception:
            return
        _cleanup_ops = ('POP_TOP', 'NOP', 'RESUME', 'CACHE', 'JUMP_FORWARD',
                        'EXTENDED_ARG')
        for _r in sorted(_regions, key=lambda x: (x.entry.start_offset
                                                  if x.entry is not None else -1)):
            try:
                if not isinstance(_r, IfRegion) or _r.entry is None:
                    continue
                if getattr(_r, 'else_blocks', None):
                    continue
                _c = _r.condition_block
                _tb = getattr(_r, 'then_blocks', None)
                if _c is None or not _tb:
                    continue
                _li = _c.get_last_instruction()
                if (_li is None or getattr(_li, 'argval', None) is None
                        or 'IF_FALSE' not in _li.opname
                        or _li.opname in NONE_CHECK_OPS):
                    continue
                _t = self.cfg.get_block_by_offset(_li.argval)
                if _t is None or _t is not getattr(_r, 'merge_block', None):
                    continue
                _ti = _t.get_last_instruction()
                if (_ti is None or getattr(_ti, 'argval', None) is None
                        or 'IF_FALSE' not in _ti.opname
                        or _ti.opname in NONE_CHECK_OPS):
                    continue
                _e = self.cfg.get_block_by_offset(_ti.argval)
                if _e is None or _e is _t:
                    continue
                _e_off = _e.start_offset
                _arm_c = [s for s in (_t.successors or [])
                          if s.start_offset != _e_off and s in _tb]
                if len(_arm_c) != 1:
                    continue
                _arm = _arm_c[0]
                if _arm.start_offset >= _e_off:
                    continue
                _m_c = [s for s in (_c.successors or [])
                        if s.start_offset != _t.start_offset
                        and _c.start_offset < s.start_offset < _t.start_offset]
                if len(_m_c) != 1:
                    continue
                _m = _m_c[0]
                _mr = None
                for _q in _regions:
                    if (isinstance(_q, IfRegion) and _q.entry is _m
                            and getattr(_q, 'condition_block', None) is _m):
                        _mr = _q
                if _mr is None:
                    continue
                _ccb = list(getattr(_mr, 'chained_compare_blocks', None) or [])
                _lt = max([_m] + _ccb, key=lambda b: b.start_offset)
                _lti = _lt.get_last_instruction()
                if (_lti is None or getattr(_lti, 'argval', None) is None
                        or 'IF_TRUE' not in _lti.opname
                        or _lti.opname in NONE_CHECK_OPS
                        or _lti.argval != _arm.start_offset):
                    continue
                _tail = [b for b in _tb if b is not None
                         and b.start_offset >= _e_off]
                if not _tail:
                    continue
                _win = set(b for b in _tb
                           if _arm.start_offset <= b.start_offset < _e_off)
                _leg = {_c, _t, _m, _lt} | set(_ccb)
                for _pb in (getattr(_r, 'blocks', None) or []):
                    if (_pb is not None and _pb is not _arm and _pb is not _e
                            and _m.start_offset <= _pb.start_offset < _t.start_offset
                            and all(i.opname in _cleanup_ops
                                    for i in _pb.instructions)):
                        _leg.add(_pb)
                _reach = {_e}
                _work = [_e]
                while _work:
                    _cur = _work.pop()
                    for _s in (getattr(_cur, 'successors', None) or []):
                        if _s is None or _s.start_offset < _e_off:
                            continue
                        if _s in _win or _s in _leg or _s in _reach:
                            continue
                        _reach.add(_s)
                        _work.append(_s)
                if not all(b in _reach for b in _tail):
                    continue
                _p = getattr(_r, 'parent', None)
                _host_attrs = None
                while _p is not None:
                    _hits = []
                    for _attr in ('body_blocks', 'then_blocks', 'else_blocks',
                                  'blocks'):
                        _lst = getattr(_p, _attr, None)
                        if isinstance(_lst, list) and _r.entry in _lst:
                            _hits.append(_attr)
                    if _hits:
                        # insert only into the list(s) that hold R.entry (the
                        # sequence the folded statement belongs to) plus the
                        # region's own blocks record; never into sibling arm
                        # lists that do not contain R.entry.
                        _host_attrs = _hits if 'blocks' in _hits else _hits + [
                            a for a in ('blocks',)
                            if isinstance(getattr(_p, a, None), list) and a not in _hits]
                        break
                    _p = getattr(_p, 'parent', None)
                if _p is None or _host_attrs is None:
                    continue
                _ms = set()
                _moved = []
                for _b in (list(_tb) + list(getattr(_r, 'blocks', None) or [])):
                    if (_b is not None and _b.start_offset >= _e_off
                            and _b in _reach and _b not in _ms):
                        _ms.add(_b)
                        _moved.append(_b)
                if not _moved:
                    continue
                _r.then_blocks = [b for b in _tb if b not in _ms]
                _r.blocks = [b for b in (getattr(_r, 'blocks', None) or [])
                             if b not in _ms]
                for _attr in _host_attrs:
                    _lst = getattr(_p, _attr)
                    _have = set(id(x) for x in _lst)
                    for _b in sorted(_moved, key=lambda x: x.start_offset):
                        if id(_b) in _have:
                            continue
                        _have.add(id(_b))
                        _idx = len(_lst)
                        for _k in range(len(_lst)):
                            if getattr(_lst[_k], 'start_offset', 0) > _b.start_offset:
                                _idx = _k
                                break
                        _lst.insert(_idx, _b)
                for _q in _regions:
                    if _q is _r or _q is _mr or _q.entry is None:
                        continue
                    if _q.entry in _ms and getattr(_q, 'parent', None) is not _p:
                        _old = _q.parent
                        if _old is not None and isinstance(
                                getattr(_old, 'children', None), list):
                            try:
                                _old.children.remove(_q)
                            except Exception:
                                pass
                        _q.parent = _p
                        if isinstance(getattr(_p, 'children', None), list):
                            _p.children.append(_q)
                if isinstance(getattr(_p, 'children', None), list):
                    try:
                        _p.children.sort(key=lambda x: (x.entry.start_offset
                                                        if x.entry is not None else -1))
                    except Exception:
                        pass
            except Exception:
                continue

"""

ANCHOR_C = "        for region in top_level_regions:"

CALL_C = ("        # [R21-88] tail-ownership re-declaration, identification-time, "
          "before any dispatch\r\n"
          "        self._r2188_tail_ownership_prepass()\r\n"
          "        for region in top_level_regions:")

CALL = ("                finally:\r\n"
        "                    _cpg.discard(id(region))\r\n"
        "        # [R21-88] positive-polarity `(A and B) or C` fold with the\r\n"
        "        # chain-continuation read, applied at identification time after the\r\n"
        "        # and before the arm walk (criteria in _r2188_and_prefix_or_tail).\r\n"
        "        # Returns None otherwise => existing path, byte-identical to [R21-86].\r\n"
        "        _r2188_test = self._r2188_and_prefix_or_tail(region, cond_block, condition)\r\n"
        "        if _r2188_test is not None:\r\n"
        "            condition = _r2188_test\r\n"
        "        self.generated_blocks.add(cond_block)")


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main():
    assert os.path.isabs(SRC) and os.path.isabs(DST), 'absolute paths required'
    raw = open(SRC, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf'), 'source has no BOM'
    assert h16(SRC) == EXPECT_SRC, 'base is not [R21-86]: %s' % h16(SRC)
    src = raw.decode('utf-8-sig')
    assert '\n' not in src.replace('\r\n', ''), 'source contains bare LF'
    already = ('_r2188_and_prefix_or_tail' in src)
    if already:
        print('[patch] anchor text already present -> idempotent no-op (re-copy only)')
    else:
        assert src.count(ANCHOR_A) == 1, 'anchor A count=%d' % src.count(ANCHOR_A)
        assert src.count(ANCHOR_B.replace('\r\n', '\n')) == 1 or src.count(ANCHOR_B) == 1, 'anchor B not unique'
        if ANCHOR_B in src:
            src = src.replace(ANCHOR_B, CALL, 1)
        else:
            src = src.replace(ANCHOR_B.replace('\r\n', '\n'),
                              CALL.replace('\r\n', '\n'), 1)
        assert src.count(ANCHOR_C) == 1, 'anchor C count=%d' % src.count(ANCHOR_C)
        src = src.replace(ANCHOR_C, CALL_C, 1)
        src = src.replace(ANCHOR_A, METHOD + ANCHOR_A, 1)
    out = b'\xef\xbb\xbf' + src.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    assert b'\r\r\n' not in out, 'CR CR LF introduced'
    body = out.decode('utf-8-sig')
    assert '\n' not in body.replace('\r\n', ''), 'bare LF introduced'
    assert body.count('\r\n') == len(body.split('\n')) - 1, 'not 100%% CRLF'
    open(DST, 'wb').write(out)
    r = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'py_compile', DST],
                       capture_output=True)
    print('[patch] py_compile rc=%d %s' % (r.returncode,
                                           (r.stderr or b'').decode('utf-8', 'replace')[:300]))
    assert r.returncode == 0
    print('[patch] bytes=%d bom=%s sha16=%s -> %s' % (
        len(out), out.startswith(b'\xef\xbb\xbf'), h16(DST), DST))
    assert r.returncode == 0 and os.path.getsize(DST) > 3_000_000


main()
