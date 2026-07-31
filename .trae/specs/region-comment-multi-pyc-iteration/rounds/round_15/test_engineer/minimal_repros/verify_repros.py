"""[R15] verify_repros.py - compile + decompile + bytecode-diff each repro.

Usage: python verify_repros.py
Prints, per repro: DEFECT-REPRO / NO-DEFECT / ERROR.

Each repro is compiled to pyc, decompiled via pycdc, recompiled, and its
bytecode compared instruction-by-instruction against the original. A repro
is DEFECT-REPRO when any function's instruction stream differs; NO-DEFECT
when every function matches exactly.
"""
import os
import sys
import types
import py_compile
import marshal
import dis
import traceback

REPRO_DIR = os.path.dirname(os.path.abspath(__file__))


def _normalize_argval(argval):
    """Normalize code-object / .py-path argvals to remove recompilation
    identity noise (co_filename / memory-address differences). Mirrors the
    canonicalization in testqouter/round1/base.py."""
    if isinstance(argval, types.CodeType):
        return f"<code object {argval.co_name}>"
    if isinstance(argval, str):
        low = argval.lower()
        if (low.endswith('.py') or low.endswith('.pyc')) and ('/' in argval or '\\' in argval):
            return os.path.basename(argval)
    return argval


def load_code_co_consts(code):
    yield code.co_name, code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            yield c.co_name, c


def instr_seq(code):
    out = []
    for ins in dis.get_instructions(code):
        out.append((ins.opname, _normalize_argval(ins.argval)))
    return out


def diff_codes(orig_code, dec_code):
    orig_map = {name: c for name, c in load_code_co_consts(orig_code)}
    dec_map = {name: c for name, c in load_code_co_consts(dec_code)}
    matched = 0
    total = 0
    true_diffs = 0
    mismatch_fns = []
    for name, oc in orig_map.items():
        total += 1
        dc = dec_map.get(name)
        if dc is None:
            mismatch_fns.append(name)
            continue
        oi = instr_seq(oc)
        di = instr_seq(dc)
        if oi == di:
            matched += 1
        else:
            true_diffs += abs(len(oi) - len(di)) + sum(
                1 for a, b in zip(oi, di) if a != b)
            mismatch_fns.append(name)
    return matched, total, true_diffs, mismatch_fns


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
        matched, total, diffs, mm_fns = diff_codes(orig_code, dec_code)
        if total > 0 and matched == total and diffs == 0:
            return name, 'NO-DEFECT', f'{matched}/{total} matched'
        return name, 'DEFECT-REPRO', f'{matched}/{total} matched, {diffs} diffs, fns={mm_fns}'
    except Exception as e:
        return name, 'ERROR', f'{type(e).__name__}: {e}'
    finally:
        for p in (pyc_path, pyc_path + '.dec'):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


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
