#!/usr/bin/env python3
"""最小复现批量验证器（Round 02 / 测试工程师）。

对同目录下每个 repro_NN.py 执行：
    src = <源码>
    code_orig  = compile(src,                  path, 'exec')   # 原始字节码
    out        = decompile(src, path)                          # 反编译产出的源码
    code_dec   = compile(out,                  path, 'exec')   # 回编译字节码
    → 递归遍历两棵 code object 树，逐一比对 co_code

判定：所有嵌套 code object 的 co_code 完全一致 → PASS，否则 FAIL。
另外给出「结构化」诊断信息（过滤 NOP/EXTENDED_ARG/PRECALL 后逐指令比对），
仅用于定位，不作为判定依据。

用法（必须用 Python 3.11.7，pyc 魔数 a70d0d0a）：
    D:/Python/python.exe run_repros.py            # 跑全部
    D:/Python/python.exe run_repros.py 01 03      # 只跑指定编号
    D:/Python/python.exe run_repros.py -v         # 打印反编译输出
"""
import dis
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    """向上找到同时含 core/ 与 pycdc.py 的项目根。"""
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(f'未找到项目根目录: {start}')


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import decompile  # noqa: E402

NOISE_OPS = {'NOP', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}


def walk(co):
    """按 co_consts 顺序深度优先展开所有嵌套 code object。"""
    yield co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c)


def qual(co):
    return co.co_name


def instrs(co):
    return [i for i in dis.get_instructions(co) if i.opname not in NOISE_OPS]


def _fmt(i):
    """指令的可比表示：code object 只留名字（地址/文件名为布局噪声）。"""
    if isinstance(i.argval, types.CodeType):
        return f'{i.opname} <code object {i.argval.co_name}>'
    s = i.argrepr.strip()
    return f'{i.opname} {s}' if s else i.opname


def first_instr_diff(a, b):
    """返回 (idx, orig_repr, dec_repr) 或 None。"""
    ia, ib = instrs(a), instrs(b)
    n = max(len(ia), len(ib))
    for i in range(n):
        ra = _fmt(ia[i]) if i < len(ia) else '<EOF>'
        rb = _fmt(ib[i]) if i < len(ib) else '<EOF>'
        if ra != rb:
            return i, ra, rb
    return None


def check_source(src, filename, verbose=False):
    """返回 (ok: bool, detail: str)。"""
    try:
        code_orig = compile(src, filename, 'exec')
    except SyntaxError as e:
        return False, f'{type(e).__name__}: {e}'
    try:
        out = decompile(src, filename)
    except Exception as e:
        return False, f'反编译异常 {type(e).__name__}: {e}'
    if verbose:
        print('---- decompile output ----')
        print(out)
        print('--------------------------')
    try:
        code_dec = compile(out, filename, 'exec')
    except SyntaxError as e:
        return False, f'反编译产物无法编译 {type(e).__name__}: {e}'

    la, lb = list(walk(code_orig)), list(walk(code_dec))
    if len(la) != len(lb):
        na = [c.co_name for c in la]
        nb = [c.co_name for c in lb]
        return False, (f'code object 数量/顺序不同 orig={na} decomp={nb}')

    for x, y in zip(la, lb):
        if x.co_code != y.co_code:
            d = first_instr_diff(x, y)
            if d is None:
                return False, (f'{qual(x)}: co_code 不同但指令流一致（仅跳转位移不同）')
            i, ra, rb = d
            return False, f'{qual(x)} 指令#{i}: 原={ra!r} 反编译={rb!r}'
        if x.co_names != y.co_names:
            return False, f'{qual(x)}: co_names 不同 {x.co_names} vs {y.co_names}'
        if x.co_varnames != y.co_varnames:
            return False, f'{qual(x)}: co_varnames 不同 {x.co_varnames} vs {y.co_varnames}'
    return True, ''


def check_repro(path, verbose=False):
    """返回 (ok: bool, detail: str)。"""
    return check_source(path.read_text(encoding='utf-8'), str(path), verbose)


def family_of(src):
    """从首行注释里取出 family 编号，如 'F3'。"""
    line = src.splitlines()[0] if src else ''
    if 'family:' in line:
        return line.split('family:', 1)[1].strip().split()[0]
    return ''


# 对照组：已知能正确往返的源码，用于证明比对器本身没有过于严格。
CONTROLS = {
    'control_simple_assign': 'a = A()\na.x = 5\n',
    'control_if_else_return': 'def f(x):\n    if x:\n        return 1\n    return 2\n',
    'control_try_except': ('def f(x):\n'
                           '    try:\n'
                           '        return int(x)\n'
                           '    except ValueError:\n'
                           '        return None\n'),
    'control_aug_attr': ('def f(self, t):\n'
                         '    self.cost += t.cost\n'
                         '    return self\n'),
}


def run_controls():
    ok = 0
    for name, src in CONTROLS.items():
        fname = str(HERE / f'_control_{name}.py')  # 仅作为 co_filename，不落盘
        good, detail = check_source(src, fname)
        print(f'[{"PASS" if good else "FAIL"}] {name:22s} (对照) {detail}')
        ok += good
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    verbose = '-v' in sys.argv[1:]
    files = sorted(HERE.glob('repro_*.py'))
    if args:
        files = [f for f in files if any(a in f.name for a in args)]
    if not files:
        print('未找到 repro_*.py')
        return 1

    npass = nfail = 0
    failed = []
    for f in files:
        ok, detail = check_repro(f, verbose)
        fam = family_of(f.read_text(encoding='utf-8'))
        tag = 'PASS' if ok else 'FAIL'
        if ok:
            npass += 1
        else:
            nfail += 1
            failed.append(f.name)
        print(f'[{tag}] {f.name:16s} {fam:4s} {detail}')
    print('-' * 100)
    print(f'复现用例 总计 {len(files)}   PASS {npass}   FAIL {nfail}')
    if failed:
        print('FAIL 列表: ' + ' '.join(failed))
    print('-' * 100)
    print(f'对照组（已知可正确往返，验证比对器不过严）共 {len(CONTROLS)} 个')
    cok = run_controls()
    print(f'对照组 PASS {cok}/{len(CONTROLS)}')
    return 0 if nfail == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
