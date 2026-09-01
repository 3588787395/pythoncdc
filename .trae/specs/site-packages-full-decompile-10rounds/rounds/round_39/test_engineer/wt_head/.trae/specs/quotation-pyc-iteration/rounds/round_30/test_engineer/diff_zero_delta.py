"""R30 测试工程师：分析diff=0但指令不同的失败函数"""
import sys
import dis

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
    mod = compile(src, src_path, 'exec')
    def collect(co, prefix=''):
        name = prefix + co.co_name
        codes[name] = co
        for c in co.co_consts:
            if isinstance(c, type(co)):
                collect(c, prefix)
    collect(mod)
    return codes


def get_instr_list(co):
    return [(i.offset, i.opname, i.argval) for i in dis.get_instructions(co)]


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        if pi == si:
            continue
        if len(pi) != len(si):
            continue
        # Same length, different instructions
        diffs = []
        for i in range(len(pi)):
            if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
                diffs.append(i)
        if not diffs:
            continue
        print(f"--- {name}: same_len={len(pi)}, diff_count={len(diffs)} ---")
        for i in diffs[:20]:
            p = pi[i]
            s = si[i]
            # For code objects, only compare opname (argval contains memory address)
            p_arg = p[2]
            s_arg = s[2]
            if hasattr(p_arg, 'co_name') and hasattr(s_arg, 'co_name'):
                p_show = f"<code {p_arg.co_name}>"
                s_show = f"<code {s_arg.co_name}>"
                if p_arg.co_name == s_arg.co_name:
                    continue  # same code object, just different address
            else:
                p_show = repr(p_arg)[:60]
                s_show = repr(s_arg)[:60]
            print(f"  idx={i}: pyc={p[1]} {p_show} | src={s[1]} {s_show}")
        print()


if __name__ == '__main__':
    main()
