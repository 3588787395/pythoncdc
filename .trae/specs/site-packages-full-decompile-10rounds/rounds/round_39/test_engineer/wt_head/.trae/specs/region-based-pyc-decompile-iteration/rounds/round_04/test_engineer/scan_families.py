#!/usr/bin/env python3
"""F2/F6/F7/F8 影响面扫描器（T1，测试工程师，精确版）。

输入：由 scripts/round_batch.py 生成的基线 batch JSON（每条文件含 mismatches，
      每个 mismatch 含 name 与 first_diff{index, orig_op, orig_arg}）。
针对每个「确实不匹配的函数」，按优先级 F2 > F8 > F7 > F6 判定其归属 family：

  F2 — 类体/局部同名别名：LOAD_NAME/GLOBAL/FAST X ; STORE_NAME X（同名）
  F8 — if 块内 import：IMPORT_NAME 之前（同一语句内）出现 if 守卫条件跳转
  F7 — STORE_ATTR 的值为三元：STORE_ATTR 之前存在 条件跳转 + JUMP_FORWARD 合并点 构成的三元
  F6 — for/while 循环区内 mismatch：函数含循环，且首个不一致点落在循环字节区间内
        （含 for/while...else；以 convert.pyc getchnstr 的 continue 极性反转为代表）

仅统计「不匹配函数」，从而精确衡量每个 family 实际影响多少文件 / 多少函数。
纯线性 + 跳转目标分析，不反编译；101 文件 < 30s。

用法（Python 3.11.7）：
    D:/Python/python.exe scan_families.py <baseline_all.json>
"""
import json
import marshal
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]  # .../pythoncdc-main
sys.path.insert(0, str(ROOT))
import dis

NOISE = {'NOP', 'PRECALL', 'EXTENDED_ARG', 'COPY_FREE_VARS', 'MAKE_CELL'}
TERNARY_COND = {
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_TRUE', 'JUMP_IF_TRUE_OR_POP',
    'JUMP_IF_FALSE_OR_POP', 'POP_JUMP_BACKWARD_IF_NONE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
}
IF_GUARD = {
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
}


def _off(ins):
    try:
        return int(str(ins.argval).split()[-1])
    except Exception:
        return None


