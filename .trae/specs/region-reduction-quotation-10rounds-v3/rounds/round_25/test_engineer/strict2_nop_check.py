"""R24-strict2: 保留 NOP/EXTENDED_ARG，仅跳过 CACHE。统计 NOP 差异。"""
import sys, types, dis, os, json
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r24_decompiled.py'
SKIP_OPS = frozenset(['CACHE'])


def get_instr_list(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        av = ins.argval
        if isinstance(av, types.CodeType):
            out.append(('CODE', av.co_name, get_instr_list(av)))
        else:
            out.append((ins.opname, av))
    return out


def count_op(il, opname):
    n = 0
    for item in il:
        if item[0] == 'CODE':
            n += count_op(item[2], opname)
        elif item[0] == opname:
            n += 1
    return n


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub, sink)
    return sink


def compare_seq(oa, na):
    if len(oa) != len(na):
        return False
    for x, y in zip(oa, na):
        if x[0] == 'CODE' and y[0] == 'CODE':
            if x[1] != y[1]:
                return False
            if not compare_seq(x[2], y[2]):
                return False
        elif x != y:
            return False
    return True


def main():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    co = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(co, 'to_python_code'):
        co = co.to_python_code()
    orig_cos = walk_code(co)
    with open(DECOMPILED) as f:
        src = f.read()
    new_code = compile(src, '<d>', 'exec')
    new_cos = walk_code(new_code)

    print(f"orig cos: {len(orig_cos)}  new cos: {len(new_cos)}")
    print(f"\n=== NOP 数对比（仅列出差异函数）===")
    print(f"{'function':<40} {'orig_NOP':>9} {'new_NOP':>9} {'diff':>6}")
    nop_diff = []
    for name in sorted(set(orig_cos) & set(new_cos)):
        oa = get_instr_list(orig_cos[name])
        na = get_instr_list(new_cos[name])
        o_nop = count_op(oa, 'NOP')
        n_nop = count_op(na, 'NOP')
        if o_nop != n_nop:
            nop_diff.append((name, o_nop, n_nop, n_nop - o_nop))
            print(f"{name:<40} {o_nop:>9} {n_nop:>9} {n_nop-o_nop:>+6}")
    print(f"NOP 差异函数数: {len(nop_diff)}")

    print(f"\n=== EXTENDED_ARG 数对比（前20）===")
    ea_diff = []
    for name in sorted(set(orig_cos) & set(new_cos)):
        oa = get_instr_list(orig_cos[name])
        na = get_instr_list(new_cos[name])
        o_ea = count_op(oa, 'EXTENDED_ARG')
        n_ea = count_op(na, 'EXTENDED_ARG')
        if o_ea != n_ea:
            ea_diff.append((name, o_ea, n_ea, n_ea - o_ea))
    for name, o, n, d in sorted(ea_diff, key=lambda x: abs(x[3]), reverse=True)[:20]:
        print(f"{name:<40} orig={o} new={n} diff={d:+d}")
    print(f"EXTENDED_ARG 差异函数数: {len(ea_diff)}")

    print(f"\n=== 严格序列比较（保留 NOP/EXTENDED_ARG，跳 CACHE）===")
    exact = 0; diff_list = []
    for name in sorted(set(orig_cos) & set(new_cos)):
        oa = get_instr_list(orig_cos[name])
        na = get_instr_list(new_cos[name])
        if len(oa) != len(na):
            diff_list.append((name, len(oa), len(na), len(na)-len(oa), 'len_diff'))
            continue
        if compare_seq(oa, na):
            exact += 1
        else:
            diff_list.append((name, len(oa), len(na), 0, 'instr_diff'))
    total = len(set(orig_cos) & set(new_cos))
    print(f"exact={exact}/{total} ({100*exact/total:.2f}%) diff={total-exact}")
    print(f"\n差异函数:")
    for name, pl, sl, d, st in diff_list:
        print(f"  {name}: {st} len {pl}->{sl} ({d:+d})")


if __name__ == '__main__':
    main()
