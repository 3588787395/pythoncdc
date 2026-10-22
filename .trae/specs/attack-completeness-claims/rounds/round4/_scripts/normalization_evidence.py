#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**归一化/比较算子 归因器**（为什么某个语义差异判据看不见）。

对一组 (原始 pyc, 变异产物 .py)：
  * 复用附件判据本体的装载与 patch 序列
    （remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable,
      remove_extended_arg, replace_firstlno —— 与 `compare_pyc` 完全一致）；
  * 计算两个指纹：
      RAW   ：patch 之前的指令流（含 argval）
      NORM  ：patch 之后的指令流
      VIS   ：patch 之后 + **类型敏感** argval（1 / True / 1.0 可分辨）
              —— 复刻附件判据的比较算子，只把 `==` 换成 (类型, 值) 标签
  * 归因：
      RAW 不同 & NORM 不同 & VIS 不同 ⇒ 判据**看得见**却仍判绿 ⇒ 比较算子问题（可改进）
      RAW 不同 & NORM 相同                 ⇒ 差异被**归一化**抹平 ⇒ 结构性不可见（须新增维度）
      VIS 相同                            ⇒ 差异落在判据**从不比较**的维度（co_consts/docstring/注解…）

用法：
  python -X utf8 normalization_evidence.py <a.pyc> <b.py> [<a.pyc> <b.py> ...]
"""
from __future__ import annotations

import os
import sys
import types

DEFAULT_PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'
PATCHES = ['remove_extended_arg', 'remove_nop', 'fix_indirect_jump',
           'fix_unreachable', 'remove_extended_arg', 'replace_firstlno']


def load(root=DEFAULT_PYLINGUAL):
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
    patches = [remove_extended_arg, remove_nop, fix_indirect_jump,
               fix_unreachable, remove_extended_arg, replace_firstlno]
    return PYCFile, patches


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


def fp(pyc_path, patches, apply_patches, type_sensitive):
    """返回 [(code_object_name, [inst_fingerprint...])]。"""
    import pylingual.editable_bytecode as eb
    f = eb.PYCFile(pyc_path)
    if apply_patches:
        f.apply_patches(list(patches))
    out = []
    for bc in f.iter_bytecodes():
        items = []
        for i in bc:
            av = i.argval
            if isinstance(av, types.CodeType):
                av = ('code', av.co_name)          # 附件判据对嵌套 code object 直接放行
            elif type_sensitive and i.opname == 'LOAD_CONST':
                av = tag(av)
            else:
                av = repr(av)
            items.append((i.opname, i.opcode, i.optype, i.real_size,
                          bool(i.has_arg), bool(i.has_extended_arg), i.offset,
                          bool(i.is_jump_target), av))
        out.append((bc.name, items))
    return out


def compile_py(src, tmp, name='m.pyc'):
    import py_compile
    out = os.path.join(tmp, name)
    py_compile.compile(src, cfile=out, doraise=True, optimize=0)
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    import py_compile
    import tempfile
    PYCFile, patches = load()
    tmp = tempfile.mkdtemp(prefix='normev_')
    args = sys.argv[1:]
    print('%-46s %-10s %-10s %-10s  %s'
          % ('pair', 'RAW', 'NORM', 'VIS', 'attribution'))
    for i in range(0, len(args), 2):
        a_pyc, b_py = args[i], args[i + 1]
        b_pyc = compile_py(b_py, tmp, 'b%d.pyc' % i)
        raw_a = fp(a_pyc, patches, False, False)
        raw_b = fp(b_pyc, patches, False, False)
        norm_a = fp(a_pyc, patches, True, False)
        norm_b = fp(b_pyc, patches, True, False)
        vis_a = fp(a_pyc, patches, True, True)
        vis_b = fp(b_pyc, patches, True, True)
        raw_eq, norm_eq, vis_eq = raw_a == raw_b, norm_a == norm_b, vis_a == vis_b
        if raw_eq:
            attr = 'NO-RAW-DIFF (变异未落到字节码)'
        elif norm_eq and vis_eq:
            attr = 'NORMALIZED-AWAY (归一化抹平 ⇒ 结构性不可见)'
        elif norm_eq and not vis_eq:
            attr = 'NORMALIZED-AWAY+TYPE-SENSITIVE-VISIBLE'
        elif not norm_eq and not vis_eq:
            attr = 'COMPARATOR-BLIND (判据看得见却判绿 ⇒ 算子可改进)'
        else:
            attr = 'OTHER'
        print('%-46s %-10s %-10s %-10s  %s'
              % (os.path.basename(a_pyc)[:45],
                 'same' if raw_eq else 'DIFF',
                 'same' if norm_eq else 'DIFF',
                 'same' if vis_eq else 'DIFF', attr))
        if not norm_eq:
            for (na, ia), (nb, ib) in zip(norm_a, norm_b):
                if ia != ib:
                    print('    first diff in %r:' % na)
                    print('      A:', ia)
                    print('      B:', ib)
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main())
