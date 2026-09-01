"""R10 测试工程师：详细 diff 单个函数的指令差异，定位首个差异点。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r10_decompiled.py'


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            child_prefix = name
            _collect(c, result, child_prefix)


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code = compile(src, src_path, 'exec')
    result = {}
    _collect(code, result, prefix='')
    return result


def instr_sequence(code):
    """返回 (opname, argval) 列表，递归处理 code object 常量。"""
    seq = []
    for ins in dis.get_instructions(code):
        seq.append((ins.opname, ins.argval))
    return seq


def diff_function(name, pyc_codes, src_codes, max_ctx=15):
    pc = pyc_codes[name]
    sc = src_codes[name]
    p_seq = instr_sequence(pc)
    s_seq = instr_sequence(sc)
    print(f"\n=== {name} ===")
    print(f"pyc instrs: {len(p_seq)}, src instrs: {len(s_seq)}")
    # find first diff
    n = min(len(p_seq), len(s_seq))
    first = None
    for i in range(n):
        if p_seq[i] != s_seq[i]:
            first = i
            break
    if first is None and len(p_seq) == len(s_seq):
        print("  IDENTICAL")
        return
    if first is None:
        first = n
    start = max(0, first - max_ctx)
    end = min(max(len(p_seq), len(s_seq)), first + max_ctx + 5)
    print(f"  first diff at index {first}:")
    print(f"  --- pyc (offset {start}..{end}) ---")
    for i in range(start, end):
        marker = '>>' if i == first else '  '
        if i < len(p_seq):
            print(f"  {marker} pyc[{i:3d}] {p_seq[i][0]:30s} {p_seq[i][1]!r}")
        else:
            print(f"  {marker} pyc[{i:3d}] <EOF>")
    print(f"  --- src (offset {start}..{end}) ---")
    for i in range(start, end):
        marker = '>>' if i == first else '  '
        if i < len(s_seq):
            print(f"  {marker} src[{i:3d}] {s_seq[i][0]:30s} {s_seq[i][1]!r}")
        else:
            print(f"  {marker} src[{i:3d}] <EOF>")


def main():
    import sys
    targets = sys.argv[1:]
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)
    if not targets:
        # default: show a few representative failures
        targets = [
            'get_growth_ability',
            'balance_statement',
            'growth_ability',
            'get_history',
            'load_get_index_stocks',
            'load_get_price',
        ]
    for t in targets:
        # try exact, then <module>.<t>
        cand = [t, '<module>.' + t]
        found = None
        for c in cand:
            if c in pyc_codes and c in src_codes:
                found = c
                break
        if found:
            diff_function(found, pyc_codes, src_codes)
        else:
            print(f"\n=== {t} === NOT FOUND (pyc={t in pyc_codes}, src={t in src_codes})")


if __name__ == '__main__':
    main()
