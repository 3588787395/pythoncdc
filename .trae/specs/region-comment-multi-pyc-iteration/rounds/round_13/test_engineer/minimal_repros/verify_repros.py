"""[R13] verify_repros.py - compile + decompile + bytecode-diff each repro.

Usage: python verify_repros.py
Prints, per repro: DEFECT-REPRO / NO-DEFECT / ERROR.
"""
import os
import sys
import py_compile
import marshal
import dis
import traceback

REPRO_DIR = os.path.dirname(os.path.abspath(__file__))


def load_code_co_consts(code):
    yield code.co_name, code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            yield c.co_name, c


def instr_seq(code):
    out = []
    for ins in dis.get_instructions(code):
        out.append((ins.opname, ins.argval))
    return out


def diff_codes(orig_code, dec_code):
    orig_map = {name: c for name, c in load_code_co_consts(orig_code)}
    dec_map = {name: c for name, c in load_code_co_consts(dec_code)}
    matched = 0
    total = 0
    true_diffs = 0
    for name, oc in orig_map.items():
        total += 1
        dc = dec_map.get(name)
        if dc is None:
            continue
        oi = instr_seq(oc)
        di = instr_seq(dc)
        if oi == di:
            matched += 1
        else:
            true_diffs += abs(len(oi) - len(di)) + sum(
                1 for a, b in zip(oi, di) if a != b)
    return matched, total, true_diffs


def run_one(repro_path):
    name = os.path.basename(repro_path)
    ok_path = repro_path[:-3] + 'OK.py'
    pyc_path = repro_path + 'c'
    try:
        py_compile.compile(repro_path, doraise=True, cfile=pyc_path)
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        sys.path.insert(0, os.path.dirname(REPRO_DIR))
        sys.path.insert(0, os.path.abspath('.'))
        from pycdc import decompile_pyc
        src = decompile_pyc(pyc_path)
        sys.path.pop(0)
        sys.path.pop(0)
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(src)
        dec_pyc = pyc_path + '.dec'
        try:
            py_compile.compile(ok_path, doraise=True, cfile=dec_pyc)
        except py_compile.PyCompileError as e:
            return name, 'DEFECT-REPRO', f'compile-fail: {e}'
        with open(dec_pyc, 'rb') as f:
            f.read(16)
            dec_code = marshal.load(f)
        matched, total, diffs = diff_codes(orig_code, dec_code)
        if total > 0 and matched == total and diffs == 0:
            return name, 'NO-DEFECT', f'{matched}/{total} matched'
        return name, 'DEFECT-REPRO', f'{matched}/{total} matched, {diffs} diffs'
    except Exception as e:
        return name, 'ERROR', f'{type(e).__name__}: {e}'


def main():
    repros = sorted(
        os.path.join(REPRO_DIR, f) for f in os.listdir(REPRO_DIR)
        if f.startswith('repro_') and f.endswith('.py') and not f.endswith('OK.py')
    )
    print(f'Found {len(repros)} repros')
    defect = 0
    nodefect = 0
    err = 0
    for r in repros:
        name, status, info = run_one(r)
        print(f'  {name:60s} {status:14s} {info}')
        if status == 'DEFECT-REPRO':
            defect += 1
        elif status == 'NO-DEFECT':
            nodefect += 1
        else:
            err += 1
    print(f'\nSummary: {defect} DEFECT-REPRO, {nodefect} NO-DEFECT, {err} ERROR')


if __name__ == '__main__':
    main()
