#!/usr/bin/env python3
"""R102 只读二分探针：R98 反编译核心 vs HEAD 反编译核心，固定 HEAD 比较器。

对关键争议 pyc，分别用 R98 与 HEAD 的 core/ 生成源码，
再用当前 HEAD 的 compare_bytecode 判定，区分「真回归」与「索引陈旧」。
不修改工作区任何文件；OK.py 写到临时目录。
"""
import marshal
import py_compile
import sys
import threading
import types
from pathlib import Path

MAIN = Path(r'F:\Downloads\pythoncdc-main')
R98 = Path(r'd:\Temp\opencode\wt_102_r98')

# 先以 MAIN 身份导入比较器（进入 sys.modules 后不再受 path 影响）
sys.path.insert(0, str(MAIN))
from testqouter.round1.base import compare_bytecode  # noqa: E402

# 再把 R98 根放到最前，使后续 import pycdc 解析到 R98
sys.path.insert(0, str(R98))
import pycdc as pycdc_r98  # noqa: E402

sys.path.pop(0)
sys.path.insert(0, str(MAIN))
import pycdc as pycdc_head  # noqa: E402


def _load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def _extract(code):
    out = {}

    def walk(c):
        out[c.co_name or '<module>'] = c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                walk(k)
    walk(code)
    return out


def decompile_with_timeout(decompile_fn, pyc, timeout=60):
    box = {'src': None, 'err': None}

    def worker():
        try:
            box['src'] = decompile_fn(str(pyc))
        except Exception as e:  # noqa: BLE001
            box['err'] = f'{type(e).__name__}: {e}'
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    return box['src'], box['err']


def measure(decompiler, tag, pyc):
    src, err = decompile_with_timeout(decompiler.decompile_pyc, pyc)
    if src is None:
        print(f'  {tag}: DECOMPILE-FAIL {err}')
        return None
    tmp_py = Path(r'd:\Temp\opencode') / (
        pyc.stem + f'_{tag}_OK.py')
    tmp_py.write_text(src, encoding='utf-8')
    cfile = py_compile.compile(str(tmp_py), doraise=True, quiet=2)
    if cfile is None:
        import importlib.util
        cfile = importlib.util.cache_from_source(str(tmp_py))
    om = _extract(_load_code(str(pyc)))
    dm = _extract(_load_code(cfile))
    total = len(om)
    matched = 0
    mism = []
    for name in sorted(set(om) & set(dm)):
        cmp = compare_bytecode(om[name], dm[name])
        if cmp.get('match') or cmp.get('jump_only'):
            matched += 1
        else:
            td = cmp.get('true_diffs', [])
            mism.append((name, len(td), cmp.get('orig_count'), cmp.get('decomp_count')))
    rate = matched / total if total else 0.0
    print(f'  {tag}: total={total} matched={matched} rate={rate:.4f} '
          f'mismatched={sorted(n for n, _, _, _ in mism)[:6]}')
    return rate, matched, total


TARGETS = [
    MAIN / 'site-packages/IQEngine/interface.pyc',
    MAIN / 'site-packages/IQEngine/utils/cache_storage.pyc',
    MAIN / 'site-packages/IQEngine/data/data_proxy.pyc',
    MAIN / 'site-packages/fly/simtradding/flyAccount.pyc',
    MAIN / 'site-packages/IQCommon/data/api_data.pyc',
]

if __name__ == '__main__':
    for pyc in TARGETS:
        print(f'== {pyc.name} ({pyc.parent.name}) ==')
        measure(pycdc_r98, 'R98', pyc)
        measure(pycdc_head, 'HEAD', pyc)
