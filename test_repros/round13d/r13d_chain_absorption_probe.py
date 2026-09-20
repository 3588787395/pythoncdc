"""Round 13d 探针组：if/elif/else 链归约后，链后续语句被吸入某个分支（真语义缺陷）。

判据 = 严格尺子（_r10_strict_check.strict_compare），走完整流水线：
源码 -> 3.11.7 编译成 pyc -> 项目反编译器 -> OK.py -> 再编译 -> 逐指令严格对照。

R13-W2-A（分支以循环区结束 -> 链后语句被吸入该分支）：s2 / s7 / s10
R13-W2-B（链无 else 臂 -> 链后语句被吸入新建的 else 臂）：s8
负对照（必须保持 MATCH，证明判据不是见链就报）：s5 / s6 / s9

正确性判据不是「字节码少一条」，而是**语义**：s10 的产物把 `y = 7` 和链尾
if/else 变成了「仅当 elif 臂成立才执行」，原始语义是无条件执行 —— 控制流被改。
"""
import io
import os
import py_compile
import sys

ROOT = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'test_repros', 'round13d'))

from scripts import pyc_batch_verify as pbv            # noqa: E402
from _r10_strict_check import strict_compare, _load_map  # noqa: E402

WORK = 'D:/Temp/r13d'

# (id, 期望, 源码)  期望 'MISMATCH' = 已知真缺陷复现；'MATCH' = 负对照
SHAPES = [
    ('s2_elif_loop_then_tail', 'MISMATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        for d in r:
            pass
    else:
        return 2
    if c:
        return 3
    else:
        return 4
'''),
    ('s7_elif_while_then_tail', 'MISMATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        while c:
            c = 0
    else:
        return 2
    if c:
        return 3
    else:
        return 4
'''),
    ('s10_loop_then_multi_tail', 'MISMATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        for d in r:
            pass
    else:
        return 2
    y = 7
    if c:
        return 3
    else:
        return 4
'''),
    ('s8_no_else_arm_then_tail', 'MISMATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        for d in r:
            pass
    if c:
        return 3
    else:
        return 4
'''),
    ('n1_elif_plain_assign', 'MATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        x = 5
    else:
        return 2
    if c:
        return 3
    else:
        return 4
'''),
    ('n2_then_assign_tail', 'MATCH', '''
def g(c, r):
    if c:
        x = 5
    elif r:
        return 1
    else:
        return 2
    if c:
        return 3
    else:
        return 4
'''),
    ('n3_elif_ends_with_return', 'MATCH', '''
def g(c, r):
    if c:
        return 1
    elif r:
        for d in r:
            if d:
                break
        return 6
    else:
        return 2
    if c:
        return 3
    else:
        return 4
'''),
]


def run_one(sid, expect, src):
    os.makedirs(WORK, exist_ok=True)
    py = os.path.join(WORK, sid + '.py')
    io.open(py, 'w', encoding='utf-8', newline='\n').write(src.lstrip('\n'))
    pyc = os.path.join(WORK, sid + '.pyc')
    py_compile.compile(py, cfile=pyc, doraise=True, quiet=2)

    out = os.path.join(WORK, sid + 'OUT.py')
    res = pbv.decompile_single(pyc, ok_py_path=out)
    if not res.get('success'):
        return sid, expect, 'DECOMPILE-FAIL', res.get('error'), ''
    dec = py_compile.compile(out, doraise=True, quiet=2,
                             cfile=os.path.join(WORK, sid + '_dec.pyc'))
    om, dm = _load_map(pyc), _load_map(dec)
    key = [k for k in om if k.endswith('g')][0]
    kind, msg, _ = strict_compare(om[key], dm[key])
    got = 'MATCH' if kind is None else 'MISMATCH'
    body = res['source'][res['source'].find('def g'):]
    return sid, expect, got, ('%s %s' % (kind, msg)) if kind else 'ok', body


def main():
    print('== Round 13d if/elif/else 链吸收探针组 ==')
    fails = 0
    for sid, expect, src in SHAPES:
        _sid, _exp, got, detail, body = run_one(sid, expect, src)
        ok = (got == expect)
        fails += 0 if ok else 1
        print('  [%s] %-28s expect=%-8s got=%-9s %s' %
              ('PASS' if ok else 'FAIL', sid, expect, got, detail))
        if got == 'MISMATCH':
            for l in body.splitlines():
                print('        | ' + l)
    print('== %d/%d PASS ==' % (len(SHAPES) - fails, len(SHAPES)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
