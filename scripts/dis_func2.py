import sys, dis, types, marshal

with open('site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_func(c, name):
    if c.co_name == name: return c
    for cc in c.co_consts:
        if isinstance(cc, types.CodeType):
            r = find_func(cc, name)
            if r: return r
    return None

func_code = find_func(code, '_sync_worker')
instrs = list(dis.get_instructions(func_code))
# Show instructions around offset 354-370 and around 700-710
for i, instr in enumerate(instrs):
    if instr.offset in range(340, 380) or instr.offset in range(694, 720) or instr.offset in range(540, 570):
        arg_str = str(instr.arg) if instr.arg is not None else ''
        argval_str = '(' + str(instr.argval) + ')' if instr.argval is not None else ''
        print(f'  [{i}] {instr.offset:4d} {instr.opname:30s} {arg_str:>5} {argval_str}')
