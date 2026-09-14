#!/usr/bin/env python3
"""Round 01 — 最小复现验证器（测试工程师）。

用法:
    D:/Python/python.exe repro.py <case_dir_or_file> ...

对每个用例 .py：
  1. 用当前解释器（必须为 3.11.x，与 pyc magic 3495 对齐）编译为 pyc
  2. 调用 pycdc.decompile_pyc 反编译
  3. 递归比对每个同名 code object 的字节码
  4. 打印 PASS/FAIL 与首个差异

退出码: 全部通过返回 0，否则返回 1。
"""
import os
import sys
import types
from pathlib import Path

def _find_project_root() -> Path:
    """向上回溯直到找到含 pycdc.py 的目录（项目根）。

    本脚本位于 <root>/.trae/specs/<spec>/rounds/round_NN/ 下，硬编码 parents[N]
    极易随目录层级变化而失效，因此改为按锚点文件回溯。
    """
    p = Path(__file__).resolve().parent
    for _ in range(10):
        if (p / 'pycdc.py').is_file():
            return p
        p = p.parent
    raise RuntimeError(f'project root not found from {__file__}')


PROJECT_ROOT = _find_project_root()
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc                      # noqa: E402
from testqouter.round1.base import (                 # noqa: E402
    compare_bytecode, get_bytecode_instructions,
)

import marshal                                        # noqa: E402
import py_compile                                     # noqa: E402
import importlib.util                                 # noqa: E402


def load_code(path):
    if str(path).endswith('.pyc'):
        with open(path, 'rb') as f:
            f.read(16)
            return marshal.load(f)
    cfile = py_compile.compile(str(path), doraise=True, quiet=2)
    if cfile is None:
        cfile = importlib.util.cache_from_source(str(path))
    with open(cfile, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def collect(code, out=None):
    out = {} if out is None else out
    out.setdefault(code.co_name or '<module>', []).append(code)
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            collect(const, out)
    return out


def run_case(src_path: Path, verbose: bool = True):
    """对单个用例 .py 执行 编译→反编译→比对。返回 (ok, detail)。"""
    src_path = Path(src_path).resolve()
    out_py = src_path.with_name(src_path.stem + '_dec.py')
    # decompile_pyc 只接受 pyc：先把用例源码编译成 pyc 再反编译。
    pyc_path = py_compile.compile(str(src_path), doraise=True, quiet=2)
    if pyc_path is None:
        pyc_path = importlib.util.cache_from_source(str(src_path))
    try:
        source = decompile_pyc(str(pyc_path))
    except Exception as e:  # noqa: BLE001
        return False, f'decompile raised {type(e).__name__}: {e}'
    if not source:
        return False, 'decompile returned empty'
    out_py.write_text(source, encoding='utf-8')

    try:
        orig_map = collect(load_code(pyc_path))
        dec_map = collect(load_code(out_py))
    except Exception as e:  # noqa: BLE001
        return False, f'compile/load failed: {type(e).__name__}: {e}'

    problems = []
    for name in sorted(orig_map):
        if name not in dec_map:
            problems.append(f'{name}: MISSING in decompiled')
            continue
        o, d = orig_map[name][0], dec_map[name][0]
        cmp_res = compare_bytecode(o, d)
        if cmp_res.get('match') or cmp_res.get('jump_only'):
            continue
        td = cmp_res.get('true_diffs', [])
        jd = cmp_res.get('jump_diffs', [])
        first = td[0] if td else (jd[0] if jd else None)
        problems.append(
            f'{name}: orig={cmp_res.get("orig_count")} '
            f'dec={cmp_res.get("decomp_count")} '
            f'true_diffs={len(td)} jump_diffs={len(jd)} first={first}'
        )
    if problems:
        return False, '; '.join(problems)
    return True, f'{len(orig_map)} code objects match'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    targets = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            targets.extend(sorted(p.glob('*.py')))
        else:
            targets.append(p)
    targets = [t for t in targets if not t.name.endswith('_dec.py')]

    passed = failed = 0
    for t in targets:
        ok, detail = run_case(t)
        if ok:
            passed += 1
            print(f'PASS  {t.name}  ({detail})')
        else:
            failed += 1
            print(f'FAIL  {t.name}  -> {detail}')
    print(f'\n=== {passed} passed, {failed} failed, '
          f'{passed / (passed + failed):.1%} ===' if (passed + failed) else '')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
