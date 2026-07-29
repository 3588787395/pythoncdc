"""轮 5 测试工程师：字节码一致性统计。

加载 quotation.pyc 原始 code objects（core.pyc_loader_v2.load_pyc_file_v2）
与反编译产物 /tmp/r5_decompiled.py 编译后的 code objects，
递归遍历所有 code object（含 <module> / 函数 / listcomp / lambda），
用 dis.get_instructions 比较指令序列：
  - 跳过 EXTENDED_ARG / CACHE
  - 对 code object 类型的 argval 递归比较内部字节码

输出每函数状态（match / len_diff / instr_diff / missing），
统计 matched / total / success_rate，写入 bc_results.json。

确认基线 141 / 150 可复现。
"""
import sys
import json
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r5_decompiled.py'
OUT_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_05/test_engineer'
OUT_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co: types.CodeType):
    """返回 [(offset, opname, argval)]，跳过 EXTENDED_ARG / CACHE。"""
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b) -> bool:
    """比较两条指令。code object 类型的 argval 递归比较内部字节码。"""
    if a[1] != b[1]:  # opname
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        return all(instr_equal(x, y) for x, y in zip(ia, ib))
    if isinstance(av_a, types.CodeType) or isinstance(av_b, types.CodeType):
        return False
    return av_a == av_b


def walk_code(co: types.CodeType, prefix: str = '', sink: dict = None):
    """递归遍历 code object，sink[name] = co。"""
    if sink is None:
        sink = {}
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    else:
        name = prefix + co.co_name
    sink[name] = co
    # 子 code object 的前缀：父名 + '.'，但 <module> 直接 ''
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig():
    """加载原始 pyc 的顶层 code object。"""
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def main() -> None:
    # 1. 加载原始 code objects
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    print(f"[stats] orig code objects: {len(orig_cos)}")

    # 2. 编译反编译产物
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        new_code = compile(src, '<decompiled>', 'exec')
        compile_ok = True
        compile_err = ''
    except SyntaxError as e:
        new_code = None
        compile_ok = False
        compile_err = f"{type(e).__name__}: {e}"
        print(f"[stats] compile FAILED: {compile_err}")

    new_cos = {}
    if new_code is not None:
        new_cos = walk_code(new_code)
    print(f"[stats] new code objects: {len(new_cos)}")

    # 3. 比较
    results = {}
    matched = 0
    mismatched = 0
    missing = 0

    for name, orig_co in orig_cos.items():
        if name not in new_cos:
            results[name] = {'status': 'missing', 'orig_len': len(get_instr_list(orig_co))}
            missing += 1
            continue
        oa = get_instr_list(orig_co)
        na = get_instr_list(new_cos[name])

        if len(oa) != len(na):
            results[name] = {
                'status': 'len_diff',
                'orig_len': len(oa),
                'new_len': len(na),
                'diff': len(na) - len(oa),
            }
            mismatched += 1
            continue

        # 长度相等，逐条比较
        first_diff = -1
        for i, (x, y) in enumerate(zip(oa, na)):
            if not instr_equal(x, y):
                first_diff = i
                break
        if first_diff < 0:
            results[name] = {'status': 'match'}
            matched += 1
        else:
            results[name] = {
                'status': 'instr_diff',
                'orig_len': len(oa),
                'first_diff_idx': first_diff,
                'orig_at': list(oa[first_diff]),
                'new_at': list(na[first_diff]),
            }
            mismatched += 1

    total = len(orig_cos)
    success_rate = matched / total * 100 if total else 0.0

    summary = {
        'pyc': PYC,
        'decompiled': DECOMPILED,
        'compile_ok': compile_ok,
    }
    if not compile_ok:
        summary['compile_error'] = compile_err
    summary.update({
        'total': total,
        'matched': matched,
        'mismatched': mismatched,
        'missing': missing,
        'success_rate_pct': round(success_rate, 2),
    })

    out = {'summary': summary, 'results': results}
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str)

    print(f"[stats] compile_ok={compile_ok}")
    print(f"[stats] total={total} matched={matched} mismatched={mismatched} missing={missing} success_rate={success_rate:.2f}%")
    print(f"[stats] baseline check: matched={matched}, expected 141 (no regression)")
    print(f"[stats] wrote {OUT_JSON}")

    # 不一致函数列表打印
    mism = [(n, r) for n, r in results.items() if r['status'] != 'match']
    print(f"[stats] mismatched functions ({len(mism)}):")
    for n, r in mism:
        if r['status'] == 'len_diff':
            print(f"  - {n}: len_diff orig={r['orig_len']} new={r['new_len']} (diff={r['diff']:+d})")
        elif r['status'] == 'instr_diff':
            print(f"  - {n}: instr_diff @idx{r['first_diff_idx']} orig={r['orig_at']} new={r['new_at']}")
        else:
            print(f"  - {n}: {r['status']}")


if __name__ == '__main__':
    main()
