"""Debug: trace the actual code path for get_open_orders comprehension"""
import sys, os, dis, types, marshal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load the pyc
pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Find the TradeLiveBroker class
def find_code(code, name):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            result = find_code(c, name)
            if result:
                return result
    return None

broker_code = find_code(orig_code, 'TradeLiveBroker')
if broker_code:
    print("Found TradeLiveBroker class")
    # Find get_open_orders
    goo_code = find_code(broker_code, 'get_open_orders')
    if goo_code:
        print(f"\nFound get_open_orders code object")
        print(f"co_consts: {[c.co_name if isinstance(c, types.CodeType) else c for c in goo_code.co_consts]}")
        
        # Show all instructions
        print(f"\nAll instructions:")
        for i, inst in enumerate(dis.get_instructions(goo_code)):
            print(f"  {i:3d} offset={inst.offset:4d} {inst.opname:30s} arg={inst.arg} argval={inst.argval}")
        
        # Check the listcomp code object
        for c in goo_code.co_consts:
            if isinstance(c, types.CodeType) and c.co_name == '<listcomp>':
                print(f"\n<listcomp> code object:")
                print(f"  co_varnames: {c.co_varnames}")
                print(f"  co_freevars: {c.co_freevars}")
                print(f"  Instructions:")
                for i, inst in enumerate(dis.get_instructions(c)):
                    print(f"    {i:3d} {inst.opname:30s} arg={inst.arg} argval={inst.argval}")
    else:
        print("get_open_orders NOT FOUND")
else:
    print("TradeLiveBroker NOT FOUND")
