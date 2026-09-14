import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal, struct, types

f = open('site-packages/IQCommon/util/trade_info_utils.pyc', 'rb')
magic = f.read(4)
flags = struct.unpack('<I', f.read(4))[0]
if flags & 0x1:
    f.read(8)
else:
    f.read(4)
f.read(4)
code = marshal.load(f)
f.close()

gu = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'get_user_info':
        gu = c
        break

cfg = CFGBuilder().build(gu)
gen = RegionASTGenerator(cfg, parent_code=gu)

# Patch _generate_loop to trace else handling
orig_loop = gen._generate_loop.__func__
def debug_loop(self, region, *args, **kwargs):
    else_offsets = [b.start_offset for b in region.else_blocks] if region.else_blocks else []
    has_break = getattr(region, 'has_break', 'NOT SET')
    print(f'[_generate_loop] else_blocks={else_offsets}')
    print(f'[_generate_loop] has_break={has_break}')
    result = orig_loop(self, region, *args, **kwargs)
    if isinstance(result, dict) and result.get('type') == 'For':
        print(f'[_generate_loop] For has orelse: {"orelse" in result}')
    elif isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and r.get('type') == 'For':
                print(f'[_generate_loop] For has orelse: {"orelse" in r}')
    return result
gen._generate_loop = types.MethodType(debug_loop, gen)

result = gen.generate()
