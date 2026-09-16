import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator
import marshal, types

with open('site-packages/IQCommon/util/replace_utils.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'decrypt_database_url':
        func_code = const
        break

builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the target region
for r in regions:
    if hasattr(r, 'container_type'):
        if hasattr(r, 'entry') and hasattr(r.entry, 'offset'):
            entry_off = r.entry.offset
        else:
            entry_off = r.entry
        if entry_off != 292:
            continue
        
        # Check _ternary_cond_start_offset
        offset = getattr(r, '_ternary_cond_start_offset', None)
        sys.stdout.write('_ternary_cond_start_offset=%s\n' % offset)
        
        # Try compute preload
        gen = RegionASTGenerator(cfg)
        gen.cfg = cfg
        gen.regions = regions
        
        preload = gen._compute_ternary_cond_preload_exprs(r)
        sys.stdout.write('preload_exprs=%s\n' % preload)
        sys.stdout.flush()
