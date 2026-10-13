# -*- coding: utf-8 -*-
"""CENSUS_R21-66 — read-only fire census of the item-4 predicates (chained-compare while latch).

usage: python -X utf8 census_r95.py <budget_sec> <pathlist> [start]

Computed with the LANDED analyzer in a process that never runs the generator (see FIX doc §2
for the inertness proof).

Code path I own: `_loop_generate_while`'s chained-compare suppression loop
(region_ast_generator.py:8126-8174), gated on region.metadata['is_chained_compare_cond'].

For such a LoopRegion L let SEG = {eval(cond_block)} u {eval(c) for c in condition_chain_blocks},
eval(b) = b's instructions with NOISE_OPS dropped and the conditional-jump terminator dropped, as
opcode-name lists. For each body block b (not header/cond/chain/back-edge) whose terminator is a
conditional jump, split at the last *statement boundary* (STORE_* / POP_TOP) into prefix and tail T:

  hitA  T non-empty, T == some s in SEG, boundary is POP_TOP
        (duplicated latch test fused behind an expression statement; today the block prints as
         body statements -> `if not <chain>: continue`)
  hitB  current `_is_recheck` fires (boundary is STORE_* and T merely *contains* a compare op)
        but T != every s in SEG
        (over-fire: a real `if` whose test reuses the just-stored value -> store hoisted to the
         body tail, the `if` disappears, its then-block prints unconditionally)
  hitC  L.back_edge_block's whole non-jmp sequence == some s in SEG but is outside the
        `_has_only_compare` whitelist (carries CALL/PRECALL) -> today emitted, my rule suppresses

  outB  hitB evaluated for loop regions WITHOUT the chained-compare gate (the boolop path), to
        show my rule cannot reach it.
"""
import marshal
import os
import sys
import time
import types

MIRROR = 'D:/Temp/r95'
sys.path.insert(0, MIRROR)

from core.cfg import build_cfg                                          # noqa: E402
import core.cfg.region_analyzer as ra                                   # noqa: E402
from core.cfg.region_analyzer import CONDITIONAL_JUMP_OPS               # noqa: E402

ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
NOISE = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
STORE_B = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
           'STORE_SUBSCR', 'STORE_ATTR')
