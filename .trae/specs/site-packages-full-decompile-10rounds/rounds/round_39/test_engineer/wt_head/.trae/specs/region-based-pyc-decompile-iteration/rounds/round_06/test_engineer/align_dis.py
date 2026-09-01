"""并排反汇编：给定 pyc，对首个不匹配的**叶子函数**做逐指令对齐打印。

A = 原始 pyc 反汇编; B = 反编译后重编译反汇编。
叶子函数 = co_consts 内不含嵌套 code object 的函数，可避免 code object 身份噪声。
逐指令比较仅比 (opname, argval)，对跳转指令 argval 是目标偏移（重编译后自然漂移），
故跳转指令仅当 opname 不同才计为 mismatch。
"""
import sys, dis, types, marshal

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

pyc = sys.argv[1]
only_leaf = "--all" not in sys.argv

with open(pyc, "rb") as f:
    f.read(16)
    omc = marshal.load(f)


def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)


oc = []
collect(omc, oc)
src = decompile_pyc(pyc, use_cfg=True)
rmc = compile(src, "<d>", "exec")
rc = []
collect(rmc, rc)


def is_leaf(co):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            return False
    return True


def key(c):
    return (c.co_name, c.co_argcount, c.co_kwonlyargcount)


rb = {}
for c in rc:
    rb.setdefault(key(c), []).append(c)


def is_jump(op):
    return op.startswith("JUMP") or op.startswith("POP_JUMP") or op.startswith("SEND") or op == "FOR_ITER"


def seq(co):
    out = []
    for i in dis.get_instructions(co):
        if is_jump(i.opname):
            out.append((i.opname, "<JUMP>"))
        else:
            out.append((i.opname, i.argval))
    return out


def show(co, cand):
    a = seq(co)
    b = seq(cand)
    if a == b:
        return False
    print("### func %s (args=%d kw=%d) orig %d recomp %d" % (
        co.co_name, co.co_argcount, co.co_kwonlyargcount, len(a), len(b)))
    n = max(len(a), len(b))
    for i in range(n):
        oa = a[i] if i < len(a) else None
        ob = b[i] if i < len(b) else None
        mark = "!" if oa != ob else " "
        so = str(oa) if oa is not None else "<--"
        sb = str(ob) if ob is not None else "-->"
        print(" %s%3d A: %-55s B: %s" % (mark, i, so, sb))
    print()
    return True


shown = 0
# 优先叶子函数，避免 code-object 身份噪声
if only_leaf:
    leaf_oc = [c for c in oc if is_leaf(c)]
    for co in leaf_oc:
        cand = rb.get(key(co))
        if not cand:
            continue
        if show(co, cand[0]):
            shown += 1
            break
    if shown == 0:
        print("(no leaf mismatch found)")
else:
    for co in oc:
        cand = rb.get(key(co))
        if not cand:
            continue
        if show(co, cand[0]):
            shown += 1
    print("(%d funcs shown)" % shown)
