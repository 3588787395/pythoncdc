#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace chained-compare cache/build calls for one function."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)


class TD(dict):
    def __setitem__(self, k, v):
        _t = v.get('type') if isinstance(v, dict) else type(v).__name__
        print('CACHE WRITE key=%s type=%s' % (k, _t))
        super().__setitem__(k, v)

    def get(self, k, d=None):
        r = super().get(k, d)
        print('CACHE GET key=%s -> %s' % (k, 'HIT' if r is not None else 'MISS'))
        return r


gen._chain_compare_expr_cache = TD()

_orig = gen._build_chained_compare_from_region_data


def _wrap(region):
    r = _orig(region)
    ent = getattr(region, 'entry', None)
    off = getattr(ent, 'start_offset', None)
    _t = r.get('type') if isinstance(r, dict) else repr(r)
    print('BUILD_CC entry=%s -> %s' % (off, _t))
    import traceback as _tb
    for fr in _tb.extract_stack()[:-1]:
        if 'region_ast_generator.py' in fr.filename:
            print('   at %s:%s %s' % (os.path.basename(fr.filename), fr.lineno,
                                      fr.name))
    return r


gen._build_chained_compare_from_region_data = _wrap

_orig_genregion = gen._generate_region


def _wrap_genregion(region):
    try:
        r = _orig_genregion(region)
    except Exception:
        import traceback as _tb2
        print('GEN_REGION %s entry=%s EXCEPTION:' % (
            type(region).__name__,
            getattr(getattr(region, 'entry', None), 'start_offset', None)))
        _tb2.print_exc()
        raise
    _rt = type(region).__name__
    _ent = getattr(getattr(region, 'entry', None), 'start_offset', None)
    if isinstance(r, list):
        _k = [it.get('type') if isinstance(it, dict) else type(it).__name__
              for it in r]
    else:
        _k = r.get('type') if isinstance(r, dict) else repr(r)
    print('GEN_REGION %s entry=%s -> %s' % (_rt, _ent, _k))
    return r


gen._generate_region = _wrap_genregion

_orig_ternary = gen._generate_ternary


def _wrap_tern(region, skip_store_targets=None):
    r = _orig_ternary(region, skip_store_targets)
    ent = getattr(getattr(region, 'entry', None), 'start_offset', None)
    if isinstance(r, list):
        _kinds = [it.get('type') if isinstance(it, dict) else type(it).__name__
                  for it in r]
    else:
        _kinds = r.get('type') if isinstance(r, dict) else repr(r)
    print('GEN_TERNARY entry=%s -> %s' % (ent, _kinds))
    return r


gen._generate_ternary = _wrap_tern

_orig_boolop_cc = gen._try_build_chained_compare_in_boolop


def _wrap2(chain_block, region):
    r = _orig_boolop_cc(chain_block, region)
    off = getattr(chain_block, 'start_offset', None)
    _t = r.get('type') if isinstance(r, dict) else repr(r)
    print('CC_IN_BOOLOP block=%s -> %s' % (off, _t))
    return r


gen._try_build_chained_compare_in_boolop = _wrap2

out = gen.generate()
print('---- GENERATED BLOCKS ----')
print(sorted(b.start_offset for b in gen.generated_blocks))
