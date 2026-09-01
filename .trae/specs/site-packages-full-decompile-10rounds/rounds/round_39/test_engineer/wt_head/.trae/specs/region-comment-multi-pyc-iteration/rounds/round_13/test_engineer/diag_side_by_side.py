#!/usr/bin/env python3
"""R13 diagnostic: side-by-side dump for get_pre_date and other Pattern B cases."""
import dis
import marshal
import os
import py_compile
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc


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


def main():
    pyc_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedata.pyc')
    ok_py_path = str(PROJECT_ROOT / 'site-packages/IQCommon/api/klinedataOK.py')

    source = decompile_pyc(pyc_path)
    with open(ok_py_path, 'w', encoding='utf-8') as f:
        f.write(source)

    orig_code = load_pyc_code(pyc_path)
    orig_map = extract_code_objects(orig_code)

    cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)
    decomp_map = extract_code_objects(decomp_code)

    # Functions to inspect (Pattern B + nearby candidates)
    targets = [
        'get_pre_date',
        'get_kline_by_date_one',
        'get_history_date_and_count_ifalse',
        'get_history_new',
        'get_multiminute_his_data_by_date',
    ]
    out_dir = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_13/test_engineer'
    for name in targets:
        if name not in orig_map or name not in decomp_map:
            print(f'[SKIP] {name} not in both maps')
            continue
        orig_instrs = list(dis.get_instructions(orig_map[name]))
        decomp_instrs = list(dis.get_instructions(decomp_map[name]))
        with open(out_dir / f'_sidebyside_{name}.txt', 'w', encoding='utf-8') as f:
            f.write(f'# side-by-side {name} (orig={len(orig_instrs)} decomp={len(decomp_instrs)})\n')
            f.write(f'# {"IDX":>4} | {"ORIG":<60} | {"DECOMP":<60}\n')
            f.write('-' * 130 + '\n')
            max_len = max(len(orig_instrs), len(decomp_instrs))
            for i in range(max_len):
                o = orig_instrs[i] if i < len(orig_instrs) else None
                d = decomp_instrs[i] if i < len(decomp_instrs) else None
                ostr = f'{o.offset:4} {o.opname} {o.argrepr}' if o else '<none>'
                dstr = f'{d.offset:4} {d.opname} {d.argrepr}' if d else '<none>'
                mark = ' ' if o and d and o.opname == d.opname and o.argrepr == d.argrepr else '*'
                f.write(f'{mark} {i:4} | {ostr:<60} | {dstr:<60}\n')
        print(f'[R13-DIAG] side-by-side for {name} saved')

    # Also dump the OK.py source for get_pre_date for inspection
    import ast
    with open(ok_py_path, 'r', encoding='utf-8') as f:
        src = f.read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in targets:
            with open(out_dir / f'_ast_{node.name}.py', 'w', encoding='utf-8') as f:
                f.write(f'# AST dump for {node.name}\n')
                f.write(ast.unparse(node))
                f.write('\n')
            print(f'[R13-DIAG] AST dump for {node.name} saved')


if __name__ == '__main__':
    main()
