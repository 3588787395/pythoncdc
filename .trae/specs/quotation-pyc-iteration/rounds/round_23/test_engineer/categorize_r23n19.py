"""R23-N19 测试工程师：按diff数量排序失败函数，找出最小修复目标"""
import sys
import importlib.util
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


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


def get_instr_list(co):
    instrs = []
    for ins in dis.get_instructions(co):
        if ins.opname == 'EXTENDED_ARG':
            continue
        if ins.opname == 'CACHE':
            continue
        instrs.append((ins.offset, ins.opname, ins.argval))
    return instrs


def instr_equal(a, b):
    if a[1] != b[1]:
        return False
    av_a, av_b = a[2], b[2]
    if isinstance(av_a, types.CodeType) and isinstance(av_b, types.CodeType):
        ia = get_instr_list(av_a)
        ib = get_instr_list(av_b)
        if len(ia) != len(ib):
            return False
        for x, y in zip(ia, ib):
            if not instr_equal(x, y):
                return False
        return True
    return av_a == av_b


def compute_diff(pyc_co, src_co):
    """返回 (diff_count, first_diff_offset, pyc_instr_count, src_instr_count)"""
    pi = get_instr_list(pyc_co)
    si = get_instr_list(src_co)
    # 简单逐项比较
    diff_count = 0
    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if a is None or b is None or not instr_equal(a, b):
            diff_count += 1
            if first_diff is None and a is not None:
                first_diff = a[0]
    return diff_count, first_diff, len(pi), len(si)


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    with open('/tmp/r23_failures.txt', 'r') as f:
        failures = [l.strip() for l in f if l.strip()]

    results = []
    for name in failures:
        if name not in pyc_codes or name not in src_codes:
            continue
        diff_count, first_diff, p_cnt, s_cnt = compute_diff(pyc_codes[name], src_codes[name])
        results.append((diff_count, name, first_diff, p_cnt, s_cnt))

    results.sort()
    print(f"=== 失败函数 diff 排序（升序）===")
    print(f"{'diff':>6}  {'p_cnt':>6}  {'s_cnt':>6}  {'first@':>8}  name")
    for dc, name, fd, pc, sc in results:
        fd_str = f"@{fd}" if fd is not None else "N/A"
        print(f"{dc:6d}  {pc:6d}  {sc:6d}  {fd_str:>8}  {name}")


if __name__ == '__main__':
    main()
