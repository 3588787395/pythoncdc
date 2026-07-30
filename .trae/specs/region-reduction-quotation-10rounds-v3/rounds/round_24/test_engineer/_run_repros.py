"""R24 测试工程师：批量验证 minimal_repros 是否复现两类缺陷。

对每个 repro_NN_*.py：
  1. py_compile → .pyc
  2. pycdc.py 反编译 .pyc → .decompiled.py
  3. 取原始 f 与反编译后 f 的字节码，归一化对比（沿用 exact_match_stats 口径）
  4. 报告 match / len_diff / instr_diff，并标注缺陷模式
"""
import sys, os, glob, types, dis, py_compile, subprocess, json
sys.path.insert(0, '/workspace')

REPRO_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_24/test_engineer/minimal_repros'
PYCDC = '/workspace/pycdc.py'
WORK = '/tmp/r24_repro_work'

# 复用 exact_match_stats 的归一化比较逻辑
sys.path.insert(0, '/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_24/test_engineer')
from exact_match_stats import get_instr_list, instr_equal, walk_code


def compile_src(src, name='<repro>'):
    return compile(src, name, 'exec')


def first_func(code_obj):
    """取模块级第一个函数的 code object。"""
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name != '<module>':
            # 跳过 listcomp/genexpr 等
            if const.co_name == 'f':
                return const
    return None


def compare_one(orig_co, new_co):
    oa = get_instr_list(orig_co)
    na = get_instr_list(new_co)
    if len(oa) != len(na):
        return {'status': 'len_diff', 'orig_len': len(oa), 'new_len': len(na),
                'diff': len(na) - len(oa)}
    first_diff = -1
    for i, (x, y) in enumerate(zip(oa, na)):
        if not instr_equal(x, y, ctx=(oa, na, i)):
            first_diff = i
            break
    if first_diff < 0:
        return {'status': 'match'}
    return {'status': 'instr_diff', 'first_diff_idx': first_diff,
            'orig_at': list(oa[first_diff]), 'new_at': list(na[first_diff])}


def run_one(py_path):
    os.makedirs(WORK, exist_ok=True)
    base = os.path.splitext(os.path.basename(py_path))[0]
    pyc_path = os.path.join(WORK, base + '.pyc')
    # py_compile
    try:
        py_compile.compile(py_path, cfile=pyc_path, doraise=True)
    except Exception as e:
        return {'py_path': py_path, 'error': f'py_compile failed: {e}'}
    # 反编译
    out_path = os.path.join(WORK, base + '.decompiled.py')
    try:
        with open(out_path, 'w') as outf:
            r = subprocess.run([sys.executable, PYCDC, pyc_path],
                               stdout=outf, stderr=subprocess.PIPE,
                               timeout=90, cwd='/workspace')
        if r.returncode != 0:
            return {'py_path': py_path, 'error': f'pycdc exit {r.returncode}: {r.stderr.decode()[:200]}'}
    except subprocess.TimeoutExpired:
        return {'py_path': py_path, 'error': 'pycdc timeout'}
    # 对比
    with open(py_path) as f:
        orig_src = f.read()
    with open(out_path) as f:
        new_src = f.read()
    try:
        orig_code = compile(orig_src, py_path, 'exec')
        new_code = compile(new_src, out_path, 'exec')
    except SyntaxError as e:
        return {'py_path': py_path, 'error': f'compile failed: {e}', 'new_src_head': new_src[:300]}
    orig_f = first_func(orig_code)
    new_cos = walk_code(new_code)
    new_f = new_cos.get('f')
    if orig_f is None or new_f is None:
        return {'py_path': py_path, 'error': 'cannot find function f'}
    res = compare_one(orig_f, new_f)
    res['py_path'] = py_path
    res['orig_len'] = len(get_instr_list(orig_f))
    res['new_len'] = len(get_instr_list(new_f))
    return res


def main():
    files = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    print(f"[repro] found {len(files)} repro files")
    results = []
    for fp in files:
        r = run_one(fp)
        results.append(r)
        name = os.path.basename(fp)
        if 'error' in r:
            print(f"  {name}: ERROR {r['error']}")
        else:
            st = r['status']
            if st == 'match':
                print(f"  {name}: match (orig={r['orig_len']} new={r['new_len']})  [未复现]")
            elif st == 'len_diff':
                print(f"  {name}: len_diff orig={r['orig_len']} new={r['new_len']} diff={r['diff']:+d}  [复现-指令数差异]")
            else:
                print(f"  {name}: instr_diff @idx{r['first_diff_idx']} orig={r['orig_at']} new={r['new_at']}  [复现-指令差异]")
    # 保存
    out_json = os.path.join(REPRO_DIR, '_repro_results.json')
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[repro] wrote {out_json}")


if __name__ == '__main__':
    main()
