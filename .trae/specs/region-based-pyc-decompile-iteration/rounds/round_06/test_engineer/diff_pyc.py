"""Round 06 — 逐函数 / 叶子级字节码 diff 工具（递归结构签名比较）。

给定 pyc：反编译为源码 → 重新编译 → 递归比较原始与反编译重编译的指令序列
（code object 常量按其指令序列递归下钻；跳转类指令仅比较 opcode 名，忽略目标
偏移），定位首个**叶子级**差异指令。用于跨 partial pyc 聚合缺陷家族
（G6: is not None 语义 / G5: 扁平 or / G2 闭包自由变量 / 其他）。

用法:
  diff_pyc.py <path.pyc> [func_name]        # 人类可读：打印首个叶子差异
  diff_pyc.py --scan <index.json>           # 聚合模式：扫描所有 partial，输出
                                            #   (原始op -> 反编译op) 频次表
"""
import sys
import os
import dis
import types
import json

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc


def _is_jump(opname):
    return 'JUMP' in opname or opname in ('FOR_ITER', 'BREAK_LOOP', 'CONTINUE_LOOP',
                                          'SEND', 'YIELD_FROM', 'BEFORE_WITH',
                                          'SETUP_WITH', 'SETUP_FINALLY', 'SETUP_EXCEPT',
                                          'SETUP_ASYNC_WITH', 'WITH_EXCEPT_START')


def _instr_seq(co):
    out = []
    for ins in dis.get_instructions(co):
        if _is_jump(ins.opname):
            out.append((ins.opname, '<JUMP>'))
        else:
            out.append((ins.opname, _arg_sig(ins.argval)))
    return out


def _arg_sig(v):
    if isinstance(v, types.CodeType):
        return ("CODE", v.co_name, v.co_argcount, tuple(_instr_seq(v)))
    if isinstance(v, tuple):
        return tuple(_arg_sig(x) for x in v)
    return v


def _collect_codes(mod_co, out):
    out.append(mod_co)
    for const in mod_co.co_consts:
        if isinstance(const, types.CodeType):
            _collect_codes(const, out)


def _deep_first_diff(a, b, path):
    """递归比较两条指令序列，返回首个叶子差异 (path, orig_pair, recomp_pair) 或 None。"""
    n = min(len(a), len(b))
    for i in range(n):
        oa, ob = a[i], b[i]
        if oa == ob:
            continue
        op_a, arg_a = oa
        op_b, arg_b = ob
        if (isinstance(arg_a, tuple) and arg_a and arg_a[0] == 'CODE'
                and isinstance(arg_b, tuple) and arg_b and arg_b[0] == 'CODE'):
            # 下钻到 code object 内部
            sub = _deep_first_diff(arg_a[3], arg_b[3], path + [i])
            if sub is not None:
                return sub
            # 若 code 内部完全一致但签名仍不等（如 co_name 不同），记为差异
            return path + [i], oa, ob
        return path + [i], oa, ob
    if len(a) != len(b):
        return path + [n], (a[n:] if n < len(a) else '<EOF>'), (b[n:] if n < len(b) else '<EOF>')
    return None


def _dis_tuple_top(co):
    return [(ins.opname, _arg_sig(ins.argval)) for ins in dis.get_instructions(co)]


def analyze_pyc(pyc):
    """返回该 pyc 首个叶子差异对 (orig_op, recomp_op) 或 None（全匹配）。"""
    import marshal
    with open(pyc, "rb") as f:
        f.read(16)
        orig_mod_co = marshal.load(f)
    orig_codes = []
    _collect_codes(orig_mod_co, orig_codes)

    src = decompile_pyc(pyc, use_cfg=True)
    try:
        re_mod_co = compile(src, "<decomp>", "exec")
    except SyntaxError as e:
        return ("<SYNTAX_ERROR>", str(e)[:40])
    re_codes = []
    _collect_codes(re_mod_co, re_codes)

    def key(co):
        return (co.co_name, co.co_argcount)

    re_by_key = {}
    for c in re_codes:
        re_by_key.setdefault(key(c), []).append(c)

    for co in orig_codes:
        k = key(co)
        cand = re_by_key.get(k)
        if not cand:
            continue
        a = _instr_seq(co)
        for rc in cand:
            b = _instr_seq(rc)
            d = _deep_first_diff(a, b, [])
            if d is None:
                break
        else:
            # 所有候选都不匹配
            b = _instr_seq(cand[0])
            d = _deep_first_diff(a, b, [])
            if d is not None:
                _, oa, ob = d
                return (oa[0] if isinstance(oa, tuple) else str(oa),
                        ob[0] if isinstance(ob, tuple) else str(ob))
    return None


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--scan":
        idx_path = sys.argv[2]
        idx = json.load(open(idx_path, encoding="utf-8"))
        if isinstance(idx, dict):
            entries = None
            for v in idx.values():
                if isinstance(v, list):
                    entries = v
                    break
            if entries is None:
                entries = list(idx.values())
        else:
            entries = idx
        from collections import Counter
        cnt = Counter()
        hits = []
        for e in entries:
            if e.get("decompile_status") != "partial":
                continue
            p = e["path"]
            try:
                r = analyze_pyc(p)
            except Exception as ex:
                r = ("<ERR>", repr(ex)[:40])
            if r is None:
                continue
            cnt[r] += 1
            hits.append((p, r))
        print("=== leaf-opcode diff frequency (partial pyc) ===")
        for (oa, ob), c in cnt.most_common(40):
            print("  %3d  %s  ->  %s" % (c, oa, ob))
        print("=== sample pyc per family ===")
        seen = set()
        for p, r in hits:
            if r not in seen:
                seen.add(r)
                print("  %s  :  %s -> %s" % (os.path.basename(p), r[0], r[1]))
        return 0
    # single pyc mode
    if len(sys.argv) < 2:
        print("usage: diff_pyc.py <path.pyc> [func_name] | --scan <index.json>")
        return 1
    pyc = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else None
    import marshal
    with open(pyc, "rb") as f:
        f.read(16)
        orig_mod_co = marshal.load(f)
    orig_codes = []
    _collect_codes(orig_mod_co, orig_codes)
    src = decompile_pyc(pyc, use_cfg=True)
    re_mod_co = compile(src, "<decomp>", "exec")
    re_codes = []
    _collect_codes(re_mod_co, re_codes)

    def key(co):
        return (co.co_name, co.co_argcount)

    re_by_key = {}
    for c in re_codes:
        re_by_key.setdefault(key(c), []).append(c)

    found = 0
    for co in orig_codes:
        if only and co.co_name != only:
            continue
        k = key(co)
        cand = re_by_key.get(k)
        if not cand:
            continue
        a = _instr_seq(co)
        matched = False
        for rc in cand:
            b = _instr_seq(rc)
            if _deep_first_diff(a, b, []) is None:
                matched = True
                break
        if matched:
            continue
        b = _instr_seq(cand[0])
        d = _deep_first_diff(a, b, [])
        print("### MISMATCH func=%s (argcount=%d)" % (co.co_name, co.co_argcount))
        if d is not None:
            path, oa, ob = d
            print("  first leaf diff path:", path)
            print("  ORIG  :", oa)
            print("  RECOMP:", ob)
        found += 1
        if only:
            break
    if found == 0:
        print("ALL FUNCTIONS BYTECODE-IDENTICAL")
    else:
        print("total mismatching functions: %d" % found)
    return 0


if __name__ == "__main__":
    sys.exit(main())
