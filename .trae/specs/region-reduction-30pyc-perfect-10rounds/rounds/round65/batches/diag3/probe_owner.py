# -*- coding: utf-8 -*-
"""probe_owner: who emits the merge_block tail for a standalone fstring ternary?

usage: python -X utf8 -B probe_owner.py <pyc> <funcname> [builddir]

In-memory monkeypatch (NO repo writes) of RegionASTGenerator:
  * _generate_ternary          -> region identity + caller + returned stmt kinds
  * _generate_block_statements -> which block, already_generated, stmt kinds
Pass builddir (e.g. F:/.../mirr_c1) to probe a candidate arm.
"""
import inspect
import io
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r'F:/Downloads/pythoncdc-main'
BUILD = sys.argv[3] if len(sys.argv) > 3 else REPO
sys.path.insert(0, BUILD)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(BUILD)

import importlib.util  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_G = _load(os.path.join(BUILD, 'core', 'cfg', 'region_ast_generator.py'), 'r65d3_po_g')
_RA = _load(os.path.join(BUILD, 'core', 'cfg', 'region_analyzer.py'), 'r65d3_po_ra')
CFGANALYZER_SRC = os.path.join(BUILD, 'core', 'cfg', 'cfg_analyzer.py')
_C = _load(CFGANALYZER_SRC, 'r65d3_po_cfg')
_IU = _load(os.path.join(BUILD, 'core', 'instruction_utils.py'), 'r65d3_po_iu')
G = _G.RegionASTGenerator


def load_pyc(path):
    data = io.open(path, 'rb').read()
    return marshal.loads(data[12:])


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def o(b):
    return getattr(b, 'start_offset', None)


def blofs(bs):
    return [o(x) for x in bs] if bs else bs


def kind(s):
    if not isinstance(s, dict):
        return type(s).__name__
    t = s.get('type')
    if t == 'Expr':
        v = s.get('value')
        return 'Expr(%s)' % (v.get('type') if isinstance(v, dict) else '?')
    if t == 'Assign':
        return 'Assign'
    return t


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]

    print('### BUILD=%s func=%s' % (BUILD, name))
    _gt = G._generate_ternary
    depth = {'n': 0}

    def gt(self, region, *a, **kw):
        pad = '  ' * depth['n']
        blocks = blofs(getattr(region, 'blocks', None))
        print('%s> T entry=%s blocks=%s merge=%s cond=%s ctx=%r container=%r '
              'merge_in_blocks=%s regions_owning_merge=%s'
              % (pad, o(region.entry), blocks, o(region.merge_block),
                 o(getattr(region, 'condition_block', None)),
                 getattr(region, 'merge_context', None),
                 getattr(region, 'container_type', None),
                 region.merge_block in (region.blocks or []),
                 [('%s@%s' % (type(r).__name__, o(getattr(r, 'entry', None))))
                  for r in self.regions
                  if r is not region and region.merge_block in (getattr(r, 'blocks', []) or [])]))
        fr = inspect.stack()[1:5]
        print('%s   callers: %s' % (pad, ' <- '.join(
            '%s@%s' % (f.function, f.lineno) for f in reversed(fr))))
        depth['n'] += 1
        try:
            r = _gt(self, region, *a, **kw)
        finally:
            depth['n'] -= 1
        print('%s< T -> [%s]' % (pad, ', '.join(kind(s) for s in (r or []))))
        return r

    G._generate_ternary = gt

    _gb = G._generate_block_statements

    def gb(self, block, *a, **kw):
        pad = '  ' * depth['n']
        r = _gb(self, block, *a, **kw)
        print('%s  # block_stmts@%s already_gen=%s -> [%s]'
              % (pad, o(block), block in self.generated_blocks,
                 ', '.join(kind(s) for s in (r or []))))
        return r

    G._generate_block_statements = gb

    cfg = _C.CFGAnalyzer().analyze(code)
    top = _RA.build_cfg(code) if hasattr(_RA, 'build_cfg') else cfg
    stmts = _G.generate_ast_from_regions(top, top_level_code=code)
    print('=== printed source (first 40 lines) ===')
    import core.code_generator as cgmod  # noqa: E402
    print(cgmod.CodeGenerator().generate(stmts)[:2200])


if __name__ == '__main__':
    main()
