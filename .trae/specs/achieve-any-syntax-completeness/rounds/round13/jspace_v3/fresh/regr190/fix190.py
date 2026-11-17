# -*- coding: utf-8 -*-
"""rr-v5r190 patch: narrow the r124 [v124-LOOPHEAD] loop-reparent pass.

Single hunk, `core/cfg/region_analyzer.py::_build_region_hierarchy` (the tail pass
that re-hangs a TryExceptRegion from its absorbed parent P onto a LoopRegion L).

r124's guard demanded "L.parent is P **or** L.parent is None".  That disjunction
lumps two opposite region-tree topologies together:

  * L.parent is P (P -> L; P's offset range swallowed the loop body, so the loop
    already hangs under P): the child try really lives inside the loop and moving
    it to L is the fix (/iterfind, ElementPath: Try@494/Try@652 -> Loop@492).
  * L.parent is None (L is a *root*, i.e. an **ancestor** of P; P itself already
    sits in the loop body, e.g. `for -> try(outer) -> try(inner)`): the child try
    is a genuine child of P, and re-hanging it onto L flattens P's subtree into
    L's sibling list.

In the second shape the two nested try regions are emitted in the wrong nesting
order, so the finally normal/exception copy lineages cross: the inner
`finally: out.append(1)` is emitted as the outer finalbody and vice versa
(v_b71_face / JS-IF-017 / the whole B142 nested-finally family).

Narrowing = delete the `or L.parent is None` branch only, so the accepted set is a
strict subset of r124's (criterion reads region-tree parent links only, [C1]
same-level structural fact).  Everything else - including the existing cycle guard
and the block/entry tests - is byte-identical, and when no candidate survives the
pass is a no-op for that region (C3).

Usage:
    python fix190.py            # apply (idempotent, skips an already-applied hunk)
    python fix190.py --revert   # revert to the pre-patch bytes
"""
import hashlib
import os
import py_compile
import sys
import tempfile

TARGET = os.path.join('core', 'cfg', 'region_analyzer.py')

HUNK_OLD = """                _lp = _lr.parent
                if _lp is not _p and _lp is not None:
                    continue
"""

HUNK_NEW = """                _lp = _lr.parent
                # [v190-LOOPHOST] 宿主环 L 必须是现父 P 的**直接子节点**
                # （`L.parent is P`）。v124 原判据多放行了一条
                # `L.parent is None`——那正好是「环是 P 的**祖先**」的
                # 拓扑（P 本身就在环体内，如 for → try(外层) → try(内层)）：
                # child 相对 P 的位置在环之下，把它从 P 重挂到环，等于把 P 的
                # 真子节点拍平成环的兄弟，两层 finally 的正常/异常副本谱系随
                # 之错位（内层 finally 被当成外层 finalbody，内层 try 退化成
                # pass）。删掉该分支后判据集合是 r124 的**严格子集**（只保留
                # 「环被吸收成 P 的子节点」的 /iterfind 病形），判据只读区域
                # 树父子关系（[C1] 同层结构事实），不命中时逐位不变（C3）。
                if _lp is not _p:
                    continue
"""

HUNKS = (('A', HUNK_OLD, HUNK_NEW),)


def read(path):
    raw = open(path, 'rb').read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


def write(path, text, bom):
    with open(path, 'wb') as fh:
        if bom:
            fh.write(b'\xef\xbb\xbf')
        fh.write(text.encode('utf-8'))


def main(argv):
    revert = '--revert' in argv[1:]
    root = os.path.dirname(os.path.abspath(__file__))
    args = argv[1:]
    for i, a in enumerate(args):
        if a == '--root' and i + 1 < len(args):
            root = args[i + 1]
        elif a.startswith('--root='):
            root = a.split('=', 1)[1]
    path = os.path.join(root, TARGET)
    text, bom = read(path)
    print('target: %s bom=%s' % (path, bom))
    changed = 0
    for name, old, new in HUNKS:
        src, dst = (new, old) if revert else (old, new)
        n = text.count(src)
        print('hunk %s anchor count=%d -> %s' % (name, n, 'REVERT' if revert else 'APPLY'))
        if n == 0:
            if text.count(dst) == 1:
                print('  already in target state, skip')
                continue
            print('  ERROR: anchor not found and target state not present')
            return 2
        if n != 1:
            print('  ERROR: anchor not unique')
            return 2
        text = text.replace(src, dst)
        changed += 1
    if changed:
        write(path, text, bom)
        print('wrote %d hunk(s), bytes=%d' % (changed, len(text.encode('utf-8'))))
        if bom and open(path, 'rb').read(3) != b'\xef\xbb\xbf':
            print('  ERROR: BOM lost')
            return 4
    else:
        print('nothing to do')
    tmp = tempfile.mkdtemp()
    try:
        py_compile.compile(path, cfile=os.path.join(tmp, 'p.pyc'), doraise=True)
        print('py_compile: OK')
    except py_compile.PyCompileError as exc:
        print('py_compile: FAILED %s' % exc)
        return 3
    print('sha256(file)=%s' % hashlib.sha256(open(path, 'rb').read()).hexdigest())
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
