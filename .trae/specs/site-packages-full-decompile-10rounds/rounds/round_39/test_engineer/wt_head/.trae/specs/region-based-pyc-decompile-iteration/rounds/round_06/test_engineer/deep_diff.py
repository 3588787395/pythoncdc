"""鲁棒深度 diff：用「递归深签名」匹配 code object，避免同名 lambda 键碰撞。

深签名 = (co_name, argcount, kwonly, tuple((opname, norm_argval)))
  - jump 指令 argval 归一为 '<J>'
  - LOAD_CONST 的 code object argval 递归为深签名（嵌套 code 参与匹配）
这样两个同名同参 lambda 若常量不同 → 深签名不同 → 不会误配对。

输出：原始侧存在、但重编译侧无相同深签名的 (name,argcount) 函数，及其指令级差异。
用法：deep_diff.py <pyc> [func_name]
"""
import sys, dis, types, marshal

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc


def is_jump(op):
    return op.startswith("JUMP") or op.startswith("POP_JUMP") or op == "FOR_ITER"


def deep_sig(co):
    body = []
    for i in dis.get_instructions(co):
        if is_jump(i.opname):
            av = "<J>"
        elif isinstance(i.argval, types.CodeType):
            av = deep_sig(i.argval)
        else:
            av = i.argval
        body.append((i.opname, av))
    return (co.co_name, co.co_argcount, co.co_kwonlyargcount, tuple(body))


def norm_instr(co):
    """指令序列，code-object 常量归一为其深签名，便于干净比对打印。"""
    out = []
    for i in dis.get_instructions(co):
        if is_jump(i.opname):
            av = "<J>"
        elif isinstance(i.argval, types.CodeType):
            av = deep_sig(i.argval)
        else:
            av = i.argval
        out.append((i.opname, av))
    return out


def is_leaf(co):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            return False
    return True


def collect_sigs(co, out):
    out.append(deep_sig(co))
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect_sigs(c, out)


def collect_objs(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect_objs(c, out)


pyc = sys.argv[1]
func = sys.argv[2] if len(sys.argv) > 2 else None

with open(pyc, "rb") as f:
    f.read(16)
    omc = marshal.load(f)
src = decompile_pyc(pyc, use_cfg=True)
rmc = compile(src, "<d>", "exec")

oc = []; collect_objs(omc, oc)
rc = []; collect_objs(rmc, rc)

osig = [deep_sig(c) for c in oc]
rsig = [deep_sig(c) for c in rc]

from collections import Counter
oc_c = Counter(osig)
rc_c = Counter(rsig)

# 找出原始有、重编译无（或计数少）的签名，仅报告叶子函数（无嵌套 code object）
print("=== leaf signatures present in ORIGINAL but under-represented in RECOMPILED ===")
shown = 0
for co_obj in oc:
    sig = deep_sig(co_obj)
    cnt = oc_c[sig]
    rcnt = rc_c.get(sig, 0)
    if rcnt < cnt and is_leaf(co_obj):
        name, argc, kw, body = sig
        if func and name != func:
            continue
        print("### %s argc=%d kw=%d (orig=%d recomp=%d)" % (name, argc, kw, cnt, rcnt))
        cand = [c for c in rc if is_leaf(c) and c.co_name == name
                and c.co_argcount == argc and c.co_kwonlyargcount == kw]
        ref = None
        for c in cand:
            if len(norm_instr(c)) == len(norm_instr(co_obj)):
                ref = c; break
        if ref is None and cand:
            ref = cand[0]
        a = norm_instr(co_obj)
        b = norm_instr(ref) if ref else []
        n = max(len(a), len(b))
        for i in range(n):
            oa = a[i] if i < len(a) else None
            ob = b[i] if i < len(b) else None
            mark = "!" if oa != ob else " "
            print(" %s%3d A: %-40s B: %s" % (mark, i, str(oa), str(ob)))
        print()
        shown += 1
        if shown >= 8:
            break
if shown == 0:
    # 检查非叶子：是否有任一签名欠表示
    any_under = any(rc_c.get(s, 0) < cnt for s, cnt in oc_c.items())
    print("(no leaf mismatch)" if not any_under else
          "(leaf mismatch none, but some nested signatures differ — inspect with --all)")
