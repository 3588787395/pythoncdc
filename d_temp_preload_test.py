import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator
import marshal, types

with open('site-packages/IQCommon/util/replace_utils.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = code.co_consts[21]

builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg)
gen.cfg = cfg
gen.regions = regions

# Find target region
for r in regions:
    if hasattr(r, 'container_type'):
        if hasattr(r, 'entry') and hasattr(r.entry, 'offset'):
            entry_off = r.entry.offset
        else:
            entry_off = r.entry
        if entry_off != 292:
            continue
        
        preload = gen._compute_ternary_cond_preload_exprs(r)
        sys.stdout.write('preload_exprs = %s\n' % str(preload)[:500])
        sys.stdout.flush()
