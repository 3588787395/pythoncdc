"""快速分析 one_prod_to_dataframe 与 build_future_fill_time 的精确指令差异。"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r4_decompiled.py'
SKIP_OPS = ('EXTENDED_ARG', 'CACHE')


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname in SKIP_OPS:
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    else:
        name = prefix + co.co_name
    sink[name] = co
    sub_prefix = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub_prefix, sink)
    return sink


def load_orig_top():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def instr_repr(ins):
    offset, opname, argval = ins
    if isinstance(argval, types.CodeType):
        av = f"<code {argval.co_name} len={len(get_instr_list(argval))}>"
    else:
        av = repr(argval)
    return f"{offset:5d} {opname:24s} {av}"


def main():
    orig_cos = walk_code(load_orig_top())
    with open(DECOMPILED) as f:
        src = f.read()
    new_cos = walk_code(compile(src, '<decompiled>', 'exec'))

    for fname in ['one_prod_to_dataframe', 'build_future_fill_time']:
        print("=" * 90)
        print(f"FUNCTION: {fname}")
        print("=" * 90)
        oa = get_instr_list(orig_cos[fname])
        na = get_instr_list(new_cos[fname])
        print(f"orig_len={len(oa)} new_len={len(na)} diff={len(na)-len(oa):+d}")
        print()

        if fname == 'one_prod_to_dataframe':
            # 打印 orig 末尾 30 条 + new 末尾 45 条
            print("--- ORIG tail (last 30) ---")
            for i in range(max(0, len(oa) - 30), len(oa)):
                print(f"  {i:>4} O {instr_repr(oa[i])}")
            print("--- NEW tail (last 45) ---")
            for i in range(max(0, len(na) - 45), len(na)):
                print(f"  {i:>4} N {instr_repr(na[i])}")
            # 找 new 中 pandas.DataFrame 出现的位置
            print("--- NEW: positions of LOAD_ATTR 'DataFrame' ---")
            for i, ins in enumerate(na):
                if ins[1] == 'LOAD_ATTR' and ins[2] == 'DataFrame':
                    print(f"  idx={i} {instr_repr(ins)}")
                    for j in range(max(0, i - 8), min(len(na), i + 10)):
                        print(f"     {j:>4} {instr_repr(na[j])}")
        else:
            # build_future_fill_time: instr_diff @226 JUMP_FORWARD 2660 vs 2586
            # 找 orig 中 offset 2660 附近的指令 + new 中 offset 2586 附近的指令
            print("--- ORIG: instructions near offset 2640-2700 ---")
            for i, ins in enumerate(oa):
                if 2640 <= ins[0] <= 2700:
                    print(f"  idx={i} {instr_repr(ins)}")
            print("--- NEW: instructions near offset 2560-2620 ---")
            for i, ins in enumerate(na):
                if 2560 <= ins[0] <= 2620:
                    print(f"  idx={i} {instr_repr(ins)}")
            print("--- ORIG: all JUMP_FORWARD / JUMP_BACKWARD with target near 2660 or 2586 ---")
            for i, ins in enumerate(oa):
                if ins[1] in ('JUMP_FORWARD', 'JUMP_BACKWARD') and isinstance(ins[2], int):
                    if abs(ins[2] - 2660) < 100 or abs(ins[2] - 2586) < 100:
                        print(f"  O idx={i} {instr_repr(ins)}")
            print("--- NEW: all JUMP_FORWARD / JUMP_BACKWARD with target near 2660 or 2586 ---")
            for i, ins in enumerate(na):
                if ins[1] in ('JUMP_FORWARD', 'JUMP_BACKWARD') and isinstance(ins[2], int):
                    if abs(ins[2] - 2660) < 100 or abs(ins[2] - 2586) < 100:
                        print(f"  N idx={i} {instr_repr(ins)}")
        print()


if __name__ == '__main__':
    main()
