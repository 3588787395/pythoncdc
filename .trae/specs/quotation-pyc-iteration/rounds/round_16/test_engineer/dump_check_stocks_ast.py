"""R16: 转储 check_stocks 函数的 AST dict，查看 raise AssertionError 的 AST 结构。"""
import sys
import types
import marshal

sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# 找到 check_stocks 函数
target = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'check_stocks':
        target = c
        break

assert target is not None
cfg = build_cfg(target)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()

import json
# 只输出 body 中含 Raise 的部分
def find_raise(node, path=''):
    if isinstance(node, dict):
        if node.get('type') == 'Raise':
            print(f'FOUND Raise at {path}:')
            print(json.dumps(node, indent=2, default=str))
        for k, v in node.items():
            find_raise(v, path+'.'+k)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            find_raise(item, path+f'[{i}]')
find_raise(ast_dict)
