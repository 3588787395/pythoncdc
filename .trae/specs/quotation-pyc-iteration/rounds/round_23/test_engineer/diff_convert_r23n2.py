"""R23-N2 验证：显示 convert_to_list 函数当前的字节码差异"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r22_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
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


def show(co, label):
    print(f"\n=== {label} ===")
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        print(f"  {ins.offset:4d}  {ins.opname:30s} {ins.argrepr}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    for name in ['convert_to_list']:
        if name not in pyc_codes or name not in src_codes:
            print(f"{name} missing")
            continue
        pc = pyc_codes[name]
        sc = src_codes[name]
        show(pc, f"PYC {name}")
        show(sc, f"SRC {name}")

        # 显示首个差异
        pi = list(dis.get_instructions(pc))
        si = list(dis.get_instructions(sc))
        i = j = 0
        diff_count = 0
        while i < len(pi) and j < len(si):
            if pi[i].opname in ('EXTENDED_ARG', 'CACHE'):
                i += 1
                continue
            if si[j].opname in ('EXTENDED_ARG', 'CACHE'):
                j += 1
                continue
            if pi[i].opname != si[j].opname:
                print(f"\n  DIFF @{pi[i].offset}: pyc={pi[i].opname}({pi[i].argrepr!r}) vs src={si[j].opname}({si[j].argrepr!r})")
                diff_count += 1
                if diff_count >= 10:
                    break
            elif pi[i].argval != si[j].argval:
                print(f"\n  ARGVAL DIFF @{pi[i].offset}: pyc={pi[i].opname}({pi[i].argval!r}) vs src={pi[i].opname}({si[j].argval!r})")
                diff_count += 1
                if diff_count >= 10:
                    break
            i += 1
            j += 1

        if len(pi) != len(si):
            print(f"\n  LENGTH: pyc={len(pi)}, src={len(si)}")

        # 显示源码片段
        print(f"\n=== SRC CODE for {name} ===")
        with open(SRC, 'r', encoding='utf-8') as f:
            src = f.read()
        import re
        m = re.search(rf'def {name}\([^)]*\)[^\n]*:\n(?:.*\n)*?(?=\n(?:def |class |@\w|\Z))', src)
        if m:
            print(m.group(0)[:1500])


if __name__ == '__main__':
    main()
