#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dis one function from a pyc. usage: _r2_dis.py <pyc> <name>"""
import dis
import io
import marshal
import sys
import types

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(sys.argv[1], 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, sys.argv[2], targets)
dis.dis(targets[-1])
