"""R16: 测试 ExpressionReconstructor 对 LOAD_ASSERTION_ERROR+LOAD_CONST+PRECALL+CALL 的处理。"""
import sys
import types
import marshal

sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_generator_v2 import ExpressionReconstructor

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

# 找到含 LOAD_ASSERTION_ERROR 的块
blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for b in blocks:
    if any(i.opname == 'LOAD_ASSERTION_ERROR' for i in b.instructions):
        print(f'Block {b.id}:')
        for i in b.instructions:
            _arg = getattr(i, 'argval', getattr(i, 'arg', None))
            print(f'  {getattr(i, "offset", "?"):>4} {i.opname:<30s} {_arg}')
        print()
        # 提取 RAISE_VARARGS 之前的指令
        pre_instrs = []
        for i in b.instructions:
            if i.opname == 'RAISE_VARARGS':
                break
            pre_instrs.append(i)
        print(f'pre_instrs ({len(pre_instrs)}):')
        for i in pre_instrs:
            _arg = getattr(i, 'argval', getattr(i, 'arg', None))
            print(f'  {getattr(i, "offset", "?"):>4} {i.opname:<30s} {_arg}')
        print()
        # 重建 - 用新的 _reconstruct_raise_exc 方法
        result = gen._reconstruct_raise_exc(pre_instrs)
        import json
        print('reconstruct result (via _reconstruct_raise_exc):')
        print(json.dumps(result, indent=2, default=str))
        break
