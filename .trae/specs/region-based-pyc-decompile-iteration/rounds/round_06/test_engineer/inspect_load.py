"""打印单个函数的原始/重编译指令对照（用于定位 dict 键顺序等问题）。

用法: D:/Python/python.exe inspect_load.py <pyc路径> <函数名> [上下文行数]
"""
import sys
import os
import types
import marshal
import dis

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)


def norm(co):
    out = []
    for ins in dis.get_instructions(co):
        if 'JUMP' in ins.opname or ins.opname == 'FOR_ITER':
            out.append((ins.opname, '<J>'))
        else:
            out.append((ins.opname, ins.argval))
    return out


def find(co, name, out):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                out.append(c)
            find(c, name, out)


def main():
    pyc = sys.argv[1]
    fname = sys.argv[2]
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    from pycdc import decompile_pyc
    src = decompile_pyc(pyc, use_cfg=True)

    with open(pyc, 'rb') as f:
        f.read(16)
        orig = marshal.load(f)
    o = []
    find(orig, fname, o)
    if not o:
        print('原始中未找到', fname)
        return
    oco = o[0]

    try:
        re_mod = compile(src, '<decomp>', 'exec')
    except SyntaxError as e:
        print('重编译失败:', e)
        return
    r = []
    find(re_mod, fname, r)
    if not r:
        print('重编译后未找到', fname)
        return

    a, b = norm(oco), norm(r[0])
    print('ORIG %d 条 / RECOMP %d 条' % (len(a), len(b)))
    # 找第一处差异
    first = None
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x != y:
            first = i
            break
    if first is None:
        print('=== BYTE-IDENTICAL ===')
        return
    lo = max(0, first - ctx)
    hi = min(max(len(a), len(b)), first + ctx)
    print('首个差异 index=%d，上下文 %d..%d' % (first, lo, hi))
    for i in range(lo, hi):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        mark = '   ' if x == y else '>> '
        print('%s%3d  ORIG: %-45s RECOMP: %s' % (mark, i, x, y))

    print('--- 反编译 %s ---' % fname)
    k = src.find('def ' + fname + '(')
    print(src[k:k + 1200] if k >= 0 else 'NOT FOUND')


if __name__ == '__main__':
    main()
