"""靶向扫描 G6：原始 pyc 含 POP_JUMP_*_IF_[NOT_]NONE 但反编译重编译后该指令 opname 改变的函数。

is None / is not None 语义丢失是最干净的 G6 信号。输出每个命中 pyc 的第一个命中函数与指令差异段。
"""
import sys, dis, types, marshal, json, os

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc

INDEX = "pyc_index.json"


def collect(co, out):
    out.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)


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


def key(c):
    return (c.co_name, c.co_argcount, c.co_kwonlyargcount)


NONE_TEST_OPS = {
    "POP_JUMP_FORWARD_IF_NONE", "POP_JUMP_FORWARD_IF_NOT_NONE",
    "POP_JUMP_BACKWARD_IF_NONE", "POP_JUMP_BACKWARD_IF_NOT_NONE",
}
NONE_TEST_SHORT = {o: o.replace("POP_JUMP_", "") for o in NONE_TEST_OPS}


def scan_one(pyc):
    try:
        with open(pyc, "rb") as f:
            f.read(16)
            omc = marshal.load(f)
    except Exception as e:
        return None
    try:
        src = decompile_pyc(pyc, use_cfg=True)
        rmc = compile(src, "<d>", "exec")
    except Exception as e:
        return None
    oc = []; collect(omc, oc)
    rc = []; collect(rmc, rc)
    rb = {}
    for c in rc:
        rb.setdefault(key(c), []).append(c)
    hits = []
    for co in oc:
        cand = rb.get(key(co))
        if not cand:
            continue
        a = seq(co); b = seq(cand[0])
        if a == b:
            continue
        # 检查 G6 特征：原始含 None-test 跳转，重编译对应位置 opname 变了
        for i in range(min(len(a), len(b))):
            oa, ob = a[i], b[i]
            if oa[0] in NONE_TEST_OPS and oa[0] != ob[0]:
                hits.append((co.co_name, co.co_argcount, i, oa[0], ob[0]))
                break
    return hits


def main():
    with open(INDEX) as f:
        idx = json.load(f)
    # idx: list of {"pyc":..., "status":...} 或 dict
    if isinstance(idx, dict):
        entries = idx.get("files", idx.get("pyc", []))
    else:
        entries = idx
    base = os.getcwd()
    found = 0
    for e in entries:
        if isinstance(e, dict):
            rel = e.get("pyc") or e.get("path") or e.get("file")
            status = e.get("status")
        else:
            rel = e; status = None
        if rel is None:
            continue
        pyc = rel if os.path.isabs(rel) else os.path.join(base, rel)
        if not os.path.exists(pyc):
            continue
        hits = scan_one(pyc)
        if hits:
            found += 1
            print("### %s  status=%s  hits=%d  %s" % (rel, status, len(hits), hits[:4]))
    print("TOTAL pyc with G6 signal:", found)


if __name__ == "__main__":
    main()
