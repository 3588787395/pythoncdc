#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 判据级 diff：用 pylingual 内部机制逐函数对比 原 pyc vs regen 产物（先编译 OK.py 为 pyc）。
用法: python _r3_bcdiff.py <orig.pyc> <regen.py> [qualname-substr]
输出：每函数 CFG是否等价 / 异常表 diff / 指令流首个分歧点（含前后指令上下文）。
"""
import os
import py_compile
import sys
import tempfile
import types

PYL = r'D:\Desktop\ptrade相关\pylingual'
sys.path.insert(0, PYL)
import typing as _typing
if not hasattr(_typing, 'override'):
    _typing.override = lambda func: func
if 'pydot' not in sys.modules:
    stub = types.ModuleType('pydot')
    stub.graph_from_dot_data = lambda *a, **k: []
    stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
    sys.modules['pydot'] = stub
if 'pylingual' not in sys.modules:
    pkg = types.ModuleType('pylingual')
    pkg.__path__ = [os.path.join(PYL, 'pylingual')]
    sys.modules['pylingual'] = pkg

from pylingual.editable_bytecode import PYCFile  # noqa: E402
from pylingual.editable_bytecode.bytecode_patches import (  # noqa: E402
    remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, replace_firstlno)
from pylingual.equivalence_check import matching_iter, is_control_flow_equivalent, compare_instruction  # noqa: E402

PATCHES = [remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, remove_extended_arg, replace_firstlno]


def load(p, is_source=False):
    if is_source:
        tmp = tempfile.mkdtemp()
        pyc = os.path.join(tmp, 'x.pyc')
        py_compile.compile(p, cfile=pyc, doraise=True)
        b = PYCFile(pyc)
    else:
        b = PYCFile(p)
    b.apply_patches(PATCHES)
    return b


def inst_line(inst):
    arg = ''
    try:
        if inst.has_arg:
            arg = ' arg=%r' % (inst.argval,)
    except Exception:
        pass
    tgt = ''
    if getattr(inst, 'is_jump_target', False):
        tgt = ' <<TARGET'
    return '%5s %-32s%s%s' % (inst.offset, inst.opname, arg, tgt)


def main():
    orig = load(sys.argv[1])
    regen = load(sys.argv[2], is_source=True)
    subs = sys.argv[3:]
    for bc_a, bc_b in matching_iter(orig, regen):
        if bc_a is None:
            print('=== EXTRA in regen:', bc_b.name)
            continue
        if bc_b is None:
            print('=== MISSING in regen:', bc_a.name)
            continue
        if subs and not any(s in bc_a.name for s in subs):
            continue
        name = bc_a.name
        cfg_a = __import__('pylingual.equivalence_check', fromlist=['x']).bytecode_to_control_flow_graph(bc_a)
        from pylingual.equivalence_check import bytecode_to_control_flow_graph
        from pylingual.control_flow_reconstruction.cfg import CFG
        g_a = CFG.from_graph(bytecode_to_control_flow_graph(bc_a), bc_a, iterate=False)
        g_b = CFG.from_graph(bytecode_to_control_flow_graph(bc_b), bc_b, iterate=False)
        flow_eq = is_control_flow_equivalent(g_a, g_b)
        et_a = bc_a.named_exception_table
        et_b = bc_b.named_exception_table
        print('=' * 100)
        print('QUALNAME:', name, '| CFG_EQ:', flow_eq, '| ET_EQ:', et_a == et_b)
        if et_a != et_b:
            print('--- ET orig ---')
            for e in et_a:
                print('   ', e)
            print('--- ET regen ---')
            for e in et_b:
                print('   ', e)
        la, lb = list(bc_a), list(bc_b)
        if len(la) != len(lb):
            print('--- instruction count differs: orig=%d regen=%d' % (len(la), len(lb)))
        for i in range(max(len(la), len(lb))):
            ia = la[i] if i < len(la) else None
            ib = lb[i] if i < len(lb) else None
            same = ia is not None and ib is not None and compare_instruction(ia, ib)
            mark = ' ' if same else '***'
            print('%s %s | %s' % (mark, inst_line(ia) if ia else '---', inst_line(ib) if ib else '---'))
            if not same:
                # 上下文各 6 条后停止：打印后续 12 条对照
                print('    ...ctx...')
                for j in range(i + 1, min(i + 13, max(len(la), len(lb)))):
                    ja = la[j] if j < len(la) else None
                    jb = lb[j] if j < len(lb) else None
                    print('    %s | %s' % (inst_line(ja) if ja else '---', inst_line(jb) if jb else '---'))
                break


if __name__ == '__main__':
    main()
