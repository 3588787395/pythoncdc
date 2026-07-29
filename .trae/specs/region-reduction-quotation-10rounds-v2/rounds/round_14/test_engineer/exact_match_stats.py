"""R14 测试工程师：字节码一致性统计（NOP 过滤 + 跳转目标归一化为指令索引）。

归一化说明（对齐 spec Requirement: 跳转目标语义等价归一化）：
- SKIP_OPS 过滤掉 EXTENDED_ARG/CACHE/NOP 等无语义指令。
- JUMP_OPS 的 argval 由字节码 offset 归一化为过滤后的指令索引，使跳转目标
  指向"同一 elif 链的下一分支入口"这类语义等价目标在比较时被识别为一致。

R14 基线版本：与 R13 一致，用于确认基线 144/150。
修复工程师阶段将在此文件上增强跳转目标语义等价归一化（见 fix_report.md）。
"""
import sys, json, types, dis, os

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r14_decompiled.py'
OUT_DIR = '/tmp/r14_out'
OUT_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE', 'NOP')

JUMP_OPS = frozenset({
    'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE', 'POP_JUMP_FORWARD_IF_NONE',
    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
    'POP_JUMP_BACKWARD_IF_NOT_NONE', 'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
    'JUMP_IF_NOT_EXC_MATCH', 'FOR_ITER',
})


def get_instr_list(co):
    raw = [ins for ins in dis.get_instructions(co) if ins.opname not in SKIP_OPS]
    offset_to_idx = {ins.offset: idx for idx, ins in enumerate(raw)}
    instrs = []
    for idx, ins in enumerate(raw):
        if ins.opname in JUMP_OPS and ins.argval is not None and isinstance(ins.argval, int):
            target_idx = offset_to_idx.get(ins.argval, -1)
            instrs.append((ins.offset, ins.opname, ('J', target_idx)))
        else:
            instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, tuple) and isinstance(av_b, tuple) and av_a[0] == 'J' and av_b[0] == 'J':
        return av_a[1] == av_b[1]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    print(f"[stats] orig code objects: {len(orig_cos)}")

    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        new_code = compile(src, '<decompiled>', 'exec')
        compile_ok = True
    except SyntaxError as e:
        new_code = None
        compile_ok = False
        print(f"[stats] compile FAILED: {e}")

    new_cos = walk_code(new_code) if new_code is not None else {}
    print(f"[stats] new code objects: {len(new_cos)}")

    results = {}
    matched = mismatched = missing = 0

    for name, orig_co in orig_cos.items():
        if name not in new_cos:
            results[name] = {'status': 'missing', 'orig_len': len(get_instr_list(orig_co))}
            missing += 1
            continue
        oa = get_instr_list(orig_co)
        na = get_instr_list(new_cos[name])
        if len(oa) != len(na):
            results[name] = {'status': 'len_diff', 'orig_len': len(oa), 'new_len': len(na), 'diff': len(na) - len(oa)}
            mismatched += 1
            continue
        first_diff = -1
        for i, (x, y) in enumerate(zip(oa, na)):
            if not instr_equal(x, y):
                first_diff = i
                break
        if first_diff < 0:
            results[name] = {'status': 'match'}
            matched += 1
        else:
            results[name] = {'status': 'instr_diff', 'first_diff_idx': first_diff,
                             'orig_at': list(oa[first_diff]), 'new_at': list(na[first_diff])}
            mismatched += 1

    total = len(orig_cos)
    sr = matched / total * 100 if total else 0.0
    print(f"[stats] compile_ok={compile_ok}")
    print(f"[stats] total={total} matched={matched} mismatched={mismatched} missing={missing} success_rate={sr:.2f}%")
    print(f"[stats] V2-R13 baseline=144/150 (96.00%) — R14 must not regress")

    out = {'summary': {'total': total, 'matched': matched, 'mismatched': mismatched,
                       'missing': missing, 'success_rate_pct': round(sr, 2),
                       'compile_ok': compile_ok}, 'results': results}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"[stats] wrote {OUT_JSON}")

    mism = [(n, r) for n, r in results.items() if r['status'] != 'match']
    print(f"[stats] mismatched functions ({len(mism)}):")
    for n, r in mism:
        if r['status'] == 'len_diff':
            print(f"  - {n}: len_diff orig={r['orig_len']} new={r['new_len']} (diff={r['diff']:+d})")
        elif r['status'] == 'instr_diff':
            print(f"  - {n}: instr_diff @idx{r['first_diff_idx']}")
        else:
            print(f"  - {n}: {r['status']}")


if __name__ == '__main__':
    main()
