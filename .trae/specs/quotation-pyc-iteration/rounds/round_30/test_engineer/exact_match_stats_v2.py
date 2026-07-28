"""R30 测试工程师：统计字节码一致性（正确处理code object比较）"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r30_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    codes = {}
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(code_obj)
    return codes


def load_src_code_objects(src_path):
    with open(src_path) as f:
        src = f.read()
    codes = {}
    try:
        mod = compile(src, src_path, 'exec')
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(mod)
    return codes


def normalize_argval(argval, seen=None):
    """Normalize argval for comparison - convert code objects to a comparable form."""
    if seen is None:
        seen = {}
    if isinstance(argval, types.CodeType):
        # Use co_name + co_code as identity for code objects
        key = (argval.co_name, argval.co_code)
        return key
    return argval


def get_instr_list_normalized(co):
    """Get instruction list with normalized argval for proper comparison."""
    result = []
    for ins in dis.get_instructions(co):
        argval = normalize_argval(ins.argval)
        result.append((ins.opname, argval))
    return result


def code_objects_equal(co1, co2):
    """Recursively compare two code objects for equality."""
    if co1 is co2:
        return True
    # Compare instruction sequences
    instrs1 = get_instr_list_normalized(co1)
    instrs2 = get_instr_list_normalized(co2)
    if instrs1 != instrs2:
        return False
    # Compare basic properties
    if co1.co_argcount != co2.co_argcount:
        return False
    if co1.co_kwonlyargcount != co2.co_kwonlyargcount:
        return False
    if co1.co_posonlyargcount != co2.co_posonlyargcount:
        return False
    if tuple(co1.co_varnames[:co1.co_argcount + co1.co_kwonlyargcount]) != tuple(co2.co_varnames[:co2.co_argcount + co2.co_kwonlyargcount]):
        return False
    return True


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if src_codes is None:
        return

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    exact_match = []
    instr_match = []
    instr_diff = []
    pyc_only = set(pyc_codes.keys()) - set(src_codes.keys())
    src_only = set(src_codes.keys()) - set(pyc_codes.keys())

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list_normalized(pc)
        si = get_instr_list_normalized(sc)

        sig_match = (
            pc.co_argcount == sc.co_argcount and
            pc.co_kwonlyargcount == sc.co_kwonlyargcount and
            pc.co_posonlyargcount == sc.co_posonlyargcount and
            tuple(pc.co_varnames[:pc.co_argcount + pc.co_kwonlyargcount]) ==
            tuple(sc.co_varnames[:sc.co_argcount + sc.co_kwonlyargcount])
        )

        if pi == si:
            if sig_match:
                exact_match.append(name)
            else:
                instr_match.append(name)
        else:
            instr_diff.append((name, len(pi), len(si), len(si) - len(pi)))

    total = len(common)
    print(f"=== 字节码一致性统计 (normalized) ===")
    print(f"common functions: {total}")
    print(f"精确匹配 (instr+sig): {len(exact_match)} ({100.0*len(exact_match)/total:.1f}%)")
    print(f"指令匹配 (仅instr):   {len(instr_match)} ({100.0*len(instr_match)/total:.1f}%)")
    print(f"指令差异:             {len(instr_diff)} ({100.0*len(instr_diff)/total:.1f}%)")
    print(f"pyc_only: {len(pyc_only)}, src_only: {len(src_only)}")
    print(f"完全成功率 (exact/total): {100.0*len(exact_match)/total:.2f}%")
    print(f"指令成功率 (exact+instr)/total: {100.0*(len(exact_match)+len(instr_match))/total:.2f}%")

    print(f"\n=== 指令差异函数 (sorted by diff size) ===")
    instr_diff_sorted = sorted(instr_diff, key=lambda x: abs(x[3]), reverse=True)
    for name, pl, sl, d in instr_diff_sorted:
        print(f"  {name}: pyc={pl} src={sl} diff={d}")

    if pyc_only:
        print(f"\n=== pyc_only ({len(pyc_only)}) ===")
        for n in sorted(pyc_only)[:20]:
            print(f"  {n}")
    if src_only:
        print(f"\n=== src_only ({len(src_only)}) ===")
        for n in sorted(src_only)[:20]:
            print(f"  {n}")


if __name__ == '__main__':
    main()
