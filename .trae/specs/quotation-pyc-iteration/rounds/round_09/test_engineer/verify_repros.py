#!/usr/bin/env python3
"""R9 minimal repro verifier: py_compile -> pycdc -> bytecode diff (in-memory).

For each repro_09_*.py:
  1. py_compile to .pyc (verify source compiles)
  2. run pycdc.py to decompile .pyc -> .out
  3. compile .out to code object in memory
  4. load .pyc code object in memory
  5. compare bytecode (function-by-function)
  6. classify DEFECT-REPRO / NOT-REPRO / COMPILE-FAIL
"""
import dis
import marshal
import os
import struct
import subprocess
import re

REPRO_DIR = "/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_09/test_engineer/minimal_repros"
PYCDC = "/workspace/pycdc.py"


def run(cmd, timeout=30):
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"


def load_code_from_pyc(path):
    with open(path, "rb") as f:
        data = f.read()
    flags = struct.unpack("<I", data[4:8])[0]
    header = 16 if flags == 0 else 12
    return marshal.loads(data[header:])


def collect_codes(code, prefix="", out=None):
    if out is None:
        out = {}
    name = prefix + code.co_name if prefix else code.co_name
    qn = getattr(code, "co_qualname", None) or name
    out[qn] = code
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            collect_codes(const, qn + ".", out)
    return out


def diff_codes(orig, new):
    out = []
    om = collect_codes(orig)
    nm = collect_codes(new)
    for qn in sorted(set(om) | set(nm)):
        if qn not in om:
            out.append((qn, -1, "new_only", "", ""))
            continue
        if qn not in nm:
            out.append((qn, -1, "lost", "", ""))
            continue
        oi = list(dis.Bytecode(om[qn], show_caches=False))
        ni = list(dis.Bytecode(nm[qn], show_caches=False))
        if len(oi) != len(ni):
            out.append((qn, -1, "length", f"orig={len(oi)}", f"new={len(ni)}"))
        for i in range(min(len(oi), len(ni))):
            a, b = oi[i], ni[i]
            if a.opname != b.opname:
                out.append((qn, a.offset, "opname", f"{a.opname} {a.argrepr}", f"{b.opname} {b.argrepr}"))
            elif repr(a.argval) != repr(b.argval) and a.opname not in ("LOAD_CONST", "MAKE_FUNCTION"):
                out.append((qn, a.offset, "argval", a.argrepr, b.argrepr))
    return out


