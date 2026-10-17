#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace region dispatch for one function (generate-only)."""
import io
import marshal
import os
import sys
import types
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 2
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

IND = ['', '  ', '    ', '      ', '        ', '          ']


def _tag(self):
    return None


def wrap_method(cls, mname, sig='region'):
    orig = getattr(cls, mname)

    def wrapper(self, *args, **kwargs):
        _reg = args[0] if args else None
        _d = getattr(self, '_r2_depth', 0)
        self._r2_depth = _d + 1
        _info = ''
        if _reg is not None and hasattr(_reg, 'entry'):
            _info = '%s@%s' % (type(_reg).__name__, getattr(_reg.entry, 'start_offset', None))
            if hasattr(_reg, 'merge_block'):
                _info += ' merge=@%s' % getattr(_reg.merge_block, 'start_offset', None)
        _b = None
        if _reg is not None and not hasattr(_reg, 'entry'):
            _b = _reg
            _info = 'block@%s' % getattr(_b, 'start_offset', None)
        def _real_caller():
            _st = traceback.extract_stack()
            for _f in reversed(_st[:-1]):
                if os.path.basename(_f.filename) not in ('_r2_disp.py',):
                    return _f
            return _st[-2]
        if mname == '_build_boolop_expression':
            _fr = _real_caller()
            _info += ' CALLER=%s:%d(%s)' % (
                os.path.basename(_fr.filename), _fr.lineno, _fr.name)
        if mname in ('_generate_block_statements', '_generate_stmts_from_instrs'):
            _fr = _real_caller()
            _info += ' CALLER=%s:%d(%s)' % (
                os.path.basename(_fr.filename), _fr.lineno, _fr.name)
        print('%s> %s(%s)' % (IND[min(_d, 5)], mname, _info))
        try:
            r = orig(self, *args, **kwargs)
        except Exception as e:
            print('%s! %s EXC %s' % (IND[min(_d, 5)], mname, e))
            self._r2_depth = _d
            raise
        _rt = None
        if r is None:
            _rt = 'None'
        elif isinstance(r, list):
            _rt = '[%s]' % ','.join(s.get('type', '?') for s in r if isinstance(s, dict))
        elif isinstance(r, dict):
            _rt = r.get('type', '?')
        else:
            _rt = type(r).__name__
        print('%s< %s -> %s' % (IND[min(_d, 5)], mname, _rt))
        if mname in ('_generate_boolop_impl', '_generate_boolop') and isinstance(r, list):
            import json as _json
            print('%s  JSON: %s' % (IND[min(_d, 5)],
                                    _json.dumps(r, ensure_ascii=False, default=str)[:3000]))
        self._r2_depth = _d
        return r
    setattr(cls, mname, wrapper)


for _m in ('_generate_region', '_generate_if', '_if_generate_normal',
           '_generate_boolop', '_generate_boolop_impl',
           '_generate_block_statements', '_generate_block_statements_body',
           '_generate_stmts_from_instrs', '_build_boolop_expression'):
    if hasattr(RegionASTGenerator, _m):
        wrap_method(RegionASTGenerator, _m)
    else:
        print('MISSING', _m)

out = gen.generate()
print('DONE', type(out))
