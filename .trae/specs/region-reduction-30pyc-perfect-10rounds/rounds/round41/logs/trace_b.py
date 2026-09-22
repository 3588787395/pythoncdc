"""Read-only trace: who calls _generate_block_statements for the escaping blocks.

Loads the landed core (REPO on sys.path) and monkeypatches methods in memory only.
No file in the repo is written or edited.
"""
import io
import json
import os
import sys

sys.path.insert(0, r'D:/Temp/r41gate')
import r41g  # noqa: E402

PYC = sys.argv[1] if len(sys.argv) > 1 else r'F:/Downloads/pythoncdc-main/site-packages/fly/data/quote.pyc'
WATCH = set(int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['1818', '1864', '1760', '1814']))

pycdc = r41g._load_arm('landed')
from core.cfg import region_ast_generator as RAG  # noqa: E402

G = RAG.RegionASTGenerator
events = []
stack = []


def frame_chain():
    out = []
    f = sys._getframe(2)
    while f is not None and len(out) < 24:
        co = f.f_code
        if 'region_ast_generator' in os.path.basename(co.co_filename):
            out.append(co.co_name + ':' + str(f.f_lineno))
        f = f.f_back
    return out[::-1]


orig_bs = G._generate_block_statements


def bs(self, block, _cjb_parent=None):
    off = getattr(block, 'start_offset', None)
    top = len(stack) and stack[-1]
    if off in WATCH:
        events.append({'ev': 'bs', 'off': off, 'depth': len(stack),
                       'chain': frame_chain()})
    return orig_bs(self, block, _cjb_parent)


G._generate_block_statements = bs

orig_rg = G._generate_region


def rg(self, region, skip_store_targets=None):
    t = type(region).__name__
    entry = getattr(region, 'entry', None)
    eo = getattr(entry, 'start_offset', None) if entry is not None else None
    stack.append(t + '@' + str(eo))
    try:
        r = orig_rg(self, region, skip_store_targets)
    finally:
        stack.pop()
    return r


G._generate_region = rg

orig_pib = G._process_if_blocks


def pib(self, blocks, region, branch='then', *a, **k):
    t = type(region).__name__
    entry = getattr(region, 'entry', None)
    events.append({'ev': 'pib', 'branch': branch, 'region': t,
                   'entry': getattr(entry, 'start_offset', None),
                   'nblocks': len(blocks), 'region_blocks': sorted(
                       [b.start_offset for b in getattr(region, 'blocks', [])])[:40],
                   'merge': getattr(getattr(region, 'merge_block', None), 'start_offset', None),
                   'loop_hdr': getattr(getattr(region, 'loop_header_block', None), 'start_offset', None),
                   'back': getattr(getattr(region, 'back_edge_block', None), 'start_offset', None),
                   'chain': list(stack)})
    return orig_pib(self, blocks, region, branch, *a, **k)


G._process_if_blocks = pib

text = pycdc.decompile_pyc(PYC)
io.open(r'D:/Temp/r41gate/trace_b_prod.py', 'w', encoding='utf-8').write(text)
io.open(r'D:/Temp/r41gate/trace_b_out.txt', 'w', encoding='utf-8').write(
    '\n'.join(json.dumps(e, ensure_ascii=False) for e in events))
print('events', len(events))
for e in events:
    if e.get('ev') == 'bs':
        print('BS', e['off'], 'depth', e['depth'], ' | '.join(e['chain'][-6:]))
