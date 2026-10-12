"""Membership census (analyzer level) for one code object.

Counting rule (stated so 148 vs 186 style disagreements cannot recur):
  blocks    = number of BasicBlock objects in build_cfg(co).blocks (dict values or list)
  regions   = len(RegionAnalyzer(cfg).analyze() then .regions)  -- every region object declared
  two_owner = number of CFG blocks that occur in the `blocks` collection of >= 2 region objects
  zero_owner= number of CFG blocks that occur in the `blocks` of 0 region objects
  not_held  = number of region objects whose entry block is not in its own blocks list

usage: python -X utf8 work/membership.py <abs pyc> <co-name-exact>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)

PYC, WANT = sys.argv[1], sys.argv[2]

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


for co in walk(code):
    name = getattr(co, 'co_qualname', None) or co.co_name
    if name != WANT:
        continue
    cfg = build_cfg(co)
    blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    an = RegionAnalyzer(cfg)
    an.analyze()
    regions = list(an.regions)
    owner = {}
    for r in regions:
        for b in (getattr(r, 'blocks', None) or []):
            owner[id(b)] = owner.get(id(b), 0) + 1
    two = sum(1 for b in blocks if owner.get(id(b), 0) >= 2)
    zero = sum(1 for b in blocks if owner.get(id(b), 0) == 0)
    not_held = sum(1 for r in regions
                   if getattr(r, 'entry', None) is not None
                   and r.entry not in (getattr(r, 'blocks', None) or []))
    print('MEMBERSHIP %s :: blocks=%d regions=%d two_owner=%d zero_owner=%d not_held=%d'
          % (name, len(blocks), len(regions), two, zero, not_held))