def classify_repro(py_path, out_path, diffs):
    src_full = open(py_path).read()
    out_full = open(out_path).read() if os.path.exists(out_path) else ""
    try:
        compile(out_full, out_path, "exec")
    except Exception as e:
        return "COMPILE-FAIL", f"decompiled output does not compile: {e}"
    # Strip docstrings: keep only code after the last triple-quoted string
    # to avoid matching defect markers inside docstrings.
    def strip_docstrings(text):
        # Remove triple-quoted strings (""" or ''')
        return re.sub(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', '', text)
    src = strip_docstrings(src_full)
    out = strip_docstrings(out_full)
    defect_markers = []
    has_chained_in_src = bool(re.search(r"\b(if|elif)\s+\d+\s*<=\s*\w+(\.\w+)?\s*<=\s*\d+\s*:", src))
    if has_chained_in_src:
        if not re.search(r"\b(if|elif)\s+\d+\s*<=\s*\w+(\.\w+)?\s*<=\s*\d+\s*:", out):
            defect_markers.append("D3:chained_compare_lost")
    # D7: if/elif assign chain compressed -> bare Expr of nested ternary with `==`
    # Only match if the ternary pattern appears as a statement (indented, no return/log before)
    if re.search(r"\bif\s+\w+\s*==\s*\d+\s*:\s*\n\s+\w+\s*=", src) and \
       re.search(r"(?m)^\s+\w+\s*==\s*\S+\s+if\s+\w+\s*==\s*\d+\s+else", out):
        defect_markers.append("D7:ternary_compress")
    # D8: body collapsed to int(IfExp) with no return
    if re.search(r"\bint\([^)]*==[^)]*if[^)]*else[^)]*\)", out) and "return" not in out:
        defect_markers.append("D8:body_collapse")
    # D10: call merged with IfExp arg (system_log(<IfExp>) or bare IfExp Expr)
    if re.search(r"system_log\([^)]*if[^)]*else[^)]*\)", out):
        defect_markers.append("D10:call_merge")
    if re.search(r"^\s*\w+\([^)]*<=\s*\d+\s+if\s+\w+\s*==\s*\d+\s+else\s+\w+\s*==\s*\d+\)\s*$", out, re.M):
        defect_markers.append("D10:call_merge")
    if re.search(r"^\s*\w+\s*<=\s*\d+\s+if\s+\w+\s*==\s*\d+\s+else\s+\w+\s*==\s*\d+\s*$", out, re.M):
        defect_markers.append("D10:bare_ifexp")
    # D6: try body return lost
    if re.search(r"\btry:\s*\n\s+return\s+", src) and re.search(r"\btry:\s*\n\s+pass", out):
        defect_markers.append("D6:try_body_lost")
    # D6 variant: if body return lost (chained compare body)
    if re.search(r"if\s+\d+\s*<=\s*\w+(\.\w+)?\s*<=\s*\d+\s*:\s*\n\s+return", src) and \
       re.search(r"if\s+\d+\s*:\s*\n\s+pass", out):
        defect_markers.append("D6:if_body_lost")
    # D6 variant: return statement lost -> bare Expr of the returned value
    # (return ({...}, {}) becomes ({...}, {}) as a bare Expr)
    src_returns = re.findall(r"return\s+(\([^)]*\))", src)
    if src_returns:
        # Check if any return value appears as a bare Expr (no return keyword) in output
        for ret_val in src_returns:
            # Escape for regex; ret_val is like "({'error_no': error_no, 'error_info': ''}, {})"
            # We check if the output has this value as a bare Expr (no preceding return on same line)
            bare_pattern = re.escape(ret_val)
            # Look for the value at start of a statement (indented, no return before)
            if re.search(r"(?m)^\s+" + bare_pattern + r"\s*$", out):
                # And confirm the corresponding `return` is missing in output near this region
                defect_markers.append("D6:return_lost_bare_expr")
                break
    has_length_diff = any(d[2] == "length" for d in diffs)
    if defect_markers:
        return "DEFECT-REPRO", ";".join(defect_markers)
    if has_length_diff:
        for qn, off, dt, o, n in diffs:
            if dt == "length" and "orig=" in o and "new=" in n:
                try:
                    oc = int(o.split("=")[1])
                    nc = int(n.split("=")[1])
                    if oc > 0 and nc < oc * 0.7:
                        return "DEFECT-REPRO", f"length_diff:{qn}:{o}->{n}"
                except Exception:
                    pass
    if diffs:
        return "NOT-REPRO", f"minor_diffs:{len(diffs)}"
    return "NOT-REPRO", "no_diffs"


def main():
    py_files = sorted(
        f for f in os.listdir(REPRO_DIR) if f.startswith("repro_09_") and f.endswith(".py")
    )
    summary = []
    for pyf in py_files:
        py_path = os.path.join(REPRO_DIR, pyf)
        stem = pyf[:-3]
        pyc_path = os.path.join(REPRO_DIR, stem + ".pyc")
        out_path = os.path.join(REPRO_DIR, stem + ".out")
        err_path = os.path.join(REPRO_DIR, stem + ".err")
        diff_path = os.path.join(REPRO_DIR, stem + ".diff")
        rc, so, se = run(f"cd /workspace && python -c \"import py_compile; py_compile.compile('{py_path}', '{pyc_path}', doraise=True)\"")
        if rc != 0:
            summary.append((pyf, "PY_COMPILE_FAIL", se.strip()[:200], "0"))
            continue
        rc, so, se = run(f"cd /workspace && timeout 20 python {PYCDC} {pyc_path}")
        with open(out_path, "w") as f:
            f.write(so)
        with open(err_path, "w") as f:
            f.write(se)
        try:
            new_code = compile(so, out_path, "exec")
        except Exception as e:
            summary.append((pyf, "COMPILE-FAIL", f"out compile: {e}", "0"))
            continue
        try:
            orig_code = load_code_from_pyc(pyc_path)
            diffs = diff_codes(orig_code, new_code)
        except Exception as e:
            summary.append((pyf, "DIFF_FAIL", str(e)[:200], "0"))
            continue
        with open(diff_path, "w") as f:
            for qn, off, dt, o, n in diffs:
                f.write(f"{qn} offset={off} type={dt} orig={o!r} new={n!r}\n")
        status, reason = classify_repro(py_path, out_path, diffs)
        summary.append((pyf, status, reason, f"diffs={len(diffs)}"))
    with open("/tmp/r9_repro_summary.txt", "w") as f:
        f.write("repro\tstatus\treason\tdiff_count\n")
        for pyf, status, reason, dc in summary:
            f.write(f"{pyf}\t{status}\t{reason}\t{dc}\n")
    print("repro\tstatus\treason\tdiff_count")
    for row in summary:
        print("\t".join(row))


if __name__ == "__main__":
    main()
