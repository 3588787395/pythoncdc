"""鲁棒排名：用 deep_sig 匹配避免同名 lambda 键碰撞。对每个 partial pyc 统计
「欠表示 code object 数」（原始有、重编译无相同深签名），并列出首个欠表示函数及其
指令级差异首段。按欠表示 code object 总数升序排，输出最容易修复的 30 个。"""
import sys, dis, types, marshal, json, os
from collections import Counter

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

INDEX = "pyc_index.json"


def is_jump(o):
    return o.startswith("JUMP") or o.startswith("POP_JUMP") or o == "FOR_ITER"


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


def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)


def norm(co):
    out = []
    for i in dis.get_instructions(co):
        if is_jump(i.opname):
            av = "<J>"
        elif isinstance(i.argval, types.CodeType):
            av = "<CODE:%s>" % i.argval.co_name
        else:
            av = i.argval
        out.append((i.opname, av))
    return out


with open(INDEX) as f:
    idx = json.load(f)
base = os.getcwd()
results = []
for e in idx:
    rel = e.get("path") or e.get("pyc")
    status = e.get("decompile_status")
    if status != "partial":
        continue
    pyc = rel if os.path.isabs(rel) else os.path.join(base, rel)
    if not os.path.exists(pyc):
        continue
    try:
        with open(pyc, "rb") as f:
            f.read(16)
            omc = marshal.load(f)
        src = decompile_pyc(pyc, use_cfg=True)
        rmc = compile(src, "<d>", "exec")
    except Exception as ex:
        results.append((rel, 10**9, "<err:%s>" % type(ex).__name__, []))
        continue
    oc = []; collect(omc, oc)
    rc = []; collect(rmc, rc)
    oc_c = Counter(deep_sig(c) for c in oc)
    rc_c = Counter(deep_sig(c) for c in rc)
    under = 0
    first = None
    first_pairs = []
    for co in oc:
        s = deep_sig(co)
        if rc_c.get(s, 0) < oc_c[s]:
            under += 1
            if first is None:
                first = co
                a = norm(co)
                # find a recompiled same-name same-argcount code obj as reference
                ref = None
                for c in rc:
                    if c.co_name == co.co_name and c.co_argcount == co.co_argcount and c.co_kwonlyargcount == co.co_kwonlyargcount and len(norm(c)) == len(a):
                        ref = c; break
                b = norm(ref) if ref else []
                for i in range(max(len(a), len(b))):
                    x = a[i] if i < len(a) else None
                    y = b[i] if i < len(b) else None
                    if x != y and len(first_pairs) < 5:
                        first_pairs.append("%s->%s" % (x[0] if x else "<--", y[0] if y else "-->"))
    if under > 0:
        results.append((rel, under, "%s(%d):%s" % (first.co_name if first else "?", len(norm(first)) if first else 0, ";".join(first_pairs)), first_pairs))

results.sort(key=lambda x: x[1])
print("=== EASIEST PARTIAL (by # under-represented code objects) ===")
for r in results[:30]:
    print("%4d  %s" % (r[1], r[0]))
    print("         %s" % r[2])
print("=== total partial scanned:", len(results))
