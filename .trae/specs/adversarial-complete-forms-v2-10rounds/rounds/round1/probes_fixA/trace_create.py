# -*- coding: utf-8 -*-
"""FIX-A 调试辅助：跟踪 _detect_ternary_pattern / _create_ternary_region_from_pattern 的创建顺序与嵌套吸收。

用法：python trace_create.py <pyc路径> <函数名> [函数名...]
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
    from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, IfRegion, BoolOpRegion
    from core.cfg.region_ast_generator import RegionASTGenerator

    def rn(r):
        if r is None:
            return 'None'
        t = type(r).__name__
        return '%s@%s' % (t, getattr(r, 'entry', None) is not None and r.entry.start_offset)

    for name in names:
        c = get_code(code_obj, name)
        if c is None:
            print('!! not found', name)
            continue
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg)
        ra = gen.region_analyzer
        print('=' * 30, name)
        print('block order:', [b.start_offset for b in cfg.get_blocks_in_order()])
        for b in cfg.get_blocks_in_order():
            li = b.get_last_instruction()
            print('  blk@%s: %s | succs=%s' % (
                b.start_offset,
                ' '.join('%s@%s' % (i.opname, i.argval if isinstance(i.argval, int) else '') for i in b.instructions),
                sorted(s.start_offset for s in b.successors)))
        orig_create = getattr(ra, '_create_ternary_region_from_pattern', None)

        def wrapped(pattern, _orig=orig_create, _ra=ra):
            tb = pattern['true_block']
            fb = pattern['false_block']
            print('TRY entry=%s true=%s(reg=%s) false=%s(reg=%s)' % (
                pattern['block'].start_offset, tb.start_offset, rn(_ra.block_to_region.get(tb)),
                fb.start_offset, rn(_ra.block_to_region.get(fb))))
            r = _orig(pattern)
            if r is not None:
                print('  OK blocks=%s' % sorted(b.start_offset for b in r.blocks))
            else:
                print('  REJECTED')
            return r

        if orig_create is not None:
            ra._create_ternary_region_from_pattern = wrapped
        else:
            print('(note: _create_ternary_region_from_pattern not yet bound; skip wrap)')
        ra.analyze()
        print('---- final regions:')
        for r in ra.regions:
            mc = getattr(r, 'merge_context', None)
            mb = getattr(r, 'merge_block', None)
            print('  ', rn(r), 'blocks=', sorted(b.start_offset for b in r.blocks),
                  'merge=', (mb.start_offset if mb is not None else None), 'merge_context=', mc)
        print('---- block_to_region:')
        for b, r in sorted(ra.block_to_region.items(), key=lambda kv: kv[0].start_offset):
            print('   blk@%s -> %s' % (b.start_offset, rn(r)))


if __name__ == '__main__':
    main()
