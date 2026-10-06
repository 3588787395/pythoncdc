# -*- coding: utf-8 -*-
"""探针：直接跑 region 管线并打印 ast_dict（只读 core/，只写 stdout）。
用法: python test_repros/round5/r5fix_dump_ast.py <pyc>
"""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../..'))

def main(path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    import types as _types
    module = load_pyc_file_v2(path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    actual = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
    cfg = build_cfg(actual)
    gen = RegionASTGenerator(cfg, top_level_code=actual if actual.co_name == '<module>' else None)
    ast_dict = gen.generate()
    print(json.dumps(ast_dict, ensure_ascii=False, indent=1, default=str))

main(sys.argv[1])