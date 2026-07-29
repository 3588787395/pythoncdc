"""R16 测试工程师：详细对比单个函数的指令差异。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r16_decompiled.py'
TARGET = sys.argv[1] if len(sys.argv) > 1 else 'check_stocks'


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
            _collect(c, result, name)


def load_src_code_objects(src_path):
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    code = compile(src, src_path, 'exec')
    result = {}
    _collect(code, result, prefix='')
    return result


def get_instr_list(code):
    """返回 (offset, opname, argval) 列表。"""
    instrs = []
    for ins in dis.get_instructions(code):
        instrs.append((ins.offset, ins.opname, repr(ins.argval)))
    return instrs


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    src_codes = load_src_code_objects(SRC)

    name = '<module>.' + TARGET
    if name not in pyc_codes:
        print(f"not found: {name}")
        return
    pc = pyc_codes[name]
    sc = src_codes[name]

    p_instrs = get_instr_list(pc)
    s_instrs = get_instr_list(sc)

    print(f"=== {TARGET} ===")
    print(f"pyc instr count: {len(p_instrs)}")
    print(f"src instr count: {len(s_instrs)}")
    print(f"delta: {len(s_instrs) - len(p_instrs)}")

    # 简单 diff
    import difflib
    p_lines = [f"  {off:4d} {op:20s} {arg}" for off, op, arg in p_instrs]
    s_lines = [f"  {off:4d} {op:20s} {arg}" for off, op, arg in s_instrs]

    diff = list(difflib.unified_diff(
        p_lines, s_lines,
        fromfile='pyc', tofile='src', lineterm=''
    ))

    # 仅显示前 100 行差异
    for line in diff[:200]:
        print(line)


if __name__ == '__main__':
    main()
