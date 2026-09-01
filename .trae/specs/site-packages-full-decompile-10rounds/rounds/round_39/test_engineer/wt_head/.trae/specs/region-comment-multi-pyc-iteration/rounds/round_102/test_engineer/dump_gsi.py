#!/usr/bin/env python3
"""Dump full instruction list of orig get_stock_info for repro reconstruction."""
import dis
import marshal
import sys
import types
from pathlib import Path

MAIN = Path(r'F:\Downloads\pythoncdc-main')


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


oc = extract(load_code(str(MAIN / 'site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc')))['get_stock_info']
for i, x in enumerate(dis.get_instructions(oc)):
    print(f'{i:4d} {x.opname:36s} {x.argrepr}')
