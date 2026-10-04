# -*- coding: utf-8 -*-
"""FIX-A 调试辅助：跟踪 TernaryRegion 生成期属性与发射路径。"""
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
    from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, BoolOpRegion
    from core.cfg.region_ast_generator import RegionASTGenerator
    import core.cfg.region_ast_generator as rag

    _orig_gen = RegionASTGenerator._generate_ternary

    def patched(self, region, skip_store_targets=None):
        res = _orig_gen(self, region, skip_store_targets)
        print('[TRACE] _generate_ternary entry=%s merge=%s is_augassign=%s op=%s kind=%s value_target=%r -> %s' % (
            region.entry.start_offset,
            region.merge_block.start_offset if region.merge_block else None,
            getattr(region, 'is_augassign', None), getattr(region, 'augassign_op', None),
            getattr(region, 'augassign_target_kind', None),
            getattr(region, 'value_target', None),
            repr(res)[:200]))
        return res

    RegionASTGenerator._generate_ternary = patched

    if hasattr(RegionASTGenerator, '_generate_boolop'):
        _orig_bop = RegionASTGenerator._generate_boolop

        def patched_bop(self, region, *a, **k):
            res = _orig_bop(self, region, *a, **k)
            print('[TRACE] _generate_boolop entry=%s merge=%s is_augassign=%s op=%s kind=%s value_target=%r -> %s' % (
                region.entry.start_offset,
                region.merge_block.start_offset if region.merge_block else None,
                getattr(region, 'is_augassign', None), getattr(region, 'augassign_op', None),
                getattr(region, 'augassign_target_kind', None),
                getattr(region, 'value_target', None),
                repr(res)[:300]))
            return res

        RegionASTGenerator._generate_boolop = patched_bop

    _orig_gr = RegionASTGenerator._generate_region

    def patched_gr(self, region, *a, **k):
        res = _orig_gr(self, region, *a, **k)
        if isinstance(region, BoolOpRegion):
            print('[TRACE] _generate_region BoolOp entry=%s blocks=%s -> %s' % (
                region.entry.start_offset,
                sorted(b.start_offset for b in region.blocks),
                repr(res)[:200]))
        return res

    RegionASTGenerator._generate_region = patched_gr

    # also patch the analyzer attach to confirm attach happens on the same object
    _orig_attach = RegionAnalyzer._b48_attach_ternary_augassign

    def patched_attach(self, region):
        _orig_attach(self, region)
        print('[TRACE] _b48_attach entry=%s merge=%s -> is_augassign=%s op=%s' % (
            region.entry.start_offset,
            region.merge_block.start_offset if region.merge_block else None,
            getattr(region, 'is_augassign', None), getattr(region, 'augassign_op', None)))

    RegionAnalyzer._b48_attach_ternary_augassign = patched_attach

    for name in names:
        if name == '<module>':
            c = code_obj
        else:
            c = get_code(code_obj, name)
        if c is None:
            print(f'!! code object not found: {name}')
            continue
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg)

        class _LoggingSet(set):
            def add(self, item):
                import traceback
                st = traceback.extract_stack()
                caller = st[-3] if len(st) >= 3 else None
                tag = f'{caller.filename.split(chr(92))[-1]}:{caller.lineno}' if caller else '?'
                if getattr(item, 'start_offset', None) is not None:
                    print('[GB+] block %s <- %s (%s)' % (item.start_offset, tag, caller.name))
                else:
                    print('[GB+] %r <- %s (%s)' % (item, tag, caller.name))
                super().add(item)

        gen.generated_blocks = _LoggingSet(gen.generated_blocks)

        import builtins
        _orig_print = print
        def _exc_hook(tp, val, tb):
            _orig_print('[EXC]', tp.__name__, val)
        sys.excepthook = _exc_hook

        import traceback as _tb
        _orig_bei = RegionASTGenerator._generate_boolop_impl

        def patched_bei(self2, region2, *a2, **k2):
            try:
                return _orig_bei(self2, region2, *a2, **k2)
            except Exception as e:
                _orig_print('[EXC-boolop_impl]', type(e).__name__, e)
                _tb.print_exc()
                raise

        RegionASTGenerator._generate_boolop_impl = patched_bei
        ast_dict = gen.generate()
        print('=' * 30, name)
        import json
        print(json.dumps(ast_dict, ensure_ascii=False, default=str)[:1500])


if __name__ == '__main__':
    main()
