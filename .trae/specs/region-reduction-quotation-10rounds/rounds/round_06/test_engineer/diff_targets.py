"""轮 6 测试工程师：生成 build_future_fill_time 等关键函数的字节码 diff 详情。"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r6_decompiled.py'

SKIP_OPS = ('EXTENDED_ARG', 'CACHE')
TARGETS = {'build_future_fill_time', 'one_prod_to_dataframe'}


def get_instr_list(co: types.CodeType):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def fmt(ins):
    av = ins[2]
    if isinstance(av, types.CodeType):
        return f"<code {av.co_name} len={len(get_instr_list(av))}>"
    return repr(av)


def main():
    orig_cos = walk_code(load_orig())
    with open(DECOMPILED, 'r', encoding='utf-8') as f:
        src = f.read()
    new_code = compile(src, '<decompiled>', 'exec')
    new_cos = walk_code(new_code)

    for name in TARGETS:
        if name not in orig_cos or name not in new_cos:
            print(f"=== {name}: MISSING ===")
            continue
        oa = get_instr_list(orig_cos[name])
        na = get_instr_list(new_cos[name])
        print(f"\n{'='*80}")
        print(f"FUNCTION: {name}  orig_len={len(oa)} new_len={len(na)} diff={len(na)-len(oa):+d}")
        print('='*80)
        # find first diff
        fd = -1
        for i, (x, y) in enumerate(zip(oa, na)):
            if x[1] != y[1] or not _eq(x[2], y[2]):
                fd = i
                break
        if fd < 0 and len(oa) == len(na):
            print("MATCH")
            continue
        start = max(0, (fd if fd >= 0 else 0) - 15)
        end = min(max(len(oa), len(na)), (fd if fd >= 0 else 0) + 25)
        print(f"FIRST DIFF @ idx={fd}")
        print(f"{'idx':>4} | {'ORIG':<60} | {'NEW':<60}")
        for i in range(start, end):
            o = f"{oa[i][0]} {oa[i][1]} {fmt(oa[i])}" if i < len(oa) else '<end>'
            n = f"{na[i][0]} {na[i][1]} {fmt(na[i])}" if i < len(na) else '<end>'
            mark = '>>' if i == fd else '  '
            print(f"{mark}{i:>3} | {o:<60} | {n:<60}")


def _eq(a, b):
    if isinstance(a, types.CodeType) and isinstance(b, types.CodeType):
        ia, ib = get_instr_list(a), get_instr_list(b)
        return len(ia) == len(ib)
    if isinstance(a, types.CodeType) or isinstance(b, types.CodeType):
        return False
    return a == b


if __name__ == '__main__':
    main()
