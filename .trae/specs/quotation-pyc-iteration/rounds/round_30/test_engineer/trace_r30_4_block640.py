"""R30-4 trace: why block 640 (return None) is placed outside IfRegion@520"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_co(co, name):
    if co.co_name == name: return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_co(c, name)
            if r: return r
    return None

co = find_co(code_obj, 'get_stock_exrights')
cfg = CFGBuilder().build(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

gen = RegionASTGenerator(cfg, analyzer)

# Find IfRegion@520
target_region = None
for r in analyzer.regions:
    if r.entry and r.entry.start_offset == 520 and type(r).__name__ == 'IfRegion':
        target_region = r
        break

print(f"Target: IfRegion@520")
print(f"  then_blocks={[b.start_offset for b in target_region.then_blocks]}")
print(f"  else_blocks={target_region.else_blocks}")
print(f"  merge_block={target_region.merge_block}")

# Check block 640 region ownership
b640 = cfg.offset_to_block[640]
print(f"\nBlock 640:")
gr = analyzer.get_region_for_block(b640)
print(f"  get_region_for_block(640) = {type(gr).__name__}@{gr.entry.start_offset if gr and gr.entry else None}")
er = analyzer.get_entry_region_for_block(b640)
print(f"  get_entry_region_for_block(640) = {type(er).__name__}@{er.entry.start_offset if er and er.entry else None}")

# Patch _process_if_blocks to trace
orig_process = gen._process_if_blocks
def traced_process(blocks, region, branch='then'):
    if region is target_region and branch == 'then':
        print(f"\n[_process_if_blocks] IfRegion@520 branch=then")
        print(f"  blocks={[b.start_offset for b in blocks]}")
        _block_set = set(blocks)
        for b in sorted(_block_set, key=lambda x: x.start_offset):
            _nr = gen.region_analyzer.get_region_for_block(b)
            _nr_name = type(_nr).__name__ if _nr else None
            _nr_entry = _nr.entry.start_offset if _nr and _nr.entry else None
            _is_region = _nr is region
            print(f"  block@{b.start_offset}: region={_nr_name}@{_nr_entry}, is_self={_is_region}")

    result = orig_process(blocks, region, branch)

    if region is target_region and branch == 'then':
        print(f"\n[_process_if_blocks] RESULT for IfRegion@520 then:")
        for i, s in enumerate(result):
            t = s.get('type') if isinstance(s, dict) else type(s).__name__
            print(f"  stmt[{i}]: type={t}")
            if t == 'If':
                body_types = [bs.get('type') if isinstance(bs, dict) else type(bs).__name__ for bs in s.get('body', [])]
                print(f"    body={body_types}")

    return result

gen._process_if_blocks = traced_process

ast = gen.generate()
