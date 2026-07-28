"""R26 测试工程师：详细对比失败函数的字节码差异"""
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


def diff_func(name, pyc_codes, src_codes, context=3):
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instrs(pc)
    si = get_instrs(sc)
    print(f"\n{'='*70}")
    print(f"=== {name} (pyc_len={len(pi)}, src_len={len(si)}) ===")
    print(f"{'='*70}")
    # find first diff
    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            first_diff = i
            break
    if first_diff is None:
        print("  IDENTICAL")
        return
    start = max(0, first_diff - context)
    end = min(max(len(pi), len(si)), first_diff + context + 8)
    for i in range(start, end):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        marker = '  '
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            marker = '>>'
        pa = f"{a[0]:>4} {a[1]:<35} {a[3]}" if a else "(none)"
        sb = f"{b[0]:>4} {b[1]:<35} {b[3]}" if b else "(none)"
        print(f"  {marker} [{i:>3}] PYC: {pa}")
        print(f"  {marker}       SRC: {sb}")


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    # Focus on small-diff failures first
    targets = ['get_cb_time_info', 'change_his_to_forward', 'get_option_info', 'get_valuation_new']
    for name in targets:
        diff_func(name, pyc_codes, src_codes)


if __name__ == '__main__':
    main()
