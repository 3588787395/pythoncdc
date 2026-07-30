"""R25: run all minimal repros - compile, decompile, recompile, strict-dis compare.

Strict口径: keep NOP/EXTENDED_ARG, skip CACHE only; recursive code-object instruction
sequence comparison (ignore co_filename/runtime addresses).
"""
import sys, os, glob, dis, types, subprocess, marshal
sys.path.insert(0, '/workspace')

REPRO_DIR = '/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_25/test_engineer/minimal_repros'
PYCDC = '/workspace/pycdc.py'


def get_instr_list(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        av = ins.argval
        if isinstance(av, types.CodeType):
            out.append(('CODE', av.co_name, get_instr_list(av)))
        else:
            out.append((ins.opname, av))
    return out


def compare_seq(oa, na, path=''):
    if len(oa) != len(na):
        return f"{path}: len_diff {len(oa)}->{len(na)} ({len(na)-len(oa):+d})"
    for idx, (x, y) in enumerate(zip(oa, na)):
        if x[0] == 'CODE' and y[0] == 'CODE':
            if x[1] != y[1]:
                return f"{path}: code name mismatch {x[1]} vs {y[1]}"
            r = compare_seq(x[2], y[2], path + x[1] + '.')
            if r:
                return r
        elif x != y:
            return f"{path}: idx{idx} DIFF orig={x} new={y}"
    return None


def first_diff_detail(oa, na, path=''):
    """Find first diverging instruction and return a short description."""
    n = min(len(oa), len(na))
    for idx in range(n):
        x, y = oa[idx], na[idx]
        if x[0] == 'CODE' and y[0] == 'CODE':
            if x[1] != y[1]:
                return f"idx{idx} code-name {x[1]} vs {y[1]}"
            r = first_diff_detail(x[2], y[2], path + x[1] + '.')
            if r:
                return f"[in {x[1]}] " + r
        elif x != y:
            return f"idx{idx} orig={x[0]} {str(x[1])[:30]} | new={y[0]} {str(y[1])[:30]}"
    if len(oa) != len(na):
        return f"len_diff {len(oa)}->{len(na)} (first extra/missing at idx{min(len(oa),len(na))})"
    return None


def run_one(src_path):
    name = os.path.basename(src_path)
    pyc_path = src_path + 'c'
    # compile
    import py_compile
    py_compile.compile(src_path, pyc_path, doraise=True)
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    # decompile
    r = subprocess.run([sys.executable, PYCDC, pyc_path],
                       capture_output=True, text=True, timeout=60, cwd='/workspace')
    if r.returncode != 0:
        return name, 'DECOMPILE_FAILED', r.stderr[:200], None, None
    decomp_src = r.stdout
    try:
        new_code = compile(decomp_src, '<d>', 'exec')
    except SyntaxError as e:
        return name, 'RECOMPILE_SYNTAX_ERROR', str(e), decomp_src, None
    oa = get_instr_list(orig_code)
    na = get_instr_list(new_code)
    diff = compare_seq(oa, na)
    detail = first_diff_detail(oa, na) if diff else None
    status = 'IDENTICAL' if diff is None else 'DIFF'
    return name, status, detail, decomp_src, diff


def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    print(f"Found {len(repros)} repros\n")
    results = []
    for rp in repros:
        name, status, detail, decomp_src, diff = run_one(rp)
        results.append((name, status, detail, diff))
        print(f"=== {name} ===")
        print(f"  status: {status}")
        if detail:
            print(f"  first_diff: {detail}")
        if decomp_src:
            # show the decompiled source body (skip header lines)
            lines = decomp_src.splitlines()
            body = '\n'.join(lines[3:]) if len(lines) > 3 else decomp_src
            print(f"  decompiled source:")
            for ln in body.splitlines():
                print(f"    {ln}")
        print()
    # summary
    print("=" * 60)
    print("SUMMARY")
    n_diff = sum(1 for _, s, _, _ in results if s == 'DIFF')
    n_id = sum(1 for _, s, _, _ in results if s == 'IDENTICAL')
    print(f"  DIFF (defect reproduced): {n_diff}/{len(results)}")
    print(f"  IDENTICAL (no defect):    {n_id}/{len(results)}")
    for name, status, detail, diff in results:
        tag = 'REPRODUCED' if status == 'DIFF' else 'no-diff'
        print(f"    [{tag}] {name}: {detail or ''}")


if __name__ == '__main__':
    main()
