"""对 partial pyc 做最小差异排名：每个 pyc 统计叶子函数层的总指令不匹配数，
并找出最小不匹配的函数及其首个不匹配 (orig_op -> recomp_op) 对。输出最容易修复的 25 个。"""
import sys, dis, types, marshal, json, os

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

INDEX = "pyc_index.json"


def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)


def is_leaf(co):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            return False
    return True


def is_jump(op):
    return op.startswith("JUMP") or op.startswith("POP_JUMP") or op == "FOR_ITER"


def seq(co):
    out = []
    for i in dis.get_instructions(co):
        if is_jump(i.opname):
            out.append((i.opname, "<J>"))
        else:
            out.append((i.opname, i.argval))
    return out


def key(c):
    return (c.co_name, c.co_argcount, c.co_kwonlyargcount)


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
    rb = {}
    for c in rc:
        rb.setdefault(key(c), []).append(c)
    total = 0
    best_func = None
    best_mismatch = 10**9
    best_pairs = []
    for co in oc:
        cand = rb.get(key(co))
        if not cand:
            continue
        if not is_leaf(co):
            continue
        a = seq(co); b = seq(cand[0])
        if a == b:
            continue
        mm = 0
        pairs = []
        for i in range(max(len(a), len(b))):
            oa = a[i] if i < len(a) else None
            ob = b[i] if i < len(b) else None
            if oa != ob:
                mm += 1
                if len(pairs) < 4:
                    pairs.append("%s->%s" % (oa[0] if oa else "<--", ob[0] if ob else "-->"))
        total += mm
        if mm < best_mismatch:
            best_mismatch = mm
            best_func = co.co_name
            best_pairs = pairs
    if best_func is not None:
        results.append((rel, total, "%s(%d):%s" % (best_func, best_mismatch, ";".join(best_pairs)), best_pairs))

results.sort(key=lambda x: x[1])
print("=== EASIEST PARTIAL (by total leaf mismatches) ===")
for r in results[:25]:
    print("%8d  %s" % (r[1], r[0]))
    print("           %s" % r[2])
print("=== total partial scanned:", len(results))