def _load_code(p):
    with open(p, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_by_name(top, name):
    if (top.co_name or '<module>') == name:
        return top
    for c in top.co_consts:
        if isinstance(c, types.CodeType):
            r = find_by_name(c, name)
            if r:
                return r
    return None


def instrs(co):
    return list(dis.get_instructions(co))


def filt_instrs(co):
    return [i for i in dis.get_instructions(co) if i.opname not in NOISE]


def detect_f2(ins):
    for i in range(len(ins) - 1):
        a, b = ins[i], ins[i + 1]
        if a.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST') and \
           b.opname == 'STORE_NAME' and a.argval == b.argval:
            return True
    return False


def detect_f7(ins):
    """STORE_ATTR 的值为三元表达式（条件跳转 + JUMP_FORWARD 合并）。返回 (bool, store_filt_idx)。"""
    n = len(ins)
    for m in range(n):
        if ins[m].opname != 'STORE_ATTR':
            continue
        mo = ins[m].offset
        for j2 in range(m - 1, -1, -1):
            if ins[j2].opname != 'JUMP_FORWARD':
                continue
            t2 = _off(ins[j2])
            if t2 is None or t2 > mo:
                continue
            bad = False
            for k in range(j2 + 1, m):
                if ins[k].opname.startswith('STORE_') or ins[k].opname == 'RETURN_VALUE':
                    bad = True
                    break
            if bad:
                continue
            for j1 in range(j2 - 1, -1, -1):
                if ins[j1].opname in TERNARY_COND:
                    t1 = _off(ins[j1])
                    if t1 is not None and ins[j1].offset < t1 <= t2:
                        return True, m
    return False, None


def detect_f8(ins):
    """IMPORT_NAME 位于 if 的 then 块内（同一语句前有守卫跳转）。返回 (bool, import_filt_idx)。"""
    n = len(ins)
    for k in range(n):
        if ins[k].opname != 'IMPORT_NAME':
            continue
        for j in range(k - 1, -1, -1):
            op = ins[j].opname
            if op in IF_GUARD:
                return True, k
            if op.startswith('STORE_') or op == 'RETURN_VALUE':
                break
            if op in ('JUMP_BACKWARD', 'JUMP_FORWARD') and j < k - 1:
                break
    return False, None


def has_loop(ins):
    opnames = {i.opname for i in ins}
    if 'FOR_ITER' in opnames:
        return True
    return 'JUMP_BACKWARD' in opnames and 'POP_JUMP_FORWARD_IF_FALSE' in opnames


def detect_f6_else(ins):
    """严格 for/while...else：存在 FOR_ITER 回环，且 break 跳转越过 else 块（目标 > 耗尽目标）。"""
    max_off = max((i.offset for i in ins), default=0)
    for i in ins:
        if i.opname != 'FOR_ITER':
            continue
        E = _off(i)
        if E is None:
            continue
        if not any(b.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                   and _off(b) is not None and _off(b) <= i.offset for b in ins):
            continue
        for b in ins:
            if b.opname == 'JUMP_FORWARD':
                tb = _off(b)
                if tb is not None and tb > E and tb <= max_off:
                    return True
    return False


def detect_f6_broad(ins, filt, fd_index):
    """首个不一致点落在某个 for/while 循环的字节区间内（含 else）—— 宽代理。"""
    if fd_index is None or not has_loop(ins):
        return False
    for fi, i in enumerate(filt):
        if i.opname != 'FOR_ITER':
            continue
        E = _off(i)
        if E is None:
            continue
        ei = None
        for idx in range(fi + 1, len(filt)):
            if filt[idx].offset >= E:
                ei = idx
                break
        loop_end = ei if ei is not None else (len(filt) - 1)
        if fi <= fd_index <= loop_end:
            return True
    return False


def classify(ins, filt, fd_index):
    # F2：类体/局部同名别名赋值
    if detect_f2(ins):
        return 'F2'
    # F8：if 块内 import，且首个不一致点贴近 import/if 守卫（避免仅是“函数里恰好有 import”）
    f8, f8_idx = detect_f8(ins)
    if f8 and fd_index is not None and f8_idx is not None and abs(fd_index - f8_idx) <= 6:
        return 'F8'
    # F7：STORE_ATTR 值为三元，且首个不一致点贴近该 STORE_ATTR
    f7, f7_idx = detect_f7(ins)
    if f7 and fd_index is not None and f7_idx is not None and abs(fd_index - f7_idx) <= 8:
        return 'F7'
    # F6：for/while...else 且首个不一致点落在该循环区间内（否则只是“函数里恰好有 for/else”）
    if detect_f6_else(ins) and detect_f6_broad(ins, filt, fd_index):
        return 'F6'
    return None


def main():
    if len(sys.argv) < 2:
        print('usage: scan_families.py <baseline_all.json>')
        return 1
    base = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    files = base.get('files', base) if isinstance(base, dict) else base

    fam_files = {'F2': set(), 'F6': set(), 'F7': set(), 'F8': set()}
    fam_funcs = {'F2': set(), 'F6': set(), 'F7': set(), 'F8': set()}
    f6_strict_files = set()
    f6_strict_funcs = set()
    details = []
    unclassified = []

    for rec in files:
        path = rec.get('path')
        mism = rec.get('mismatches', [])
        if not path or not os.path.exists(path):
            continue
        rel = os.path.relpath(path, str(ROOT / 'site-packages'))
        top = None
        funcs_hit = {'F2': [], 'F6': [], 'F7': [], 'F8': []}
        for m in mism:
            nm = m.get('name')
            if not nm:
                continue
            if top is None:
                try:
                    top = _load_code(path)
                except Exception as ex:
                    print(f'[skip] {path}: {ex}')
                    break
            co = find_by_name(top, nm)
            if co is None:
                continue
            ins = instrs(co)
            filt = filt_instrs(co)
            fd = m.get('first_diff') or {}
            fd_index = fd.get('index')
            fam = classify(ins, filt, fd_index)
            if fam:
                funcs_hit[fam].append(nm)
                if fam == 'F6' and detect_f6_else(ins):
                    f6_strict_files.add(rel)
                    f6_strict_funcs.add(f'{rel}::{nm}')
            else:
                unclassified.append(f'{rel}::{nm}')
        hit = {f for f in ('F2', 'F6', 'F7', 'F8') if funcs_hit[f]}
        if hit:
            details.append({'file': rel, 'hits': sorted(hit),
                            'funcs': funcs_hit})
            for f in hit:
                fam_files[f].add(rel)
                for fn in funcs_hit[f]:
                    fam_funcs[f].add(f'{rel}::{fn}')

    out = {
        'families': {
            f: {'files': sorted(fam_files[f]),
                'file_count': len(fam_files[f]),
                'func_count': len(fam_funcs[f]),
                'funcs': sorted(fam_funcs[f])}
            for f in ('F2', 'F6', 'F7', 'F8')
        },
        'f6_strict_else': {
            'file_count': len(f6_strict_files),
            'func_count': len(f6_strict_funcs),
            'funcs': sorted(f6_strict_funcs),
        },
        'unclassified_mismatch_funcs': sorted(unclassified),
    }
    here = Path(__file__).resolve().parent
    (here / 'impact_families.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'扫描 baseline 文件数: {len(files)}')
    for f in ('F2', 'F6', 'F7', 'F8'):
        print(f'  {f}: {len(fam_files[f])} 文件 / {len(fam_funcs[f])} 函数')
    print(f'  F6 严格(for/while...else): {len(f6_strict_files)} 文件 / {len(f6_strict_funcs)} 函数')
    print(f'  未归类不匹配函数: {len(unclassified)}')
    print(f'明细写入: {here / "impact_families.json"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
