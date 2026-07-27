"""R17 调试：直接从 quotation.pyc 提取 load_get_index_stocks 并测试"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(code_obj)
    return result


codes = load_pyc_code_objects(PYC)
fn_name = 'load_get_index_stocks'
f_code = codes[fn_name]

print(f"=== {fn_name} 原始字节码 (最后 30 条) ===")
instrs = list(dis.get_instructions(f_code))
for ins in instrs[-30:]:
    print(f"  L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")
print()

print(f"=== {fn_name} co_consts ===")
for c in f_code.co_consts:
    print(f"  {type(c).__name__}: {c!r}")
print()

# 构建 CFG 并生成 AST
print(f"=== 构建 CFG ===")
cfg = build_cfg(f_code)
print(f"CFG 块数: {len(cfg.blocks)}")

# 列出所有块及其指令
_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for i, blk in enumerate(_blocks):
    last_instr = blk.instructions[-1] if blk.instructions else None
    first_instr = blk.instructions[0] if blk.instructions else None
    print(f"  Block {i} (offset {blk.start_offset}): {len(blk.instructions)} instrs, "
          f"first={first_instr.opname if first_instr else 'None'}@L{first_instr.starts_line if first_instr else '-'}, "
          f"last={last_instr.opname if last_instr else 'None'}@L{last_instr.starts_line if last_instr else '-'}")
    # 显示块内所有指令的行号
    if i in (6, 7):
        for ins in blk.instructions:
            print(f"    L{str(ins.starts_line or '-'):>3} {ins.offset:4d} {ins.opname:25s} {ins.argval!r}")

print()
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print(f"=== 反编译结果 ===")
print(source)
print()

decompiled_code = compile(source, '<decompiled>', 'exec')
decompiled_f = None
for const in decompiled_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == fn_name:
        decompiled_f = const
        break

print(f"=== 反编译后字节码 (最后 30 条) ===")
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
            # 输出附近指令
            lo = max(0, i - 5)
            hi = min(len(orig_instrs), i + 5)
            print(f"  orig[{lo}:{hi}]:")
            for j in range(lo, hi):
                m = '>>' if j == i else '  '
                print(f"    {m} [{j}] {orig_instrs[j]}")
            print(f"  new[{lo}:{hi}]:")
            for j in range(lo, hi):
                m = '>>' if j == i else '  '
                print(f"    {m} [{j}] {new_instrs[j]}")
            break
