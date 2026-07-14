"""
字节码 diff 工具 - 用于根因分析

用法:
    python _diag_bytecode_diff.py <test_file_path>
    python _diag_bytecode_diff.py tests/exhaustive/if_region/test_c05nested_if_in_if_x.py

输出:
    - 原始源码
    - 反编译源码
    - 原始字节码 (dis)
    - 重编译字节码 (dis)
    - 指令级 diff
"""
import sys
import os
import dis
import types
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.exhaustive.base import ExhaustiveTestCase


def load_test_class(test_file):
    module_name = f'diag_{test_file.stem}'
    spec = importlib.util.spec_from_file_location(module_name, str(test_file))
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and
                issubclass(obj, ExhaustiveTestCase) and
                obj is not ExhaustiveTestCase):
            return obj
    return None


def filter_jump_instructions(instructions):
    skip_opnames = {
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'FOR_ITER', 'SEND',
        'NOP', 'CACHE',
    }
    return [i for i in instructions if i.opname not in skip_opnames]


def print_instrs(label, instructions, max_lines=50):
    print(f"\n{'='*60}")
    print(f"{label} ({len(instructions)} instructions)")
    print(f"{'='*60}")
    for i, ins in enumerate(instructions[:max_lines]):
        argval_str = str(ins.argval)[:60]
        arg_str = str(ins.arg) if ins.arg is not None else '-'
        print(f"  [{i:3d}] {ins.offset:4d} {ins.opname:30s} arg={arg_str:>3s} argval={argval_str}")
    if len(instructions) > max_lines:
        print(f"  ... ({len(instructions) - max_lines} more)")


def diff_instructions(orig, recomp):
    """指令级 diff"""
    print(f"\n{'='*60}")
    print(f"DIFF (filtered)")
    print(f"{'='*60}")
    orig_f = filter_jump_instructions(orig)
    recomp_f = filter_jump_instructions(recomp)
    max_len = max(len(orig_f), len(recomp_f))
    diffs_found = 0
    for i in range(max_len):
        o = orig_f[i] if i < len(orig_f) else None
        r = recomp_f[i] if i < len(recomp_f) else None
        if o is None:
            print(f"  [{i:3d}] +++ RECOMP ONLY: {r.opname} argval={r.argval}")
            diffs_found += 1
        elif r is None:
            print(f"  [{i:3d}] --- ORIG ONLY:  {o.opname} argval={o.argval}")
            diffs_found += 1
        elif o.opname != r.opname:
            print(f"  [{i:3d}] OPNAME: orig={o.opname} vs recomp={r.opname}")
            diffs_found += 1
        elif o.argval != r.argval and o.opname not in (
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        ):
            if isinstance(o.argval, types.CodeType) and isinstance(r.argval, types.CodeType):
                print(f"  [{i:3d}] NESTED CODE OBJECT (recursing):")
                print(f"       orig.co_name={o.argval.co_name}, recomp.co_name={r.argval.co_name}")
                diff_code_objects(o.argval, r.argval, depth=1)
            else:
                print(f"  [{i:3d}] ARGVAL: orig={o.argval} vs recomp={r.argval} (op={o.opname})")
                diffs_found += 1
    if diffs_found == 0:
        print("  (no differences in filtered instructions)")
    return diffs_found


def diff_code_objects(orig, recomp, depth=0):
    if depth > 5:
        return
    prefix = "  " * (depth + 1)
    print(f"\n{prefix}--- Nested code object: {orig.co_name} ---")
    orig_instrs = list(dis.get_instructions(orig))
    recomp_instrs = list(dis.get_instructions(recomp))
    print(f"{prefix}orig: {len(orig_instrs)} instrs, recomp: {len(recomp_instrs)} instrs")
    diff_instructions(orig_instrs, recomp_instrs)


def main():
    if len(sys.argv) < 2:
        print("Usage: python _diag_bytecode_diff.py <test_file_path>")
        print("Example: python _diag_bytecode_diff.py tests/exhaustive/if_region/test_c05nested_if_in_if_x.py")
        sys.exit(1)

    test_file = Path(sys.argv[1])
    if not test_file.is_absolute():
        test_file = PROJECT_ROOT / test_file

    if not test_file.exists():
        print(f"Error: test file not found: {test_file}")
        sys.exit(1)

    test_class = load_test_class(test_file)
    if test_class is None:
        print(f"Error: could not load test class from {test_file}")
        sys.exit(1)

    print(f"Test file: {test_file}")
    print(f"Test class: {test_class.__name__}")
    print(f"SOURCE_CODE:")
    print(test_class.SOURCE_CODE)

    try:
        test_class.setUpClass()
    except Exception as e:
        print(f"Error in setUpClass: {e}")
        sys.exit(1)

    test_method_name = 'test_decompile'
    if not hasattr(test_class, test_method_name):
        for name in dir(test_class):
            if name.startswith('test_'):
                test_method_name = name
                break
    instance = test_class(test_method_name)

    print(f"\n{'#'*60}")
    print("# ORIGINAL BYTECODE")
    print(f"{'#'*60}")
    orig_code = instance.original_code
    orig_instrs = list(dis.get_instructions(orig_code))
    print_instrs("ORIGINAL (full)", orig_instrs)

    try:
        decompiled = instance.decompile()
        print(f"\n{'#'*60}")
        print("# DECOMPILED SOURCE")
        print(f"{'#'*60}")
        print(decompiled)
    except Exception as e:
        print(f"\nDECOMPILE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        recompiled = compile(decompiled, '<decompiled>', 'exec')
    except SyntaxError as e:
        print(f"\nRECOMPILE FAILED (syntax): {e}")
        return

    print(f"\n{'#'*60}")
    print("# RECOMPILED BYTECODE")
    print(f"{'#'*60}")
    recomp_instrs = list(dis.get_instructions(recompiled))
    print_instrs("RECOMPILED (full)", recomp_instrs)

    diff_instructions(orig_instrs, recomp_instrs)

    error = instance._compare_code_objects(orig_code, recompiled)
    print(f"\n{'='*60}")
    print(f"_compare_code_objects result: {error if error else 'None (equivalent)'}")


if __name__ == '__main__':
    main()
