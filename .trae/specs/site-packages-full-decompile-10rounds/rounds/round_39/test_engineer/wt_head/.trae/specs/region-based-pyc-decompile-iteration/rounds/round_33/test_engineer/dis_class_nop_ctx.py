"""Round 33: dump PtradeAccount 类体 NOP 位置前后的完整指令上下文（含行号）。

目标：确认 pyc 中 4 个 NOP 的前后指令、行号，与 OK.py 对应位置的差异。
"""
import sys, marshal, types, py_compile, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_cls(code, name):
    return [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name == name][0]


def instrs_with_lines(code):
    """返回 [(offset, instr)]，instr.starts_line 为行号或 None。"""
    return [(instr.offset, instr) for instr in dis.get_instructions(code)]


def dump_ctx(code, title, nop_offsets, radius=6):
    print('=' * 70)
    print(title, 'len(co_code)=', len(code.co_code))
    ins = instrs_with_lines(code)
    by_off = {off: (insn, idx) for idx, (off, insn) in enumerate(ins)}
    nops = set(nop_offsets)
    for off in nop_offsets:
        print('-' * 60)
        print('NOP 目标偏移 %d (0x%x)' % (off, off))
        if off not in by_off:
            print('  (偏移不在指令表中!)')
            continue
        _, idx = by_off[off]
        for k in range(max(0, idx - radius), min(len(ins), idx + radius + 1)):
            off2, insn = ins[k]
            mark = ' <<<< NOP' if off2 in nops else ''
            print('  %6d  L%-5s %-42s %s%s' % (
                off2, str(insn.starts_line), insn.opname,
                ('' if insn.argval is None else repr(insn.argval)), mark))
    # 同时列出所有 NOP 偏移处的行号
    print('-' * 60)
    for off in nop_offsets:
        if off in by_off:
            insn, _ = by_off[off]
            print('NOP @%d -> line %s' % (off, insn.starts_line))


def main():
    pyc = load_code(PYC)
    cfile = py_compile.compile(OK, doraise=True, quiet=2)
    ok = load_code(cfile)
    a = find_cls(pyc, 'PtradeAccount')
    b = find_cls(ok, 'PtradeAccount')
    print('pyc len:', len(a.co_code), ' ok len:', len(b.co_code))
    pa, pb = a.co_code, b.co_code
    pyc_nops = [k for k in range(0, len(pa), 2) if pa[k] == 0x09]
    ok_nops = [k for k in range(0, len(pb), 2) if pb[k] == 0x09]
    print('pyc NOP offsets:', pyc_nops)
    print('ok  NOP offsets:', ok_nops)
    dump_ctx(a, 'PYC 类体 NOP 上下文', pyc_nops)
    # OK 类体：找出与 pyc NOP 偏移大致对应的区域（pyc 无 NOP 时 ok 对应偏移错位，
    # 用行号对齐：找到 ok 中行号 >= pyc NOP 行号的第一条指令）
    print()
    print('=' * 70)
    print('OK 类体全函数 def 行号分布:')
    for off, insn in instrs_with_lines(b):
        if insn.opname == 'LOAD_CONST' and isinstance(insn.argval, types.CodeType):
            print('  %6d  L%-5s def %s' % (off, insn.starts_line, insn.argval.co_name))


if __name__ == '__main__':
    main()
