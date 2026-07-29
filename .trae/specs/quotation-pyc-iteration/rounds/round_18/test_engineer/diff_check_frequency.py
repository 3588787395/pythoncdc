"""R18: 详细对比 check_frequency 函数的原始字节码 vs 反编译字节码"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2


def load_pyc_code_objects(pyc_path):
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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects('/workspace/quotation.pyc')
    with open('/tmp/r18_decompiled.py', 'r', encoding='utf-8') as f:
        src = f.read()
    src_codes = compile(src, '<decompiled>', 'exec')

    src_map = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        src_map[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(src_codes)

    for name in ['check_frequency', 'get_opt_objects', 'get_opt_contracts', 'get_opt_last_dates']:
        print(f"\n{'='*80}\n=== {name} ===\n{'='*80}")
        pc = pyc_codes.get(name)
        sc = src_map.get(name)
        if not pc or not sc:
            print(f"  missing: pyc={pc is not None}, src={sc is not None}")
            continue
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        print(f"  pyc len={len(pi)}, src len={len(si)}")
        n = max(len(pi), len(si))
        print(f"\n  --- diff (pyc | src) ---")
        for i in range(n):
            a = pi[i] if i < len(pi) else None
            b = si[i] if i < len(si) else None
            mark = ' ' if a == b else '!'
            # 对 code object 简化显示
            def fmt(x):
                if x is None:
                    return '----'
                if isinstance(x[2], types.CodeType):
                    return f"({x[0]},{x[1]},<code {x[2].co_name}>)"
                return f"({x[0]},{x[1]},{x[2]!r})"
            print(f"  {mark} [{i:3d}] pyc: {fmt(a):<60} src: {fmt(b)}")

    # 同时打印 check_frequency 的反编译源码
    print("\n\n=== check_frequency 反编译源码 ===")
    import re
    m = re.search(r'def check_frequency\([^)]*\):.*?(?=\ndef |\Z)', src, re.DOTALL)
    if m:
        print(m.group(0))

    print("\n=== get_opt_objects 反编译源码 ===")
    m = re.search(r'def get_opt_objects\([^)]*\):.*?(?=\ndef |\Z)', src, re.DOTALL)
    if m:
        print(m.group(0))


if __name__ == '__main__':
    main()
