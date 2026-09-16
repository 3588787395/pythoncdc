import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
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

# Find Block 6
for blk in cfg.blocks:
    if hasattr(blk, 'offset') and blk.offset == 400:
        sys.stdout.write('Block at offset 400:\n')
        for i in blk.instructions:
            sys.stdout.write('  %s %s %s\n' % (i.offset, i.opname, i.arg))
        break

sys.stdout.flush()
