"""R17 调试：最小复现 load_get_index_stocks 的 POP_TOP+RETURN_VALUE 合并 bug"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
import dis
import types


# 最小复现：elif 分支包含 (call+POP_TOP) + return X
SRC = '''
def f(x):
    data = []
    if isinstance(x, str):
        data = [x]
    elif isinstance(x, list):
        s = []
        for v in x:
            s.append(v)
        data = list(set(s))
        data.sort(key=s.index)
        return data
    return data
'''

# 编译为code object
code_obj = compile(SRC, '<test>', 'exec')

# 找到 f 函数的 code object
f_code = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'f':
        f_code = const
        break

print("=== f 的原始字节码 ===")
dis.dis(f_code)
print()

# 构建 CFG 并生成 AST
cfg = build_cfg(f_code)
gen = RegionASTGenerator(cfg, top_level_code=None)

# 启用详细调试
import logging
logging.basicConfig(level=logging.DEBUG)

ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print("=== 反编译结果 ===")
print(source)
print()

# 重新编译反编译结果，对比字节码
decompiled_code = compile(source, '<decompiled>', 'exec')
decompiled_f = None
for const in decompiled_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'f':
        decompiled_f = const
        break

print("=== 反编译后 f 的字节码 ===")
dis.dis(decompiled_f)
print()

# 对比
orig_instrs = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(f_code) if i.opname not in ('EXTENDED_ARG', 'CACHE')]
new_instrs = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(decompiled_f) if i.opname not in ('EXTENDED_ARG', 'CACHE')]
print(f"原指令数: {len(orig_instrs)}, 新指令数: {len(new_instrs)}")
print(f"匹配: {orig_instrs == new_instrs}")
if orig_instrs != new_instrs:
    for i, (o, n) in enumerate(zip(orig_instrs, new_instrs)):
        if o != n:
            print(f"  首个差异 at {i}: orig={o} vs new={n}")
            break
