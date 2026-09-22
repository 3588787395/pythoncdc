# -*- coding: utf-8 -*-
"""Round 39 line A, step 4: OWNERSHIP-layer probe (no core edit).

Wraps RegionAnalyzer.analyze from outside and, for the target function, dumps
  * every CFG block: start_offset, #instructions, terminator + target,
    block_to_region[blk] (the single owning region), block_roles[off]
  * the full region inventory with every role-specific block list
  * a decisive section: every block terminating in JUMP_BACKWARD, whether its
    target is a loop header, who owns it and with what BlockRole

usage: python -X utf8 probe_owner.py <src.py> <func-name>
"""
import dis
import functools
import importlib.util
import io
import os
import py_compile
import sys

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC = os.path.abspath(pos[0]) if pos else None
TAIL = pos[1] if len(pos) > 1 else ''
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(HERE)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion  # noqa: E402


def offs(bs):
    return sorted(getattr(b, 'start_offset', None) for b in (bs or [])
                  if b is not None)


def term(b):
    i = b.get_last_instruction() if hasattr(b, 'get_last_instruction') else None
    if i is None:
        return '-'
    return '%s->%s' % (i.opname, i.argval if isinstance(i.argval, int) else '-')


def desc(r):
    if r is None:
        return 'NONE'
    return '%s@%s' % (type(r).__name__,
                      getattr(getattr(r, 'entry', None), 'start_offset', None))


M = RegionAnalyzer.analyze
DONE = []


def wrapped(self, *a, **k):
    res = M(self, *a, **k)
    name = getattr(self.cfg, 'name', '?')
    if TAIL and TAIL not in name:
        return res
    if name in DONE:
        return res
    DONE.append(name)
    blks = getattr(self.cfg, 'blocks', None)
    blocks = list(blks.values()) if isinstance(blks, dict) else list(blks or [])
    print('\n================ CFG %s ================' % name)
    print('--- CFG blocks (%d) ---' % len(blocks))
    for b in sorted(blocks, key=lambda x: x.start_offset):
        role = self.block_roles.get(b.start_offset)
        print('  blk @%-4d n=%-3d term=%-32s owner=%-22s role=%s'
              % (b.start_offset, len(getattr(b, 'instructions', []) or []), term(b),
                 desc(self.block_to_region.get(b)),
                 role.name if role is not None else '-'))
    print('--- regions (%d) ---' % len(self.regions))
    for r in self.regions:
        print('  %-14s entry@%-4s parent=%-18s blocks=%s'
              % (type(r).__name__,
                 getattr(getattr(r, 'entry', None), 'start_offset', None),
                 desc(r.parent), offs(getattr(r, 'blocks', None))))
        if isinstance(r, IfRegion):
            for f in ('condition_block', 'merge_block'):
                print('        %-20s %s' % (f, offs([getattr(r, f, None)])))
            for f in ('then_blocks', 'else_blocks', 'elif_conditions',
                      'elif_final_else', 'chained_compare_blocks'):
                print('        %-20s %s' % (f, offs(getattr(r, f, None))))
            for i, bl in enumerate(getattr(r, 'elif_bodies', None) or []):
                print('        %-20s %s' % ('elif_bodies[%d]' % i, offs(bl)))
        if isinstance(r, LoopRegion):
            for f in ('header_block', 'condition_block', 'back_edge_block'):
                print('        %-20s %s' % (f, offs([getattr(r, f, None)])))
            for f in ('body_blocks', 'else_blocks', 'init_blocks', 'break_blocks',
                      'back_edge_blocks', 'pre_condition_blocks',
                      'condition_chain_blocks'):
                print('        %-20s %s' % (f, offs(getattr(r, f, None))))
            print('        %-20s %s' % ('children', [desc(c) for c in r.children]))
    hdrs = set()
    for r in self.regions:
        if isinstance(r, LoopRegion) and r.header_block is not None:
            hdrs.add(r.header_block.start_offset)
    print('--- blocks terminating in JUMP_BACKWARD ---')
    for b in sorted(blocks, key=lambda x: x.start_offset):
        i = b.get_last_instruction()
        if i is None or 'JUMP_BACKWARD' not in i.opname:
            continue
        t = i.argval if isinstance(i.argval, int) else None
        role = self.block_roles.get(b.start_offset)
        print('  @%-4s -> %-4s target_is_loop_header=%-5s owner=%-22s role=%-14s '
              'n=%d term=%s'
              % (b.start_offset, t, t in hdrs, desc(self.block_to_region.get(b)),
                 role.name if role is not None else '-',
                 len(getattr(b, 'instructions', []) or []), term(b)))
    return res


RegionAnalyzer.analyze = functools.wraps(M)(wrapped)

PYC = SRC if SRC.lower().endswith('.pyc') else os.path.join(HERE, 'probe_owner.pyc')
if PYC is not SRC:
    py_compile.compile(SRC, cfile=PYC, doraise=True, quiet=2)
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
import pycdc  # noqa: E402

o_map = r10._load_map(PYC)
print('--- ORIGINAL bytecode of target(s) ---')
for key, c in o_map.items():
    if not TAIL or key == TAIL or key.endswith('.' + TAIL):
        print('  [%s]' % key)
        dis.dis(c)
prod = pycdc.decompile_pyc(PYC)
PRODPY = os.path.join(HERE, 'probe_owner_prod.py')
io.open(PRODPY, 'w', encoding='utf-8').write(prod)
print('================ PRODUCT ================')
print(prod)
d_map = r10._compile_map(PRODPY)
for key in o_map:
    if key in d_map:
        print('strict %-24s %s' % (key, r10.strict_compare(o_map[key], d_map[key])))