RECHECK_OPS = ('COPY', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
ONLY_COMPARE_WL = ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                   'COPY', 'SWAP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'POP_TOP')


def code_objects(root):
    stack = [root]
    while stack:
        c = stack.pop()
        yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                stack.append(k)


def eff(b):
    return [i for i in b.instructions if i.opname not in NOISE]


def eval_seq(b):
    ins = eff(b)
    last = b.get_last_instruction()
    if last is not None and last.opname in CONDITIONAL_JUMP_OPS:
        ins = [i for i in ins if i.offset != last.offset]
    return tuple(i.opname for i in ins)


def split_boundary(ins):
    for idx in range(len(ins) - 1, -1, -1):
        if ins[idx].opname in STORE_B:
            return idx, 'STORE'
        if ins[idx].opname == 'POP_TOP':
            return idx, 'POP_TOP'
    return -1, None


def census_unit(co, want_out):
    cfg = build_cfg(co)
    ana = ra.RegionAnalyzer(cfg)
    regions = ana.analyze()
    seen = set()
    allr = []

    def collect(rs):
        for r in rs:
            if id(r) in seen:
                continue
            seen.add(id(r))
            allr.append(r)
            collect(getattr(r, 'children', None) or [])

    collect(regions)
    rows = []
    n_cc = 0
    n_other = 0
    for r in allr:
        if not isinstance(r, ra.LoopRegion) or r.condition_block is None:
            continue
        md = getattr(r, 'metadata', None) or {}
        # exact reachability gate of region_ast_generator.py:8102-8108
        cc = (bool(md.get('is_chained_compare_cond'))
              and bool(r.condition_chain_blocks)
              and len(md.get('chained_compare_ops') or []) >= 2)
        if cc:
            n_cc += 1
        else:
            n_other += 1
            if not want_out:
                continue
        segs = {eval_seq(r.condition_block)}
        for c in (r.condition_chain_blocks or []):
            if c is not None:
                segs.add(eval_seq(c))
        segs.discard(())
        guard = {r.header_block, r.condition_block, r.back_edge_block}
        guard.update([c for c in (r.condition_chain_blocks or []) if c is not None])
        guard.discard(None)
        hits = {'A': [], 'B': [], 'C': []}
        for b in (r.body_blocks or []):
            if b in guard:
                continue
            ins = eff(b)
            last = b.get_last_instruction()
            if not ins or last is None or last.opname not in CONDITIONAL_JUMP_OPS:
                continue
            nonjmp = [i for i in ins if i.offset != last.offset]
            bi, bk = split_boundary(nonjmp)
            tail = nonjmp[bi + 1:] if bi >= 0 else nonjmp
            tn = tuple(i.opname for i in tail)
            dup = bool(tn) and tn in segs
            has_cmp = any(i.opname in RECHECK_OPS for i in tail)
            if dup and bk == 'POP_TOP' and has_cmp:
                hits['A'].append(b.start_offset)
            if bi >= 0 and bk == 'STORE' and has_cmp and not dup:
                hits['B'].append(b.start_offset)
        be = r.back_edge_block
        if be is not None and be in (r.body_blocks or []):
            bins = eff(be)
            blast = be.get_last_instruction()
            if blast is not None and blast.opname in CONDITIONAL_JUMP_OPS:
                bnon = [i for i in bins if i.offset != blast.offset]
                if tuple(i.opname for i in bnon) in segs and not all(
                        i.opname in ONLY_COMPARE_WL for i in bnon):
                    hits['C'].append(be.start_offset)
        tag = 'CC' if cc else 'OTHER'
        if any(hits.values()):
            rows.append((tag, '%s unit=%s loop@%d cond=@%d seglens=%s A=%s B=%s C=%s' % (
                tag, co.co_name,
                r.entry.start_offset if getattr(r, 'entry', None) else -1,
                r.condition_block.start_offset,
                sorted(len(s) for s in segs),
                hits['A'], hits['B'], hits['C']), dict(hits)))
    return rows, n_cc, n_other


def census_file(p):
    code = marshal.loads(open(p, 'rb').read()[16:])
    tot = {'A': 0, 'B': 0, 'C': 0, 'cc': 0, 'other': 0,
           'oA': 0, 'oB': 0, 'oC': 0}
    lines = []
    for co in code_objects(code):
        if not hasattr(co, 'co_code'):
            continue
        try:
            rows, n_cc, n_other = census_unit(co, True)
        except Exception as exc:
            lines.append('  ANALYZE_FAIL %s: %s' % (co.co_name, exc))
            continue
        tot['cc'] += n_cc
        tot['other'] += n_other
        for tag, text, hits in rows:
            pre = '' if tag == 'CC' else 'o'
            for key in ('A', 'B', 'C'):
                tot[pre + key] += len(hits[key])
            lines.append('  ' + text)
    return tot, lines


def main():
    budget = float(sys.argv[1])
    paths = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    t0 = time.time()
    agg = {'A': 0, 'B': 0, 'C': 0, 'cc': 0, 'other': 0, 'oA': 0, 'oB': 0, 'oC': 0}
    for cursor in range(start, len(paths)):
        if time.time() - t0 > budget:
            print('BUDGET NEXT=%d' % cursor)
            sys.exit(3)
        rel = paths[cursor]
        p = rel if os.path.isabs(rel) else os.path.join(ROOT, rel.replace('/', os.sep))
        if not os.path.isfile(p):
            print('MISSING %s' % rel)
            continue
        try:
            tot, lines = census_file(p)
        except Exception as exc:
            print('FAIL %s: %s' % (rel, exc))
            continue
        for k in agg:
            agg[k] += tot[k]
        print('FILE %s cc_loops=%d other_loops=%d A=%d B=%d C=%d | noncc A=%d B=%d C=%d' % (
            rel, tot['cc'], tot['other'], tot['A'], tot['B'], tot['C'],
            tot['oA'], tot['oB'], tot['oC']))
        for l in lines:
            print(l)
    print('DONE files=%d cc_loops=%d other_loops=%d A=%d B=%d C=%d noncc_A=%d noncc_B=%d noncc_C=%d elapsed=%.0fs'
          % (len(paths), agg['cc'], agg['other'], agg['A'], agg['B'], agg['C'],
             agg['oA'], agg['oB'], agg['oC'], time.time() - t0))


if __name__ == '__main__':
    main()
