"""Trace api_get_financial B10 handler processing with debug"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import core.cfg.region_ast_generator as rag_mod

PYC = '/workspace/quotation.pyc'


# Monkey-patch _generate_handler_body_statements to trace B10
orig_method = rag_mod.RegionASTGenerator._generate_handler_body_statements

def traced_method(self, block):
    if block.start_offset == 456:
        print(f"\n[TRACE] _generate_handler_body_statements called for B{block.id} (off {block.start_offset})")
        print(f"  _try_depth={self._try_depth}")
        print(f"  _loop_depth={self._loop_depth}")
        print(f"  block succs: {[s.id for s in block.successors]}")
        result = orig_method(self, block)
        print(f"  result: {result}")
        return result
    return orig_method(self, block)

rag_mod.RegionASTGenerator._generate_handler_body_statements = traced_method


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    def walk(co):
        nonlocal target
        if co.co_name == 'api_get_financial':
            target = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                walk(const)
    walk(code_obj)

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    gen = rag_mod.RegionASTGenerator(cfg, analyzer)
    result = gen.generate()
    print("\n[done]")


if __name__ == '__main__':
    main()
