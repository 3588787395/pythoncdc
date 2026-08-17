import marshal, types, sys, io
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

f = open('site-packages/IQEngine/core/asset.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

def find_code(co, name):
    if hasattr(co, 'co_name') and co.co_name == name:
        return co
    for c in getattr(co, 'co_consts', []):
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r: return r
    return None

code = find_code(code, 'check_time')
print(f"Found: {code.co_name}")

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg)
# Force region analysis
gen.regions = gen.region_analyzer.analyze()
print(f"Regions: {len(gen.regions)}")
for r in gen.regions:
    rt = type(r).__name__
    e = r.entry.start_offset if r.entry else None
    parts = [f'{rt}', f'entry={e}']
    if hasattr(r,'op_chain') and r.op_chain:
        parts.append(f'op_chain={[(b.start_offset,op) for b,op in r.op_chain]}')
    if hasattr(r,'condition_block') and r.condition_block:
        parts.append(f'cond={r.condition_block.start_offset}')
    if hasattr(r,'then_blocks'):
        parts.append(f'then={[b.start_offset for b in r.then_blocks]}')
    if hasattr(r,'else_blocks'):
        parts.append(f'else={[b.start_offset for b in r.else_blocks]}')
    if hasattr(r,'merge_block') and r.merge_block:
        parts.append(f'merge={r.merge_block.start_offset}')
    if hasattr(r,'body_blocks'):
        parts.append(f'body={[b.start_offset for b in r.body_blocks]}')
    if hasattr(r,'header_block') and r.header_block:
        parts.append(f'header={r.header_block.start_offset}')
    print(' '.join(parts))

# Now try to generate
ast_dict = gen.generate()
print(f"\nAST dict type: {type(ast_dict)}")
if isinstance(ast_dict, dict):
    print(f"Keys: {list(ast_dict.keys())}")
    # Try to convert and generate
    converter = CFGASTConverter()
    py_ast = converter.convert(ast_dict)
    code_gen = CFGCodeGenerator()
    source = code_gen.generate(py_ast)
    print(f"\n=== Generated source ===")
    print(source)
