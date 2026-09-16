import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')
pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r
om = extract(orig)
co = om['growth_factors_sql_get']

from core.cfg import build_cfg
cfg = build_cfg(co)

# Find all blocks containing LOAD_FAST 'security' + GET_ITER
var_names = co.co_varnames
security_idx = var_names.index('security') if 'security' in var_names else None
print(f'var_names: {var_names}')
print(f'security index: {security_idx}')

# Now find blocks that load security and call GET_ITER
for off, b in sorted(cfg.blocks.items()):
    if not hasattr(b, 'instructions'):
        continue
    instrs = list(b.instructions)
    for i, instr in enumerate(instrs):
        if instr.opname == 'GET_ITER' and i > 0:
            prev = instrs[i-1]
            if prev.opname == 'LOAD_FAST' and prev.arg == security_idx:
                print(f'Block@{off}: LOAD_FAST security + GET_ITER at offsets {prev.offset}-{instr.offset}')
