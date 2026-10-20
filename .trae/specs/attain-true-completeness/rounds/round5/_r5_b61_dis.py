"""[R5] B61 ground-truth dis: r8_dh2_match_guard (r8_11) + r8_dh_match_multi (r8_09).

CPython 3.11.7 dis of the two B61 red units' sources, block-mapped, to
establish the compiler protocol before any fix.
"""
import dis
import importlib.util
import sys

TARGETS = [
    (r'test_repros\round8\r8_11_deep_host_combo2.py', 'r8_dh2_match_guard'),
    (r'test_repros\round8\r8_09_deep_host_combo.py', 'r8_dh_match_multi'),
]

out = open(r'.trae\specs\attain-true-completeness\rounds\round5\_r5_b61_dis.txt',
           'w', encoding='utf-8')


def dump(fn, name):
    out.write(f'===== {name} =====\n')
    code = fn.__code__
    out.write(f'co_consts: {code.co_consts!r}\n')
    out.write(f'co_names: {code.co_names!r}\n')
    out.write(f'co_varnames: {code.co_varnames!r}\n')
    labels = set()
    for ins in dis.get_instructions(code):
        if ins.opname.startswith(('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND')):
            if isinstance(ins.argval, int):
                labels.add(ins.argval)
    cur = None
    for ins in dis.get_instructions(code):
        if ins.offset in labels:
            out.write(f'---- BLOCK@{ins.offset} ----\n')
        tgt = f' ->{ins.argval}' if ('jump' in ins.opname.lower()
                                    or ins.opname == 'FOR_ITER') else ''
        out.write(f'{ins.offset:4d} {ins.opname:30s} {ins.argrepr}{tgt}\n')
    out.write('\n')


for path, fname in TARGETS:
    spec = importlib.util.spec_from_file_location('_t_' + fname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    dump(getattr(mod, fname), fname)
    out.write('\n')

out.close()
print('written _r5_b61_dis.txt')
