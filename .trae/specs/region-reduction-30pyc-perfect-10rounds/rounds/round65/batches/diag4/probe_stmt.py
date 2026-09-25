# -*- coding: utf-8 -*-
"""probe_stmt: while decompiling ONE function with the LIVE landed core, record every
generator method that returns an AST node dict whose printed form matches a regex,
together with the creating method + call stack.  Repo is read-only.

usage: python -X utf8 probe_stmt.py <pyc> <funcname> <regex>
"""
import io
import marshal
import os
import re
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('bad pyc')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


import traceback
import json

pat = re.compile(sys.argv[3])
seen = set()
_orig_exceptionhook = None


def _report(node_repr, depth_hint=''):
    stack = [f for f in traceback.extract_stack()
             if 'region_ast_generator' in f.filename or 'region_analyzer' in f.filename]
    key = tuple('%s:%s:%s' % (os.path.basename(f.filename), f.lineno, f.name) for f in stack[-8:])
    if key in seen:
        return
    seen.add(key)
    print('MATCH %s' % node_repr[:150])
    for f in stack[-9:]:
        print('     at %s:%d %s' % (os.path.basename(f.filename), f.lineno, f.name))


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator

    FN = os.path.join('core', 'cfg', 'region_ast_generator.py').replace('\\', '/')
    LINE = 0

    def trace(frame, event, arg):
        if frame.f_code.co_filename.replace('\\', '/') != FN:
            return None
        if event != 'return':
            return trace
        rv = arg
        if rv is None:
            return trace
        try:
            s = json.dumps(rv, ensure_ascii=False, default=str)[:4000]
        except Exception:
            return trace
        if pat.search(s):
            _report(s[:200])
        return trace

    sys.settrace(trace)
    try:
        cfg = build_cfg(code)
        gen = RegionASTGenerator(cfg)
        ast = gen.generate()
    finally:
        sys.settrace(None)
    print('distinct creating sites:', len(seen))


if __name__ == '__main__':
    main()
