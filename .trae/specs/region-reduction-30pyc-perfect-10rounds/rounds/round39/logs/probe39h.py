# -*- coding: utf-8 -*-
"""Round 39 line A, step 8: why does the arm-tail-Continue rule fire in 16
wrong places and 2 right ones?  Print, at every candidate site, the structural
facts that could separate them (T's predecessor count, whether T is the if
region's merge, whether T is the loop's own back edge, T's role).

usage: python -X utf8 probe39h.py
"""
import functools
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(HERE)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402

TARGETS = [
    ('site-packages/IQCommon/strategy/wizard_quant_api.pyc', 'wizard_quant_check_limit', 'FIX'),
    ('site-packages/IQCommon/strategy/wizard_quant_api.pyc', 'add_to_strategy_info', 'REG'),
    ('site-packages/IQCommon/util/user_info_utils.pyc', 'get_vip_user_info', 'REG'),
    ('site-packages/IQCommon/db/db_base.pyc', 'merge', 'REG'),
    ('site-packages/IQData/analysis/strategy.pyc', 'reload_strategy', 'REG'),
    ('site-packages/IQCommon/util/fly_data_source.pyc', 'get_stock_name', 'REG'),
    ('site-packages/IQEngine/klinedata.pyc', 'get_all_real_daily_kline', 'FIX2'),
]

M = G._process_if_blocks
_state = {'tag': None, 'tail': None, 'n': 0}


def o(b):
    return getattr(b, 'start_offset', None)


def last(b):
    return b.get_last_instruction() if b is not None else None


def wrapped(self, blocks, region=None, *a, **k):
    res = M(self, blocks, region, *a, **k)
    if _state['tail'] is None:
        return res
    cfgname = getattr(getattr(self, 'cfg', None), 'name', '?')
    if _state['tail'] not in cfgname:
        return res
    _state['n'] += 1
    loop = getattr(self, '_current_loop', None)
    hdr = getattr(loop, 'header_block', None) if loop else None
    bl = list(blocks or [])
    tail = None
    for b in reversed(bl):
        if b in self.generated_blocks:
            tail = b
            break
    if tail is None:
        return res
    ll = last(tail)
    if ll is None or 'JUMP' in ll.opname:
        return res
    an = getattr(self, 'region_analyzer', None)
    roles = getattr(an, 'block_roles', {}) if an else {}
    rblocks = set(getattr(region, 'blocks', None) or [])
    be = set(getattr(loop, 'back_edge_blocks', None) or [])
    if loop is not None and getattr(loop, 'back_edge_block', None) is not None:
        be.add(loop.back_edge_block)
    out = []
    for c in list(tail.successors):
        if c.start_offset <= tail.start_offset:
            continue
        ins = list(getattr(c, 'instructions', None) or [])
        if ins and ins[0].opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):
            continue
        cl = last(c)
        fired = (len(ins) == 1 and cl is not None
                 and cl.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                 and isinstance(cl.argval, int)
                 and self.cfg.get_block_by_offset(cl.argval) is hdr)
        own = getattr(an, 'block_to_region', {}).get(c) if an else None
        out.append(dict(
            c=o(c), n=len(ins), term=(cl.opname if cl else None, cl.argval if cl else None),
            fired=fired, preds=sorted(o(x) for x in (c.predecessors or set())),
            merge=(region is not None and getattr(region, 'merge_block', None) is c),
            backedge=c in be, role=str(roles.get(id(c))),
            own='%s@%s' % (type(own).__name__, o(getattr(own, 'entry', None) or getattr(own, 'header_block', None))),
            in_arm_blocks=c in bl, in_region=rblocks and c in rblocks,
            in_gen=c in self.generated_blocks,
        ))
    if out:
        print('SITE %-4s %-34s arm=%s tail=%s(%s) hdr=%s' % (
            _state['tag'], cfgname, [o(x) for x in bl], o(tail),
            ll.opname, o(hdr)))
        for d in out:
            print('     %s' % d)
    return res


G._process_if_blocks = functools.wraps(M)(wrapped)

for rel, func, tag in TARGETS:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
    if not os.path.isfile(pyc):
        print('!! missing %s' % rel)
        continue
    _state['tag'] = tag
    _state['tail'] = func
    _state['n'] = 0
    import pycdc  # noqa: E402
    prod = pycdc.decompile_pyc(pyc)
    io.open(os.path.join(HERE, 'prod39h_%s.py' % func), 'w', encoding='utf-8').write(prod)
    print('### %s %s: %d if-arm returns inspected' % (tag, func, _state['n']))
