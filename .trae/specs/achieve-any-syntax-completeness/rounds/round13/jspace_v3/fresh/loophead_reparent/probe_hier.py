import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, TryExceptRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

_orig = RegionAnalyzer._build_region_hierarchy
TRACE = []
def patched(self, regions):
    res = _orig(self, regions)
    for r in regions:
        tn = type(r).__name__
        if tn == 'Region':
            continue
        par = r.parent
        TRACE.append('%-16s entry=%-4s -> parent=%s' % (
            tn, r.entry.start_offset,
            par.entry.start_offset if par is not None else None))
    TRACE.append('---')
    return res
RegionAnalyzer._build_region_hierarchy = patched

# trace candidates inside the original by wrapping the sorted loop: simpler—
# instrument via a manual re-run of the selection for the interesting child.
module = load_pyc_file_v2('F:/Downloads/pythoncdc-main/.trae/specs/attack-completeness-claims/rounds/round6/offcorpus/stdlib_xml_ElementPath.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
def find_code(code, acc):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            acc.append(c); find_code(c, acc)
acc = []
find_code(root, acc)
fn = [c for c in acc if c.co_name == 'iterfind'][0]
cfg = build_cfg(fn)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
print('\n'.join(TRACE))
print()
# ranges of the interesting regions
ana = gen.region_analyzer if hasattr(gen, 'region_analyzer') else None
if ana is None:
    # RegionASTGenerator holds analyzer differently
    ana = getattr(gen, 'analyzer', None)
print('analyzer found:', ana is not None)
if ana is not None:
    for r in ana.regions:
        tn = type(r).__name__
        if tn in ('TryExceptRegion', 'LoopRegion'):
            rng = ana._get_region_offset_range(r)
            print('%-16s entry=%-4s range=%s blocks=%s' % (
                tn, r.entry.start_offset, rng,
                [b.start_offset for b in r.blocks][:10]))
