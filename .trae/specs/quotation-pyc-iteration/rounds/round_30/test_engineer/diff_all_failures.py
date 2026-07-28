"""R30 测试工程师：详细分析所有失败函数的指令差异"""
import sys
import dis
import types

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
    try:
        mod = compile(src, src_path, 'exec')
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
        return None
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
    if src_codes is None:
        return

    common = set(pyc_codes.keys()) & set(src_codes.keys())

    failures = []
    for name in sorted(common):
        pc = pyc_codes[name]
        sc = src_codes[name]
        pi = get_instr_list(pc)
        si = get_instr_list(sc)
        if pi != si:
            failures.append((name, pi, si))

    print(f"=== 失败函数详细分析 ({len(failures)}) ===\n")
    for name, pi, si in failures:
        diff = len(si) - len(pi)
        # Find first diff index
        min_len = min(len(pi), len(si))
        first_diff = -1
        last_diff = -1
        for i in range(min_len):
            if pi[i][1] != si[i][1] or pi[i][2] != si[i][2]:
                if first_diff == -1:
                    first_diff = i
                last_diff = i
        print(f"--- {name}: pyc={len(pi)} src={len(si)} diff={diff} first_diff={first_diff} last_diff={last_diff} ---")
        if first_diff == -1:
            # diff at the end
            if len(pi) > len(si):
                print(f"  pyc has extra tail: {pi[len(si):][:5]}")
            else:
                print(f"  src has extra tail: {si[len(pi):][:5]}")
        else:
            # show context around first diff
            start = max(0, first_diff - 2)
            end = min(min_len, last_diff + 3)
            for i in range(start, end):
                p = pi[i]
                s = si[i]
                mark = '  ' if p[1] == s[1] and p[2] == s[2] else '>>'
                print(f"  {mark} idx={i}: pyc={p[1]} {p[2]!r:.80} | src={s[1]} {s[2]!r:.80}")
            if len(pi) > min_len:
                print(f"  pyc tail ({len(pi)-min_len} extra): {pi[min_len:min_len+3]}")
            if len(si) > min_len:
                print(f"  src tail ({len(si)-min_len} extra): {si[min_len:min_len+3]}")
        print()


if __name__ == '__main__':
    main()
