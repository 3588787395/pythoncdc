"""验证 R07 minimal_repros/ 下所有 repro_*.py 是否触发反编译字节码不一致。

流程（每个 repro）：
  1. py_compile 编译原 .py 为 .pyc
  2. pycdc.decompile_pyc 反编译 .pyc -> 反编译源码
  3. compile() 重编译反编译源码 -> code object
  4. compare_bytecode(原 code object, 重编译 code object) 逐同名函数比对
  5. 输出 match=True/False + 最严重不一致函数 + 差异数

退出码：0=全部成功运行（不论 match），1=脚本异常。
在 stdout 末尾打印 JSON 行 VERIFY_RESULT 供报告归档。
"""
import os
import sys
import json
import glob
import types
import marshal
import py_compile
import tempfile

_here = os.path.dirname(os.path.abspath(__file__))
ROOT = _here
for _ in range(10):
    if os.path.exists(os.path.join(ROOT, 'pycdc.py')):
        break
    parent = os.path.dirname(ROOT)
    if parent == ROOT:
        break
    ROOT = parent
sys.path.insert(0, ROOT)

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode


def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract_code_objects(code_obj, out=None):
    if out is None:
        out = {}
    name = code_obj.co_name or '<module>'
    out[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            extract_code_objects(const, out)
    return out


def verify_one(py_path):
    name = os.path.basename(py_path)
    result = {'name': name, 'match': False, 'error': None,
              'orig_count': 0, 'decomp_count': 0,
              'true_diffs': 0, 'jump_diffs': 0, 'first_diff': None,
              'mismatch_fn': None}

    tmpdir = tempfile.mkdtemp(prefix='r08_repro_')
    pyc_path = os.path.join(tmpdir, os.path.splitext(name)[0] + '__c.pyc')
    try:
        py_compile.compile(py_path, pyc_path, doraise=True, quiet=2)
    except Exception as e:
        result['error'] = f'compile_orig_failed: {type(e).__name__}: {e}'
        return result

    orig_code = load_pyc_code(pyc_path)
    try:
        decompiled_src = decompile_pyc(pyc_path)
    except Exception as e:
        result['error'] = f'decompile_failed: {type(e).__name__}: {e}'
        return result
    try:
        decomp_code = compile(decompiled_src, '<decompiled>', 'exec')
    except SyntaxError as e:
        result['error'] = f'syntax_error_in_decompiled: {type(e).__name__}: {e}'
        result['decompiled_snippet'] = decompiled_src[:300]
        return result

    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = sorted(set(orig_map.keys()) & set(decomp_map.keys()))

    worst = None
    real_mismatch = False
    for fn_name in common:
        cmp = compare_bytecode(orig_map[fn_name], decomp_map[fn_name])
        if not cmp.get('match', False):
            td = len(cmp.get('true_diffs', []))
            jd = len(cmp.get('jump_diffs', []))
            fd = (cmp.get('true_diffs') or cmp.get('jump_diffs') or [None])[0]
            is_identity_noise = (
                fn_name == '<module>'
                and td + jd == 1
                and fd and fd.get('orig_op') == 'LOAD_CONST'
                and fd.get('decomp_op') == 'LOAD_CONST'
                and isinstance(fd.get('orig_arg'), types.CodeType)
            )
            if is_identity_noise:
                continue
            real_mismatch = True
            if worst is None or td + jd > worst['true_diffs'] + worst['jump_diffs']:
                worst = {
                    'fn': fn_name,
                    'orig_count': cmp.get('orig_count', 0),
                    'decomp_count': cmp.get('decomp_count', 0),
                    'true_diffs': td,
                    'jump_diffs': jd,
                    'first_diff': fd,
                }

    result['match'] = not real_mismatch
    if worst:
        result['orig_count'] = worst['orig_count']
        result['decomp_count'] = worst['decomp_count']
        result['true_diffs'] = worst['true_diffs']
        result['jump_diffs'] = worst['jump_diffs']
        result['first_diff'] = worst['first_diff']
        result['mismatch_fn'] = worst['fn']
    else:
        result['orig_count'] = len(orig_map)
        result['decomp_count'] = len(decomp_map)

    try:
        os.remove(pyc_path)
        os.rmdir(tmpdir)
    except OSError:
        pass
    return result


def main():
    repros = sorted(glob.glob(os.path.join(_here, 'repro_*.py')))
    if not repros:
        print('[verify_repros] no repro_*.py found')
        return 0

    print('=' * 78)
    print(f'verifying {len(repros)} minimal repros')
    print('=' * 78)

    summary = []
    triggered = 0
    for py_path in repros:
        r = verify_one(py_path)
        nm = r['name']
        if r['error']:
            status = f'ERROR   : {r["error"]}'
            verdict = 'ERROR'
        elif r['match']:
            status = f'match=True (fns={r["orig_count"]})  [NO-DEFECT]'
            verdict = 'NO-DEFECT'
        else:
            fn = r.get('mismatch_fn', '?')
            status = (f'match=False [fn={fn}] (orig={r["orig_count"]} decomp={r["decomp_count"]} '
                      f'true_diffs={r["true_diffs"]} jump_diffs={r["jump_diffs"]})  [DEFECT-REPRO]')
            verdict = 'DEFECT-REPRO'
            triggered += 1
        print(f'  {nm}')
        print(f'    {status}')
        if r['first_diff']:
            fd = r['first_diff']
            fd_show = {k: (f'<code object {v.co_name}>' if isinstance(v, types.CodeType) else v)
                       for k, v in fd.items()}
            print(f'    first_diff: {fd_show}')
        if r.get('decompiled_snippet'):
            print(f'    decompiled_snippet: {r["decompiled_snippet"]!r}')
        summary.append({'name': nm, 'verdict': verdict, 'match': r['match'],
                        'mismatch_fn': r.get('mismatch_fn'),
                        'true_diffs': r['true_diffs'], 'jump_diffs': r['jump_diffs'],
                        'first_diff': r['first_diff'] if r['first_diff'] else None,
                        'error': r['error']})

    print('=' * 78)
    print(f'summary: {len(repros)} repros, DEFECT-REPRO={triggered}, NO-DEFECT={len(repros) - triggered}')
    print('=' * 78)
    print('VERIFY_RESULT ' + json.dumps(summary, default=str, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())

