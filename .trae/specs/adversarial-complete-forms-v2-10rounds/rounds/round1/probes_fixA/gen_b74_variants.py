# -*- coding: utf-8 -*-
"""FIX-A 判定性实验：B74 幻影 guard 根因隔离。

变体 A（无 import）：case 体只有 if v>0: return wrap(v)
变体 B（有 import）：case 体 import + if（= r10_06 原形态）
各自编译→反编译→字节码 diff，对比幻影 guard 是否只出现在 B。
探针产物落在 probes_fixA/tmp/，不触碰 test_repros/。
"""
import os
import sys
import py_compile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..')))

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
os.makedirs(TMP, exist_ok=True)

VARIANTS = {
    'b74_a_noimport': (
        'def f(rows):\n'
        '    for row in rows:\n'
        '        match row:\n'
        '            case {"k": v}:\n'
        '                if v > 0:\n'
        '                    return wrap(v)\n'
        '    return base_value\n'
    ),
    'b74_b_import': (
        'def f(rows):\n'
        '    for row in rows:\n'
        '        match row:\n'
        '            case {"k": v}:\n'
        '                from m9 import wrap\n'
        '                if v > 0:\n'
        '                    return wrap(v)\n'
        '    return base_value\n'
    ),
}

from scripts import pyc_batch_verify as pbv  # noqa: E402


def main():
    for name, src in VARIANTS.items():
        py_path = os.path.join(TMP, name + '.py')
        pyc_path = os.path.join(TMP, name + '.pyc')
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(src)
        py_compile.compile(py_path, cfile=pyc_path, doraise=True)
        single = pbv.decompile_single(pyc_path)
        if not single['success']:
            print('[%s] decompile FAILED: %s' % (name, single.get('error')))
            continue
        diff = pbv.bytecode_diff(pyc_path, single['ok_py_path'])
        print('[%s] rate=%s matched=%s/%s' % (
            name, diff.get('match_rate'),
            diff.get('matched_functions'), diff.get('total_functions')))
        for m in diff.get('mismatches', []):
            print('   mismatch %s first_diff=%s' % (m.get('name'), m.get('first_diff')))
        with open(single['ok_py_path'], 'r', encoding='utf-8') as f:
            print('--- decompiled:')
            print(f.read())
        print('=' * 50)


if __name__ == '__main__':
    main()
