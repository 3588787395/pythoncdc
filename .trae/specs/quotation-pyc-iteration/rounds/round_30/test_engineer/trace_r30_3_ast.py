"""R30-3 调试：跟踪 IfRegion@342 和 IfRegion@384 的 AST 生成"""
import sys
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/core')
from cfg.cfg_builder import build_cfg
from cfg.region_analyzer import RegionAnalyzer, IfRegion
from cfg.region_ast_generator import RegionASTGenerator
import marshal, struct

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(4); flags = struct.unpack('<I', f.read(4))[0]
    f.read(8); code = marshal.load(f)

def find_code(co, name):
    if co.co_name == name: return co
    for const in co.co_consts:
        if hasattr(const, 'co_name'):
            r = find_code(const, name)
            if r: return r
    return None

target = find_code(code, 'get_stock_exrights')
cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegions at 342 and 384
r342 = None
r384 = None
for r in analyzer.regions:
    if isinstance(r, IfRegion):
        if r.entry and r.entry.start_offset == 342:
            r342 = r
        elif r.entry and r.entry.start_offset == 384:
            r384 = r

def show(name, r):
    if not r:
        print(f"{name}: None")
        return
    print(f"=== {name} ===")
    print(f"  type={type(r).__name__}")
    print(f"  blocks={[b.start_offset for b in r.blocks]}")
    print(f"  then={[b.start_offset for b in r.then_blocks] if r.then_blocks else None}")
    _e = getattr(r, 'else_blocks', None)
    print(f"  else={[b.start_offset for b in _e] if _e else None}")
    _m = getattr(r, 'merge_block', None)
    print(f"  merge={_m.start_offset if _m else None}")
    print(f"  parent={type(r.parent).__name__ if r.parent else None}")
    print(f"  children={[type(c).__name__+':'+str(c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")

show("IfRegion@342", r342)
show("IfRegion@384", r384)

# Find IfRegion@0 and show its children
r0 = None
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        r0 = r
        break
if r0:
    show("IfRegion@0", r0)
    print(f"  Is IfRegion@342 a child of IfRegion@0? {r342 in (r0.children or [])}")
    print(f"  Is IfRegion@384 a child of IfRegion@0? {r384 in (r0.children or [])}")

# Check block_to_region
print("\n=== block_to_region ===")
for offset in [342, 384, 484, 516, 520]:
    b = cfg.get_block_by_offset(offset)
    r = analyzer.block_to_region.get(b)
    print(f"  Block@{offset} -> {type(r).__name__}@{r.entry.start_offset if r and r.entry else None}")

# Now generate AST with tracing
print("\n=== Generating AST ===")
gen = RegionASTGenerator(cfg, analyzer)

# Monkey-patch _generate_if to trace
orig_generate_if = gen._generate_if
def traced_generate_if(region):
    if region.entry and region.entry.start_offset in (0, 342, 384, 520):
        print(f"\n[_generate_if] called for IfRegion@{region.entry.start_offset}")
        print(f"  region_type={region.region_type}")
        print(f"  entry in generated_blocks: {region.entry in gen.generated_blocks}")
        if region.entry.start_offset == 342:
            # Check what generated block 342
            import traceback
            print(f"  generated_blocks offsets near 342: {[b.start_offset for b in gen.generated_blocks if 300 <= b.start_offset <= 600]}")
    result = orig_generate_if(region)
    if region.entry and region.entry.start_offset in (0, 342, 384, 520):
        if isinstance(result, list):
            print(f"  -> returned list of {len(result)} items: {[s.get('type') if isinstance(s, dict) else s for s in result]}")
        elif isinstance(result, dict):
            print(f"  -> returned dict: type={result.get('type')}")
        else:
            print(f"  -> returned: {result}")
    return result
gen._generate_if = traced_generate_if

# Monkey-patch _generate_region to trace
orig_generate_region = gen._generate_region
def traced_generate_region(region, skip_store_targets=None):
    if hasattr(region, 'entry') and region.entry and region.entry.start_offset in (342, 384, 520):
        print(f"\n[_generate_region] called for {type(region).__name__}@{region.entry.start_offset}")
        print(f"  entry in generated_blocks: {region.entry in gen.generated_blocks}")
    return orig_generate_region(region, skip_store_targets)
gen._generate_region = traced_generate_region

# Monkey-patch _process_if_blocks to trace
orig_process = gen._process_if_blocks
def traced_process(blocks, region, branch='then'):
    if region and hasattr(region, 'entry') and region.entry and region.entry.start_offset in (0, 342):
        _offsets = [b.start_offset for b in blocks]
        if 342 in _offsets or 384 in _offsets:
            print(f"\n[_process_if_blocks] region@{region.entry.start_offset} branch={branch} blocks={_offsets}")
    result = orig_process(blocks, region, branch)
    if region and hasattr(region, 'entry') and region.entry and region.entry.start_offset in (0, 342):
        _offsets = [b.start_offset for b in blocks]
        if 342 in _offsets or 384 in _offsets:
            if isinstance(result, list):
                print(f"  -> {len(result)} stmts: {[s.get('type') if isinstance(s, dict) else s for s in result]}")
    return result
gen._process_if_blocks = traced_process

ast = gen.generate()
