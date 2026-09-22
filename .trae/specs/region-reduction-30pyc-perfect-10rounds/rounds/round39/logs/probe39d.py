# -*- coding: utf-8 -*-
"""Round 39 line A, step 3: at the R100 suppression decision, print the loop-region facts that
could discriminate 'this arm tail IS the loop body end' (legit Mode B) from
'this arm tail is one of several physical back edges' (our defect).

Wraps _process_if_blocks from outside (no core edit) and, for each call whose branch block list
contains a pure/terminal JUMP_BACKWARD block, prints the LoopRegion attribute inventory, the
IfRegion roles, and which block(s) in the loop jump to the header.

usage: python -X utf8 probe39d.py <src.py> <func-name>
"""
import functools
import inspect
import io
import os
import py_compile
import sys
from pprint import pformat

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC = os.path.abspath(pos[0]) if pos else None
TAIL = pos[1] if len(pos) > 1 else ''
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(HERE)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402
import pycdc  # noqa: E402

M = G._process_if_blocks
WORK = []
LOOP_DONE = []


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


def last(b):
    i = b.get_last_instruction() if hasattr(b, 'get_last_instruction') else None
    return (i.opname, i.argval if isinstance(getattr(i, 'argval', None), int) else None) if i else None


def wrapped(self, *args, **k):
    blocks, region = (list(args[0]) if args and args[0] else []), None
    for cand in list(args[1:]) + list(k.values()):
        if cand is not None and hasattr(cand, 'then_blocks'):
            region = cand
            break
    if region is None:
        return M(self, *args, **k)
    bl = blocks
    tgt = [b for b in bl if (last(b) or ('', None))[0] in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
    if tgt:
        loop = getattr(self, '_current_loop', None)
        rec = {'branch_blocks': offs(bl), 'tail_jump_blocks': [(offs([b])[0], last(b)) for b in tgt],
               'region_type': type(region).__name__, 'region_entry': offs([getattr(region, 'entry', None)]),
               'then': offs(getattr(region, 'then_blocks', None)),
               'else': offs(getattr(region, 'else_blocks', None)),
               'merge': offs([getattr(region, 'merge_block', None)]),
               'loop_type': type(loop).__name__ if loop else None}
        if loop is not None:
            rec['loop_entry'] = offs([getattr(loop, 'entry', None)])
            rec['loop_header'] = offs([getattr(loop, 'header_block', None)])
            rec['loop_attrs'] = sorted(k2 for k2 in dir(loop) if not k2.startswith('__'))
            rec['loop_merge_is_header'] = (getattr(loop, 'header_block', None)
                                           is getattr(region, 'merge_block', None))
            hdr = getattr(loop, 'header_block', None)
            back = []
            for b in (getattr(self, 'cfg', None) and getattr(self.cfg, 'blocks', None) or []):
                op, t = last(b) or ('', None)
                if op in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') and hdr is not None \
                        and t == getattr(hdr, 'start_offset', -1):
                    back.append((b.start_offset, len([i for i in b.instructions
                                                     if i.opname not in ('RESUME', 'NOP', 'CACHE')]),
                                 offs(sorted(getattr(b, 'predecessors', None) or [],
                                             key=lambda p: p.start_offset)),
                                 'in_this_branch' if b in bl else ''))
            rec['blocks_jumping_to_header'] = back
            WORK.append(rec)
    out = M(self, *args, **k)
    if tgt:
        LOOP_DONE.append({'branch': offs(bl), 'emitted_has_continue':
                          'Continue' in pformat(out, width=200)})
    return out


G._process_if_blocks = functools.wraps(M)(wrapped)

work = os.path.join(HERE, 'probe39d_work')
os.makedirs(work, exist_ok=True)
orig_pyc = os.path.join(work, 'orig.pyc')
py_compile.compile(SRC, cfile=orig_pyc, doraise=True, quiet=2)
prod = pycdc.decompile_pyc(orig_pyc)
print('=== %d R100-candidate branch calls ===' % len(WORK))
for r in WORK:
    print(pformat(r, width=120))
    print()
print('=== emission ===')
for r in LOOP_DONE:
    print(r)
print(prod)
