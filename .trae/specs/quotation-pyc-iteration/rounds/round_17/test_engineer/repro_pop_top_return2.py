"""R17 调试：更接近 load_get_index_stocks 的最小复现"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
import dis
import types


# 更接近实际函数 - 含 chained call (data_proxy().get_x(stock, date))
SRC = '''
def load_get_index_stocks(stocks, date=None):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_index_stocks_local(stocks, date)
    elif isinstance(stocks, list):
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_index_stocks_local(stock, date))
        data = list(set(stockslist))
        data.sort(key=stockslist.index)
        return data
    return data
'''

code_obj = compile(SRC, '<test>', 'exec')

f_code = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'load_get_index_stocks':
        f_code = const
        break

print("=== 原始字节码 (最后 30 条) ===")
instrs = list(dis.get_instructions(f_code))
for ins in instrs[-30:]:
    print(f"  {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")
print()

cfg = build_cfg(f_code)
print(f"=== CFG 块数: {len(cfg.blocks)} ===")
_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for i, blk in enumerate(_blocks):
    last_instr = blk.instructions[-1] if blk.instructions else None
    print(f"  Block {i} (offset {blk.start_offset}): {len(blk.instructions)} instrs, last={last_instr.opname if last_instr else 'None'}")
print()
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print("=== 反编译结果 ===")
print(source)
print()

decompiled_code = compile(source, '<decompiled>', 'exec')
decompiled_f = None
for const in decompiled_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'load_get_index_stocks':
        decompiled_f = const
        break

print("=== 反编译后字节码 (最后 30 条) ===")
new_instrs_list = list(dis.get_instructions(decompiled_f))
for ins in new_instrs_list[-30:]:
    print(f"  {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")
print()

orig_instrs = [(i.offset, i.opname, i.argval) for i in instrs if i.opname not in ('EXTENDED_ARG', 'CACHE')]
new_instrs = [(i.offset, i.opname, i.argval) for i in new_instrs_list if i.opname not in ('EXTENDED_ARG', 'CACHE')]
print(f"原指令数: {len(orig_instrs)}, 新指令数: {len(new_instrs)}")
print(f"匹配: {orig_instrs == new_instrs}")
if orig_instrs != new_instrs:
    for i, (o, n) in enumerate(zip(orig_instrs, new_instrs)):
        if o != n:
            print(f"  首个差异 at {i}: orig={o} vs new={n}")
            break
