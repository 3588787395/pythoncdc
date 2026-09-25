# -*- coding: utf-8 -*-
"""diag1b: same as regdump.py but resolves core/ from an arbitrary mirror arm.

usage: python -X utf8 regarm.py <arm:landed|b1|head> <pyc> <funcname>
"""
import io
import marshal
import os
import sys
import types

REPO = r'F:/Downloads/pythoncdc-main'
ROOT = r'D:/Temp/opencode/r67gate/diag1'
arm, pyc, name = sys.argv[1], sys.argv[2], sys.argv[3]
core = REPO if arm == 'landed' else ROOT + '/mirr_' + arm
sys.path.insert(0, REPO)
sys.path.insert(0, core)
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(REPO)
import importlib
import core.cfg as _c
assert os.path.abspath(_c.__file__).replace('\\', '/').startswith(core.replace('\\', '/')), _c.__file__
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal %s' % path)


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def o(b):
    return getattr(b, 'start_offset', None)


def L(bs):
    if bs is None:
        return None
    try:
        return sorted(o(x) for x in bs)
    except TypeError:
        return bs


print('arm=%s core=%s' % (arm, os.path.dirname(_c.__file__)))
for c in [x for x in walk(load_pyc(pyc), []) if x.co_name == name]:
    cfg = build_cfg(c)
    gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
    regions = gen.region_analyzer.analyze()
    print('CFG %s: %d blocks, %d regions' % (c.co_name, len(cfg.blocks), len(regions)))
    for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        if 'Ternary' not in type(r).__name__:
            continue
        print('%s@%s blocks=%s cond=%s tv=%s fv=%s merge=%s vt=%r mc=%r' % (
            type(r).__name__, o(r.entry), L(getattr(r, 'blocks', None)),
            o(getattr(r, 'condition_block', None)),
            L(getattr(r, 'true_value_block', None)), L(getattr(r, 'false_value_block', None)),
            o(getattr(r, 'merge_block', None)), getattr(r, 'value_target', None),
            getattr(r, 'merge_context', None)))
