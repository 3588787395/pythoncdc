# -*- coding: utf-8 -*-
"""FIX-A 调试辅助：dump TryExceptRegion 的 try/handler/finally 块划分。

用法：python dump_try.py <pyc路径> <函数名> [函数名...]
仅打印，不修改任何文件；放置于 probes_fixA/ 属本轮工作产物。
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..')))

from core.pyc_loader_v2 import load_pyc_file_v2  # noqa: E402


def get_code(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            found = get_code(c, name)
            if found is not None:
                return found
    return None


def offs(blocks):
    return sorted(b.start_offset for b in blocks)


def main():
    pyc = sys.argv[1]
    names = sys.argv[2:]
    module = load_pyc_file_v2(pyc)
    code_obj = module.code
    if hasattr(code_obj, 'get'):
        code_obj = code_obj.get()
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.region_analyzer import TryExceptRegion, TernaryRegion

    for name in names:
        c = get_code(code_obj, name)
        if c is None:
            print('!! not found', name)
            continue
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg)
        gen.region_analyzer.analyze()
        print('=' * 30, name)
        print('exception table:', getattr(cfg, 'exception_table', None))
        for r in gen.region_analyzer.regions:
            if isinstance(r, TernaryRegion):
                p = getattr(r, 'parent', None)
                print('TernaryRegion@%s parent=%s blocks=%s' % (
                    r.entry.start_offset if r.entry else None,
                    ('%s@%s' % (type(p).__name__, p.entry.start_offset)) if p is not None else None,
                    offs(r.blocks)))
        for r in gen.region_analyzer.regions:
            if not isinstance(r, TryExceptRegion):
                continue
            print('TryExceptRegion@%s entry=%s' % (
                r.entry.start_offset if r.entry else None,
                r.entry.start_offset if r.entry else None))
            ch = [('%s@%s' % (type(x).__name__, x.entry.start_offset if x.entry else None))
                  for x in (getattr(r, 'children', None) or [])]
            print('  children=', ch)
            print('  try_blocks=', offs(r.try_blocks))


if __name__ == '__main__':
    main()
