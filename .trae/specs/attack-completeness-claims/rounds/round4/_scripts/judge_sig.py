#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**判据可见性指纹**（judge-visible signature）。

目的：区分两类「漏检」——
  * HARD_MISS   ：判据**看得到**差异（字节码级、类型敏感）却仍判绿 ⇒ 判据比较算子/归一化有洞；
  * STRUCTURAL  ：判据**看不到**差异（差异落在 co_varnames / 注解 / docstring / NOP / 行号 等
                  未被比较的维度，或差异根本不在指令流里）⇒ 结构性不可见（不可由判据改进单独解决）。

实现：完全复用**附件判据本体**的装载与归一化
      （`pylingual.editable_bytecode.PYCFile` + 与 `compare_pyc` 完全相同的 patch 序列
        remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, remove_extended_arg,
        replace_firstlno
       + `CFG.from_graph(..., iterate=False)`），
      唯一差别：**argval 用类型敏感标签比较**（`1` vs `True` vs `1.0` 可分辨），
      而附件本体用 Python `==`（`1 == True` ⇒ 不可分辨）。

⇒ 若本模块判「可见」而附件判 Equal，则附件的比较算子是**可改进**的；
   若本模块判「不可见」，则须新增**判据维度**（不是改比较算子）。

用法：
  python -X utf8 judge_sig.py <pyc_a> <pyc_b>      # 打印 A/B 指纹是否一致 + 首个差异
"""
from __future__ import annotations

import os
import sys
import types

DEFAULT_PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'


def load_sig(root: str = DEFAULT_PYLINGUAL):
    root = os.path.abspath(root)
    sys.path.insert(0, root)
    import typing
    if not hasattr(typing, 'override'):
        typing.override = lambda f: f
    if 'pydot' not in sys.modules:
        stub = types.ModuleType('pydot')
        stub.graph_from_dot_data = lambda *a, **k: []
        stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
        sys.modules['pydot'] = stub
    if 'pylingual' not in sys.modules:
        pkg = types.ModuleType('pylingual')
        pkg.__path__ = [os.path.join(root, 'pylingual')]
        sys.modules['pylingual'] = pkg
    from pylingual.editable_bytecode import PYCFile
    from pylingual.editable_bytecode.bytecode_patches import (
        fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop, replace_firstlno)
    from pylingual.control_flow_reconstruction.cfg import CFG
    from pylingual.editable_bytecode.control_flow_graph import bytecode_to_control_flow_graph

    patches = [remove_extended_arg, remove_nop, fix_indirect_jump,
               fix_unreachable, remove_extended_arg, replace_firstlno]

    def tag(v):
        if isinstance(v, bool):
            return ('bool', v)
        if isinstance(v, int):
            return ('int', v)
        if isinstance(v, float):
            return ('float', repr(v))
        if isinstance(v, complex):
            return ('complex', repr(v))
        if isinstance(v, str):
            return ('str', v)
        if isinstance(v, bytes):
            return ('bytes', v)
        if v is None:
            return ('none',)
        if isinstance(v, tuple):
            return ('tuple', tuple(tag(x) for x in v))
        if isinstance(v, frozenset):
            return ('frozenset', tuple(sorted(repr(tag(x)) for x in v)))
        return (type(v).__name__, repr(v))

    def inst_sig(inst):
        av = inst.argval
        if isinstance(av, types.CodeType):
            av = ('code', av.co_name)
        elif inst.opname == 'LOAD_CONST':
            av = tag(av)
        else:
            av = repr(av)
        return (inst.opname, inst.opcode, inst.optype, inst.real_size,
                bool(inst.has_arg), bool(inst.has_extended_arg), inst.offset,
                bool(inst.is_jump_target), av)

    def file_sig(pyc_path):
        f = PYCFile(pyc_path)
        f.apply_patches(list(patches))
        out = []
        for bc in f.iter_bytecodes():
            # 注：判据的 CFG 形状比较（is_control_flow_equivalent）完全由指令流派生
            #（基本块切分 + 跳转目标），故指令流一致 ⇒ CFG 一致；本指纹以指令流为准，
            # 省去 networkx 图构造（成本 ~2/3），语义等价。
            out.append((bc.name,
                        tuple(inst_sig(i) for i in bc),
                        repr(getattr(bc, 'named_exception_table', None)),
                        bc.co_varnames if hasattr(bc, 'co_varnames') else None,
                        bc.co_flags if hasattr(bc, 'co_flags') else None))
        out.sort(key=lambda r: (r[0], r[1]))
        return tuple(out)

    return file_sig


def main():
    file_sig = load_sig()
    a = file_sig(sys.argv[1])
    b = file_sig(sys.argv[2])
    if a == b:
        print('VISIBLE-SIGNATURE-EQUAL')
        return 0
    print('VISIBLE-SIGNATURE-DIFFER')
    na = {r[0] for r in a}
    nb = {r[0] for r in b}
    print('names only in A:', sorted(na - nb))
    print('names only in B:', sorted(nb - na))
    for ra, rb in zip(a, b):
        if ra[0] != rb[0]:
            print('pairing differs at', ra[0], rb[0])
            break
        if ra[1] != rb[1]:
            for i, (x, y) in enumerate(zip(ra[1], rb[1])):
                if x != y:
                    print('first instr diff @%d:\n  A=%r\n  B=%r' % (i, x, y))
                    break
            else:
                print('instr count differs: %d vs %d' % (len(ra[1]), len(rb[1])))
            break
        if ra[2] != rb[2]:
            print('exception table differs in', ra[0])
            break
        if ra[3] != rb[3]:
            print('co_varnames differs (NOT judged):', ra[0], ra[3], rb[3])
            break
        if ra[4] != rb[4]:
            print('co_flags differs (NOT judged):', ra[0], ra[3], rb[3])
            break
    return 1


if __name__ == '__main__':
    sys.exit(main())
