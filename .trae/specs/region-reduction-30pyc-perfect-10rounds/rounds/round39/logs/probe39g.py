# -*- coding: utf-8 -*-
"""Round 39 line A, step 7: why did R39-A not fire?  Evaluate the candidate
predicate term-by-term at every _process_if_blocks return, for the target CFG.

usage: python -X utf8 probe39g.py <src-or-pyc> <func-name>
"""
import functools
import importlib.util
import os
import py_compile
import sys

pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC = os.path.abspath(pos[0]) if pos else None
TAIL = pos[1] if len(pos) > 1 else ''
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(HERE)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402

M = G._process_if_blocks
HIT = {'n': 0}


def o(b):
    return getattr(b, 'start_offset', None)


def last(b):
    i = b.get_last_instruction() if b is not None else None
    return i


def wrapped(self, blocks, region=None, *a, **k):
    res = M(self, blocks, region, *a, **k)
    cfgname = getattr(getattr(self, 'cfg', None), 'name', '?')
    if TAIL and TAIL not in cfgname:
        return res
    HIT['n'] += 1
    loop = getattr(self, '_current_loop', None)
    hdr = getattr(loop, 'header_block', None) if loop else None
    bl = list(blocks or [])
    tail = None
    for b in reversed(bl):
        if b in self.generated_blocks:
            tail = b
            break
    terms = None
    if tail is None:
        terms = {'arm': '%s/%s' % ([o(x) for x in bl], getattr(region, 'region_type', None)),
                 'note': 'no block of this arm is in generated_blocks yet',
                 'generated_of_arm': sorted(o(x) for x in bl if x in self.generated_blocks)}
    if tail is not None:
        su = list(getattr(tail, 'successors', []) or [])
        t = su[0] if len(su) == 1 else None
        tl = last(t)
        ll = last(tail)
        rblocks = set(getattr(region, 'blocks', None) or [])
        be = set(getattr(loop, 'back_edge_blocks', None) or [])
        if loop is not None and getattr(loop, 'back_edge_block', None) is not None:
            be.add(loop.back_edge_block)
        terms = {
            'arm': '%s/%s' % ([o(x) for x in bl], getattr(region, 'region_type', None)),
            'region_is_None': region is None,
            'stmts': len(res),
            'ends_cont': bool(res and isinstance(res[-1], dict) and res[-1].get('type') == 'Continue'),
            'tail_blk': o(tail),
            'tail_term': ll.opname if ll else None,
            'n_succ': len(su),
            'T': o(t) if t else None,
            'T_term': (tl.opname if tl else None, tl.argval if tl else None),
            'T_n_instr': len(list(getattr(t, 'instructions', []) or [])) if t else None,
            'T_is_hdr': (t is not None and tl is not None and isinstance(tl.argval, int)
                         and self.cfg.get_block_by_offset(tl.argval) is hdr),
            'cur_loop': o(hdr),
            'T_in_generated': (t in self.generated_blocks) if t else None,
            'T_in_blocks': (t in bl) if t else None,
            'T_in_region_blocks': (t in rblocks) if t else None,
            'T_is_back_edge': (t in be) if t else None,
            'T_pred': sorted(o(x) for x in (getattr(t, 'predecessors', set()) or [])) if t else None,
            'all_succ': sorted(o(x) for x in su),
        }
    if terms is not None:
        print('EVAL ' + repr(terms))
    return res


G._process_if_blocks = functools.wraps(M)(wrapped)

PYC = SRC if SRC.lower().endswith('.pyc') else os.path.join(HERE, 'probe39g.pyc')
if PYC is not SRC:
    py_compile.compile(SRC, cfile=PYC, doraise=True, quiet=2)
import pycdc  # noqa: E402
pycdc.decompile_pyc(PYC)
print('### _process_if_blocks returns seen: %d' % HIT['n'])
