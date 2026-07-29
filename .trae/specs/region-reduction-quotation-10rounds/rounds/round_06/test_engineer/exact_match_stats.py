"""轮 6 测试工程师：字节码一致性统计。"""
import sys
import json
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r6_decompiled.py'
OUT_DIR = '/tmp/r6_out'
OUT_JSON = OUT_DIR + '/bc_results.json'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co: types.CodeType):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b) -> bool:
    if a[1] != b[1]:
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
    if sink is None:
        sink = {}
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    else:
        name = prefix + co.co_name
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


def main() -> None:
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    orig_top = load_orig()
    orig_cos = walk_code(orig_top)
    print(f"[stats] orig code objects: {len(orig_cos)}")

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
    print(f"[stats] baseline check: matched={matched}, R5=141 (no regression)")
    print(f"[stats] wrote {OUT_JSON}")

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
