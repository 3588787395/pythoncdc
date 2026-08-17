import marshal, types, dis, sys
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

f = open('site-packages/IQEngine/core/asset.pyc', 'rb')
f.read(16)
code = marshal.load(f)

def find_code(code_obj, name):
    if hasattr(code_obj, 'co_name') and code_obj.co_name == name:
        return code_obj
    for const in getattr(code_obj, 'co_consts', []):
        if isinstance(const, types.CodeType):
            result = find_code(const, name)
            if result is not None:
                return result
    return None

code = find_code(code, 'check_time')
print(f"Found: {code.co_name}")
cfg = build_cfg(code)

print(f"\ncfg.blocks type: {type(cfg.blocks)}")
if isinstance(cfg.blocks, dict):
    blocks = list(cfg.blocks.values())
elif isinstance(cfg.blocks, list):
    blocks = cfg.blocks
else:
    blocks = list(cfg.blocks)
print(f"Block count: {len(blocks)}")
print(f"Block[0] type: {type(blocks[0])}")

# Try different attribute names
b0 = blocks[0]
print(f"Block[0] attrs: {[a for a in dir(b0) if not a.startswith('_')]}")
