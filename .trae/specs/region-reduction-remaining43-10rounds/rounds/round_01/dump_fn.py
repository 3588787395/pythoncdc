#!/usr/bin/env python3
"""Round 01 — 单函数字节码导出工具（测试工程师）。

用法:
    D:/Python/python.exe dump_fn.py <pyc_or_py> <func_name>

从 pyc（跳过 16 字节头）或已编译的 .py 中递归提取同名 code object，
用 dis 逐条打印指令，供人工/脚本做字节码 diff。
"""
import dis
import importlib.util
import marshal
import py_compile
import sys
import types


def load_code(path):
    """从 pyc 或 .py 加载顶层 code object。"""
    if path.endswith('.pyc'):
        with open(path, 'rb') as f:
            f.read(16)
            return marshal.load(f)
    # .py -> 用当前解释器编译后加载
    cfile = py_compile.compile(path, doraise=True, quiet=2)
    if cfile is None:
        cfile = importlib.util.cache_from_source(path)
    with open(cfile, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def collect(code, out=None):
    """递归收集 code object，按 co_name 分组（保持嵌套顺序）。"""
    out = {} if out is None else out
    out.setdefault(code.co_name or '<module>', []).append(code)
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            collect(const, out)
    return out


def main():
    path, name = sys.argv[1], sys.argv[2]
    codes = collect(load_code(path))
    cands = codes.get(name, [])
    print(f'# {name}: {len(cands)} code obj(s) in {path}')
    for i, c in enumerate(cands):
        instrs = list(dis.get_instructions(c))
        print(f'--- obj{i} co_name={c.co_name} nconsts={len(c.co_consts)} '
              f'ninstrs={len(instrs)} ---')
        for ins in instrs:
            print(f'{ins.offset:4d}|{ins.opname}|{ins.argrepr}')


if __name__ == '__main__':
    main()
