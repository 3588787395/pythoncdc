"""R17 调试：追踪 return data.sort(...) 的生成路径"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole


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
f_code = codes['load_get_index_stocks']

cfg = build_cfg(f_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

# 检查 Block 6 (offset 280) 的 effective_instructions
_blocks = list(cfg.blocks.values()) if hasattr(cfg.blocks, 'values') else list(cfg.blocks)
for blk in _blocks:
    if blk.start_offset == 280:
        print(f"=== Block at offset 280 ===")
        print(f"  role: {ra.get_block_role(blk)}")
        eff = ra.effective_instructions.get(blk.start_offset)
        print(f"  effective_instructions: {eff}")
        if eff:
            for i in eff:
                print(f"    {i.offset:4d} {i.opname:25s} {i.argval!r}")
        print()

# 现在给 _generate_return_ast 打补丁，追踪调用
import core.cfg.region_ast_generator as rag_module
orig_generate_return_ast = rag_module.RegionASTGenerator._generate_return_ast

def traced_generate_return_ast(self, block, return_instr=None):
    if block.start_offset == 280:
        print(f"\n!!! _generate_return_ast called for Block 280 !!!")
        print(f"  return_instr: {return_instr}")
        if return_instr:
            print(f"  return_instr.opname: {return_instr.opname}")
        import traceback
        traceback.print_stack()
    return orig_generate_return_ast(self, block, return_instr)

rag_module.RegionASTGenerator._generate_return_ast = traced_generate_return_ast

# 也追踪 _build_statements_from_instructions
orig_build = rag_module.RegionASTGenerator._build_statements_from_instructions

def traced_build(self, instrs, block=None):
    if block is not None and block.start_offset == 280:
        print(f"\n!!! _build_statements_from_instructions called for Block 280 !!!")
        print(f"  instrs count: {len(instrs)}")
        for i in instrs:
            print(f"    {i.offset:4d} {i.opname:25s} {i.argval!r}")
    return orig_build(self, instrs, block)

rag_module.RegionASTGenerator._build_statements_from_instructions = traced_build

# 追踪 _generate_block_statements
orig_gbs = rag_module.RegionASTGenerator._generate_block_statements

def traced_gbs(self, block, _cjb_parent=None):
    if block.start_offset == 280:
        print(f"\n!!! _generate_block_statements called for Block 280 !!!")
    result = orig_gbs(self, block, _cjb_parent)
    if block.start_offset == 280:
        print(f"\n!!! _generate_block_statements for Block 280 returned: {result}")
    return result

rag_module.RegionASTGenerator._generate_block_statements = traced_gbs

print("\n=== 生成 AST ===")
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
print("\n=== AST 生成完成 ===")
