# -*- coding: utf-8 -*-
"""F-OTHER / quote.check_industry_code — minimal repro (R73 fix3, surg4).

Trigger: an ``assert <or-chain>, msg`` that is the **last statement of the
function**.  CPython then emits one distinct ``LOAD_CONST None; RETURN_VALUE``
block per chain operand (A jumps to block X, B jumps to block Y, X != Y) instead
of one shared continuation block.

The analyzer's backward or-chain walk in
``region_analyzer._detect_assert_boolop_chain`` requires every predecessor's
``POP_JUMP_FORWARD_IF_TRUE`` target to be *block-identical* to the last chain
block's end target (region_analyzer.py: ``p_target is not end_target``), so the
walk stops: the AssertRegion only covers the last operand.  The function then
degrades to ``if not A: assert B, m`` (+ a synthetic ``return None``) instead of
``assert A or B, m`` — the observed
``check_industry_code: Failure: Different control flow``.

The ``*_call`` variants keep a statement after the assert, so CPython shares one
continuation block: they already work today and are the in-family controls that
must keep working after the fix.

PASS criterion (structural, uses only the region's own blocks): some AssertRegion
that owns the RAISE_VARARGS block contains at least two conditional-jump blocks —
i.e. the whole chain was recognised as ONE assert region instead of a bare
``if``/``assert`` split.

Run:  python -X utf8 synth/assert_or_tail.py
"""
import io
import json
import os
import sys
import types

REPO = r'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(REPO)

TRIGGERS = ['assert_or_tail', 'assert_or_triple_tail', 'assert_in_or_tail',
            'assert_and_or_tail']
CONTROLS = ['assert_or_tail_call', 'assert_in_or_tail_call',
            'assert_chain_cmp_tail']


def assert_or_tail(a, b, m):
    assert a or b, m


def assert_or_tail_call(a, b, m):
    assert a or b, m
    g()


def assert_or_triple_tail(a, b, c, m):
    assert a or b or c, m


def assert_in_or_tail(s, ic, m):
    assert ('%s.csv' % s[:-5]) in ic or ('%s.csv' % s[:-3]) in ic, m


def assert_in_or_tail_call(s, ic, m):
    assert ('%s.csv' % s[:-5]) in ic or ('%s.csv' % s[:-3]) in ic, m
    g()


def assert_and_or_tail(a, b, c, m):
    assert a and b or c, m


def assert_chain_cmp_tail(a, m):
    assert 0 < a < 10, m


def g():
    return 1


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def O(b):
    return getattr(b, 'start_offset', None)


def check():
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import AssertRegion
    from core.cfg.region_ast_generator import RegionASTGenerator

    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, 'assert_or_tail.py')
    root = compile(io.open(src, 'rb').read(), src, 'exec')
    codes = {c.co_name: c for c in walk(root, [])}
    results = {}
    for name in TRIGGERS + CONTROLS:
        c = codes[name]
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg, top_level_code=None)
        regions = gen.region_analyzer.analyze()
        raise_off = None
        for b in cfg.get_blocks_in_order():
            if any(i.opname == 'RAISE_VARARGS' for i in b.instructions):
                raise_off = b.start_offset
        best = None
        for r in regions:
            if not isinstance(r, AssertRegion):
                continue
            offs = [O(b) for b in r.blocks]
            if raise_off is None or raise_off not in offs:
                continue
            ncond = sum(1 for b in r.blocks
                        if b.get_last_instruction() is not None
                        and b.get_last_instruction().opname.startswith(
                            'POP_JUMP_FORWARD_IF'))
            if best is None or ncond > best[0]:
                best = (ncond, r)
        results[name] = {
            'family': 'trigger' if name in TRIGGERS else 'control',
            'raise_block': raise_off,
            'assert_regions': sum(1 for r in regions if isinstance(r, AssertRegion)),
            'chain_condition_blocks': best[0] if best else 0,
            'region_entry': O(best[1].entry) if best else None,
            'region_blocks': sorted(O(b) for b in best[1].blocks) if best else None,
            'PASS': bool(best and best[0] >= 2),
        }
    return results


if __name__ == '__main__':
    res = check()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    fails = [k for k, v in res.items() if not v['PASS']]
    print('FAILING=%d/%d %s' % (len(fails), len(res), fails))
    bad_ctrl = [k for k, v in res.items()
                if v['family'] == 'control' and not v['PASS']]
    print('CONTROL_REGRESSION=%d %s' % (len(bad_ctrl), bad_ctrl))
