# -*- coding: utf-8 -*-
"""探针：追踪 y1 的 Import 节点由哪个方法发出（只读 core/）。"""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../..'))

path = sys.argv[1]
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

def is_import(node):
    if isinstance(node, dict):
        if node.get('type') in ('Import', 'ImportFrom'):
            return True
        for v in node.values():
            if is_import(v):
                return True
    elif isinstance(node, list):
        return any(is_import(x) for x in node)
    return False

def wrap(name):
    orig = getattr(RegionASTGenerator, name, None)
    if orig is None:
        print('NO SUCH METHOD', name); return
    def wrapper(self, *a, **k):
        r = orig(self, *a, **k)
        if is_import(r):
            print('>>> %s -> %s' % (name, json.dumps(r, ensure_ascii=False, default=str)[:300]))
        return r
    setattr(RegionASTGenerator, name, wrapper)

for m in ['_process_instruction', '_extract_imports_from_block_prefix',
          '_build_store_statement', '_generate_stmts_from_instrs',
          '_generate_block_statements', '_generate_module', 'generate']:
    wrap(m)

module = load_pyc_file_v2(path)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
actual = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
cfg = build_cfg(actual)
gen = RegionASTGenerator(cfg, top_level_code=actual if actual.co_name == '<module>' else None)
ast_dict = gen.generate()
print('--- final ---')
print(json.dumps(ast_dict, ensure_ascii=False, default=str)[:800])