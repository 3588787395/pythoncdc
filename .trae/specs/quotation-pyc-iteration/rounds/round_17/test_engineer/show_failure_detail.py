"""R17 显示特定失败模式的详细 diff"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r17_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(code_obj)
    return result


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code_obj = compile(src, '<decompiled>', 'exec')
    result = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(code_obj)
    return result


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def show_diff(name, pyc_codes, src_codes):
    pc = pyc_codes.get(name)
    sc = src_codes.get(name)
    if not pc or not sc:
        print(f"  {name}: not found")
        return
    pi = get_instr_list(pc)
    si = get_instr_list(sc)
    print(f"\n--- {name} (pyc len={len(pi)}, src len={len(si)}, delta={len(si)-len(pi)}) ---")
    for i, (a, b) in enumerate(zip(pi, si)):
        if a != b:
            print(f"  first diff at idx={i}: pyc={a} vs src={b}")
            print(f"  pyc[{max(0,i-3)}:{i+5}]:")
            for j in range(max(0,i-3), min(len(pi), i+5)):
                marker = " >>" if j == i else "   "
                print(f"   {marker}[{j}] {pi[j]}")
            print(f"  src[{max(0,i-3)}:{i+5}]:")
            for j in range(max(0,i-3), min(len(si), i+5)):
                marker = " >>" if j == i else "   "
                print(f"   {marker}[{j}] {si[j]}")
            return
    if len(pi) != len(si):
        print(f"  length diff: pyc={len(pi)}, src={len(si)}")
        if len(pi) < len(si):
            print(f"  src extra instructions from idx {len(pi)}:")
            for j in range(len(pi), min(len(si), len(pi)+10)):
                print(f"     [{j}] {si[j]}")
        else:
            print(f"  pyc extra instructions from idx {len(si)}:")
            for j in range(len(si), min(len(pi), len(si)+10)):
                print(f"     [{j}] {pi[j]}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r17_failures.txt') as f:
        failures = [l.strip() for l in f if l.strip()]

    # 找出所有 NOP_vs_LOAD_GLOBAL 的函数
    target_pattern = sys.argv[1] if len(sys.argv) > 1 else "NOP_vs_LOAD_GLOBAL"

    for name in failures:
        pc = pyc_codes.get(name)
        sc = src_codes.get(name)
        if not pc or not sc:
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        for i, (a, b) in enumerate(zip(pi, si)):
            if a[1] != b[1]:
                pattern = f"opname_diff:{a[1]}_vs_{b[1]}"
                if target_pattern in pattern or target_pattern == "ALL":
                    show_diff(name, pyc_codes, src_codes)
                break
            elif a[2] != b[2]:
                if a[1] == 'LOAD_CONST' and isinstance(a[2], types.CodeType):
                    pattern = "const_diff:code_object"
                else:
                    pattern = f"argval_diff:{a[1]}"
                if target_pattern in pattern or target_pattern == "ALL":
                    show_diff(name, pyc_codes, src_codes)
                break
        else:
            if len(pi) != len(si):
                pattern = f"length_diff(delta={len(si)-len(pi)})"
                if target_pattern in pattern or target_pattern == "ALL":
                    show_diff(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
