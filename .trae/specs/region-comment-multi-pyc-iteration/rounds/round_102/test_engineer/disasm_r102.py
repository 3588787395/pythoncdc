#!/usr/bin/env python3
"""R102 提名目标反汇编诊断：orig pyc vs 再生成 OK.py 的首差区域对比."""
import dis
import marshal
import sys
import types
from pathlib import Path

MAIN = Path(r'F:\Downloads\pythoncdc-main')
sys.path.insert(0, str(MAIN))

CASES = [
    ('site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc',
     'get_stock_info', range(40, 62)),
    ('site-packages/IQEngine/plugins/plugin_system_accounts/account_model/stock_account.pyc',
     'update_account', range(48, 66)),
    ('site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc',
     'make_trade', range(252, 272)),
]


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract(code):
    out = {}

    def walk(c):
        out[c.co_name or '<module>'] = c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                walk(k)
    walk(code)
    return out


def instrs(co):
    return list(dis.get_instructions(co))


def show(tag, ins, rng):
    print(f'  [{tag}]')
    for i in rng:
        if i >= len(ins):
            break
        x = ins[i]
        arg = x.argrepr
        print(f'    {i:4d} {x.opname:34s} {arg}')


for rel, fname, rng in CASES:
    pyc = MAIN / rel
    okpy = Path(str(pyc.with_suffix('')) + 'OK.py')
    print(f'===== {fname}  ({rel.split("/")[-1]}) =====')
    oc = extract(load_code(str(pyc)))[fname]
    import py_compile
    cfile = py_compile.compile(str(okpy), doraise=True, quiet=2)
    dc = extract(load_code(cfile))[fname]
    oi, di = instrs(oc), instrs(dc)
    print(f'  orig={len(oi)} instrs, decomp={len(di)} instrs')
    show('ORIG', oi, rng)
    show('DECOMP', di, rng)
    print()
