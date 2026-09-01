#!/usr/bin/env python3
"""R8 bytecode diff: compare /tmp/r8_decompiled.py recompiled vs /workspace/quotation.pyc.

Walks both code objects recursively by qualname. For each function, compares
the disassembled instruction list (opname + argrepr) and reports mismatches.
"""
import dis
import marshal
import struct
import sys
from collections import defaultdict


def load_code_from_pyc(path):
    with open(path, "rb") as f:
        data = f.read()
    # Python 3.7+: magic(4) + flags(4) + [timestamp(4) + size(4) if flags==0] + code
    flags = struct.unpack("<I", data[4:8])[0]
    if flags == 0:
        header = 16
    else:
        header = 12
    return marshal.loads(data[header:])


def load_code_from_py(path):
    src = open(path, "r").read()
    return compile(src, path, "exec")


def collect_codes(code, prefix="", out=None):
    if out is None:
        out = {}
    name = prefix + code.co_name if prefix else code.co_name
    qn = getattr(code, "co_qualname", None) or name
    out[qn] = code
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            sub_prefix = qn + "."
            collect_codes(const, sub_prefix, out)
    return out


def diff_function(name, orig_code, new_code):
    """Return list of (offset, orig_instr, new_instr, diff_type) tuples."""
    out = []
    orig_insts = list(dis.Bytecode(orig_code, show_caches=False))
    new_insts = list(dis.Bytecode(new_code, show_caches=False))
    if len(orig_insts) != len(new_insts):
        out.append(
            (
                -1,
                f"INSTRUCTION_COUNT={len(orig_insts)}",
                f"INSTRUCTION_COUNT={len(new_insts)}",
                "length_mismatch",
            )
        )
    n = min(len(orig_insts), len(new_insts))
    for i in range(n):
        a = orig_insts[i]
        b = new_insts[i]
        if a.opname != b.opname:
            out.append(
                (
                    a.offset,
                    f"{a.opname} {a.argrepr}",
                    f"{b.opname} {b.argrepr}",
                    "opname_mismatch",
                )
            )
        elif a.argval != b.argval and a.opname not in (
            "LOAD_CONST",
            "MAKE_FUNCTION",
        ):
            if repr(a.argval) != repr(b.argval):
                out.append(
                    (
                        a.offset,
                        f"{a.opname} {a.argrepr}",
                        f"{b.opname} {b.argrepr}",
                        "argval_mismatch",
                    )
                )
    return out


def main():
    orig = load_code_from_pyc("/workspace/quotation.pyc")
    try:
        new = load_code_from_py("/tmp/r8_decompiled.py")
    except Exception as e:
        print(f"COMPILE_FAIL: {e}")
        sys.exit(2)

    orig_map = collect_codes(orig)
    new_map = collect_codes(new)

    detail_lines = []
    summary_lines = []
    diff_count_by_type = defaultdict(int)
    diff_count_by_func = defaultdict(int)
    total_funcs = 0
    diff_funcs = 0
    lost_funcs = 0
    new_only_funcs = 0

    all_names = set(orig_map.keys()) | set(new_map.keys())
    for name in sorted(all_names):
        if name not in orig_map:
            summary_lines.append(f"[NEW-ONLY] {name}: present in new only")
            new_only_funcs += 1
            continue
        if name not in new_map:
            summary_lines.append(f"[LOST] {name}: missing in new (lost function body)")
            lost_funcs += 1
            continue
        total_funcs += 1
        diffs = diff_function(name, orig_map[name], new_map[name])
        if diffs:
            diff_funcs += 1
            detail_lines.append(f"=== FUNCTION {name} ===")
            for offset, o, n, dt in diffs:
                diff_count_by_type[dt] += 1
                diff_count_by_func[name] += 1
                detail_lines.append(f"  offset={offset} type={dt}")
                detail_lines.append(f"    orig: {o}")
                detail_lines.append(f"    new : {n}")
            detail_lines.append("")

    summary_lines.append("")
    summary_lines.append("=== SUMMARY ===")
    summary_lines.append(f"total_functions_compared: {total_funcs}")
    summary_lines.append(f"functions_with_diffs: {diff_funcs}")
    summary_lines.append(f"lost_functions: {lost_funcs}")
    summary_lines.append(f"new_only_functions: {new_only_funcs}")
    summary_lines.append(f"total_diff_entries: {sum(diff_count_by_type.values())}")
    summary_lines.append("")
    summary_lines.append("=== DIFF COUNT BY TYPE ===")
    for k, v in sorted(diff_count_by_type.items(), key=lambda x: -x[1]):
        summary_lines.append(f"  {k}: {v}")
    summary_lines.append("")
    summary_lines.append("=== TOP 30 FUNCTIONS BY DIFF COUNT ===")
    for k, v in sorted(diff_count_by_func.items(), key=lambda x: -x[1])[:30]:
        summary_lines.append(f"  {k}: {v} diffs")

    with open("/tmp/r8_diff_detail.txt", "w") as f:
        f.write("\n".join(detail_lines))
    with open("/tmp/r8_summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    print(f"detail_lines={len(detail_lines)} summary_lines={len(summary_lines)}")
    print(f"total_funcs={total_funcs} diff_funcs={diff_funcs} lost={lost_funcs} new_only={new_only_funcs}")
    print(f"diffs_by_type={dict(diff_count_by_type)}")


if __name__ == "__main__":
    main()
