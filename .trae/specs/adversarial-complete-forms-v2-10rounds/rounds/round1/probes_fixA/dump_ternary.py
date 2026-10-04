# -*- coding: utf-8 -*-
"""FIX-A 调试辅助：对目标 pyc 的指定函数单元 dump TernaryRegion / BoolOpRegion 关键属性。

用法：python dump_ternary.py <pyc路径> <函数名> [函数名...]
仅打印区域分析结果，不修改任何文件；放置于 probes_fixA/ 属本轮工作产物。
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
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.region_analyzer import (
        TernaryRegion, BoolOpRegion, IfRegion, LoopRegion, TryExceptRegion,
        MatchRegion, AssertRegion, WithRegion,
    )

    for name in names:
        c = get_code(code_obj, name)
        if c is None:
            print(f'!! code object not found: {name}')
            continue
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg)
        gen.region_analyzer.analyze()
        print('=' * 30, name)
        for r in gen.region_analyzer.regions:
            tn = type(r).__name__
            info = [f'{tn} type={getattr(r, "region_type", None)}',
                    f'entry={getattr(r, "entry", None) and getattr(r, "entry").start_offset}',
                    f'merge={getattr(r, "merge_block", None) and r.merge_block.start_offset}']
            print('  ', ' '.join(info))
            if isinstance(r, TernaryRegion):
                merge = getattr(r, 'merge_block', None)
                mi = None
                if merge is not None:
                    mi = [(i.offset, i.opname, i.arg) for i in merge.instructions[:8]]
                print('      ternary: is_augassign=%s op=%s target_kind=%s merge_instrs=%s' % (
                    getattr(r, 'is_augassign', None), getattr(r, 'augassign_op', None),
                    getattr(r, 'augassign_target_kind', None), mi))
                tb = r.true_value_block
                fb = r.false_value_block
                print('      arms: true=%s false=%s value_target=%s' % (
                    tb and tb.start_offset, fb and fb.start_offset,
                    getattr(r, 'value_target', None) and getattr(r.value_target, 'start_offset', None)))
            if isinstance(r, BoolOpRegion):
                print('      boolop: blocks=%s' % sorted(b.start_offset for b in r.blocks))


if __name__ == '__main__':
    main()
