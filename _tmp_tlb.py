import sys, dis, marshal

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

from pycdc import decompile_pyc

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_trade\trade_live_broker.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_trade\trade_live_broker.pyc')
decomp_code = compile(source, '<decompiled>', 'exec')

def find_method(code, cls_name, method_name):
    for c in code.co_consts:
        if hasattr(c, 'co_name') and c.co_name == cls_name:
            for m in c.co_consts:
                if hasattr(m, 'co_name') and m.co_name == method_name:
                    return m
    return None

orig_method = find_method(orig_code, 'TradeLiveBroker', '_trade_status_handle')
decomp_method = find_method(decomp_code, 'TradeLiveBroker', '_trade_status_handle')

orig_instrs = list(dis.get_instructions(orig_method))
decomp_instrs = list(dis.get_instructions(decomp_method))

print(f"Orig len: {len(orig_instrs)}, Decomp len: {len(decomp_instrs)}")
print()
print("=== Orig first 15 ===")
for k in range(min(15, len(orig_instrs))):
    oi = orig_instrs[k]
    print(f"  {k:3d}: {oi.opname} {oi.argval if oi.argval is not None else ''}"[:100])
print()
print("=== Decomp first 15 ===")
for k in range(min(15, len(decomp_instrs))):
    di = decomp_instrs[k]
    print(f"  {k:3d}: {di.opname} {di.argval if di.argval is not None else ''}"[:100])
