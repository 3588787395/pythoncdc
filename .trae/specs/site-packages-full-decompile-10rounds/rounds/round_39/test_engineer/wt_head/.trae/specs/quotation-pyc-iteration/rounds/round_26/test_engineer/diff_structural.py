"""R26 测试工程师：通过最长公共前缀+后缀找到真正的结构差异"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r26_decompiled.py'


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


def get_instrs(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
    return out


def find_structural_diff(name, pyc_codes, src_codes):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instrs(pc)
    si = get_instrs(sc)
    print(f"\n{'='*70}")
    print(f"=== {name} (pyc={len(pi)}, src={len(si)}, diff={len(si)-len(pi):+d}) ===")
    print(f"{'='*70}")
    # Longest common prefix (by opname only)
    prefix = 0
    for i in range(min(len(pi), len(si))):
        if pi[i][1] == si[i][1]:
            prefix = i + 1
        else:
            break
    # Longest common suffix (by opname only)
    suffix = 0
    while (suffix < min(len(pi), len(si)) - prefix):
        if pi[len(pi)-1-suffix][1] == si[len(si)-1-suffix][1]:
            suffix += 1
        else:
            break
    pyc_mid = pi[prefix:len(pi)-suffix]
    src_mid = si[prefix:len(si)-suffix]
    print(f"  common prefix={prefix}, common suffix={suffix}")
    print(f"  PYC middle ({len(pyc_mid)} instrs):")
    for i, ins in enumerate(pyc_mid):
        print(f"    [{prefix+i:>3}] {ins[0]:>4} {ins[1]:<35} {ins[3]}")
    print(f"  SRC middle ({len(src_mid)} instrs):")
    for i, ins in enumerate(src_mid):
        print(f"    [{prefix+i:>3}] {ins[0]:>4} {ins[1]:<35} {ins[3]}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    targets = ['get_cb_time_info', 'change_his_to_forward', 'get_option_info']
    for name in targets:
        find_structural_diff(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
