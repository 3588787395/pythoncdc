"""验证 minimal_repros/ 下所有 repro_*.py 是否触发反编译字节码不一致。

流程（每个 repro）：
  1. py_compile 编译原 .py 为 .pyc
  2. pycdc.decompile_pyc 反编译 .pyc -> 反编译源码
  3. compile() 重编译反编译源码 -> code object
  4. compare_bytecode(原 code object, 重编译 code object)
  5. 输出 match=True/False + 差异数

退出码：0=全部成功运行（不论 match），1=脚本异常。
"""
import os
import sys
import glob
import types
import marshal
import py_compile
import tempfile

# 项目根目录加入 sys.path（向上查找直至找到 pycdc.py）
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
        f.read(16)  # 跳过 16 字节头
        return marshal.load(f)


def extract_code_objects(code_obj, out=None):
    """递归提取所有 code object，按 co_name 命名。<module> 用 '<module>'。"""
    if out is None:
        out = {}
    name = code_obj.co_name or '<module>'
    out[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            extract_code_objects(const, out)
    return out


def verify_one(py_path):
    """验证单个 repro .py，返回结果 dict。"""
    name = os.path.basename(py_path)
    result = {'name': name, 'match': False, 'error': None,
              'orig_count': 0, 'decomp_count': 0,
              'true_diffs': 0, 'jump_diffs': 0, 'first_diff': None}

    tmpdir = tempfile.mkdtemp(prefix='repro_verify_')
    pyc_path = os.path.join(tmpdir, name + 'c')

    # 1. 编译原 .py
    try:
        py_compile.compile(py_path, pyc_path, doraise=True, quiet=2)
    except Exception as e:
        result['error'] = f'compile_orig_failed: {type(e).__name__}: {e}'
        return result

    orig_code = load_pyc_code(pyc_path)

    # 2. 反编译
    try:
        decompiled_src = decompile_pyc(pyc_path)
    except Exception as e:
        result['error'] = f'decompile_failed: {type(e).__name__}: {e}'
        return result

    # 3. 重编译反编译源码
    try:
        decomp_code = compile(decompiled_src, '<decompiled>', 'exec')
    except SyntaxError as e:
        result['error'] = f'syntax_error_in_decompiled: {type(e).__name__}: {e}'
        result['decompiled_snippet'] = decompiled_src[:300]
        return result

    # 4. 递归提取并逐个比对同名 code object（函数级比对，避免模块级 code object 身份噪声）
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = sorted(set(orig_map.keys()) & set(decomp_map.keys()))

    worst = None  # 记录最严重的不一致
    real_mismatch = False
    for fn_name in common:
        cmp = compare_bytecode(orig_map[fn_name], decomp_map[fn_name])
        if not cmp.get('match', False):
            td = len(cmp.get('true_diffs', []))
            jd = len(cmp.get('jump_diffs', []))
            fd = (cmp.get('true_diffs') or cmp.get('jump_diffs') or [None])[0]
            # 跳过纯 code-object 身份差异的模块级噪声（first_diff 为 LOAD_CONST code object）
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
            if worst is None or td > worst['true_diffs']:
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
        # 全部一致时取函数数统计
        result['orig_count'] = len(orig_map)
        result['decomp_count'] = len(decomp_map)

    # 清理临时 pyc
    try:
        os.remove(pyc_path)
        os.rmdir(tmpdir)
    except OSError:
        pass

    return result


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repros = sorted(glob.glob(os.path.join(here, 'repro_*.py')))
    if not repros:
        print('[verify_repros] 未找到 repro_*.py 文件')
        return 0

    print('=' * 78)
    print(f'验证 {len(repros)} 个最小复现实例')
    print('=' * 78)

    triggered = 0
    for py_path in repros:
        r = verify_one(py_path)
        name = r['name']
        if r['error']:
            status = f'ERROR   : {r["error"]}'
        elif r['match']:
            status = f'match=True (fns={r["orig_count"]})  [未触发缺陷]'
        else:
            fn = r.get('mismatch_fn', '?')
            status = (f'match=False [fn={fn}] (orig={r["orig_count"]} decomp={r["decomp_count"]} '
                      f'true_diffs={r["true_diffs"]} jump_diffs={r["jump_diffs"]})  [触发缺陷]')
            triggered += 1
        print(f'  {name}')
        print(f'    {status}')
        if r['first_diff']:
            fd = r['first_diff']
            # 截断 code object 类型的 arg 以避免打印内存地址
            fd_show = {k: (f'<code object {v.co_name}>' if isinstance(v, types.CodeType) else v)
                       for k, v in fd.items()}
            print(f'    first_diff: {fd_show}')
        if r.get('decompiled_snippet'):
            print(f'    decompiled_snippet: {r["decompiled_snippet"]!r}')

    print('=' * 78)
    print(f'汇总: 共 {len(repros)} 个实例, 触发缺陷 {triggered} 个, 未触发 {len(repros) - triggered} 个')
    print('=' * 78)
    return 0


if __name__ == '__main__':
    sys.exit(main())
