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

for r in regions:
    if hasattr(r, 'container_type'):
        mc = getattr(r, 'merge_context', None)
        fci = getattr(r, 'func_call_info', None)
        vt = getattr(r, 'value_target', None)
        ct = getattr(r, 'container_type', None)
        print('TernaryRegion entry=%s blocks=%s container_type=%s merge_context=%s func_call_info=%s value_target=%s' % (r.entry, r.blocks, ct, mc, fci, vt))
        if r.entry == 292:
            print('  merge_block=%s' % r.merge_block)
            if r.merge_block:
                print('  merge_block instructions:')
                for i in r.merge_block.instructions:
                    if i.opname not in ('RESUME', 'NOP', 'CACHE'):
                        print('    %s %s %s %s' % (i.offset, i.opname, i.arg, i.argval))
