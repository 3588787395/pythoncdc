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

# cfg.blocks is a dict or list - let me check
print(type(cfg.blocks))
if isinstance(cfg.blocks, dict):
    for off, b in sorted(cfg.blocks.items()):
        if hasattr(b, 'instructions'):
            has_get_iter = any(i.opname == 'GET_ITER' for i in b.instructions)
            if has_get_iter:
                instrs = [(i.opname, i.offset, i.arg) for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                print(f'Block@{off}: {instrs}')
elif isinstance(cfg.blocks, list):
    for b in cfg.blocks:
        if hasattr(b, 'instructions'):
            has_get_iter = any(i.opname == 'GET_ITER' for i in b.instructions)
            if has_get_iter:
                instrs = [(i.opname, i.offset, i.arg) for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                print(f'Block@{b.start_offset}: {instrs}')
