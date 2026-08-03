"""R21 diag: dump orig vs dec instruction streams for the SECOND `_target` (stream version)."""
import dis
import marshal
import sys
import types

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from testqouter.round1.base import compare_bytecode, get_bytecode_instructions  # noqa: E402
from pycdc import decompile_pyc  # noqa: E402


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out


def dump(code, label, fh):
    fh.write(f'=== {label} ===\n')
    fh.write(f'varnames={code.co_varnames}\n')
    fh.write(f'names={code.co_names}\n')
    fh.write(f'consts={[c for c in code.co_consts if not isinstance(c, types.CodeType)]}\n')
    for i in get_bytecode_instructions(code):
        fh.write(f'  {i.offset:4d} {i.opname:<28} {i.arg!s:>6}  {i.argval!s}\n')
    fh.write('\n')


def main():
    root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
    targets = [c for c in collect(root, []) if c.co_name == '_target']
    t = targets[-1]  # second (stream version)
    print(f'orig _target: varnames={t.co_varnames}')
    # decompile the whole pyc to a temp module source
    src = decompile_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
    with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/_target2_dec.py', 'w', encoding='utf-8') as fh:
        fh.write(src)
    # compile dec source and extract dec _target (last defined)
    dec_root = compile(src, '<dec>', 'exec')
    dec_targets = [c for c in collect(dec_root, []) if c.co_name == '_target']
    print(f'dec _target: varnames={dec_targets[-1].co_varnames}')
    with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/_dis_target2_orig.txt', 'w', encoding='utf-8') as fh:
        dump(t, 'ORIG _target (stream)', fh)
    with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/_dis_target2_dec.txt', 'w', encoding='utf-8') as fh:
        dump(dec_targets[-1], 'DEC _target (stream)', fh)
    cmp = compare_bytecode(t, dec_targets[-1])
    print('compare:', cmp)
    # print first 30 diffs in a readable way
    orig_instrs = list(get_bytecode_instructions(t))
    dec_instrs = list(get_bytecode_instructions(dec_targets[-1]))
    print(f'orig instrs: {len(orig_instrs)}, dec instrs: {len(dec_instrs)}')
    oi, di = iter(orig_instrs), iter(dec_instrs)
    for idx in range(min(len(orig_instrs), len(dec_instrs))):
        o = next(oi)
        d = next(di)
        ok = (o.opname == d.opname and o.arg == d.arg)
        if not ok:
            print(f'diff@{idx}: orig={o.offset}:{o.opname} {o.argval} | dec={d.offset}:{d.opname} {d.argval}')


if __name__ == '__main__':
    main()
