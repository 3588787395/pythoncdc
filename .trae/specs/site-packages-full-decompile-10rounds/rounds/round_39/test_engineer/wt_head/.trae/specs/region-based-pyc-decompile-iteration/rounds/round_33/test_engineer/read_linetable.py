"""Round 33: 直接读 pyc 类体 linetable (co_lines)，确认 NOP 与 STORE_NAME 的真实行号。"""
import sys, marshal, types, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def main():
    pyc = load_code(PYC)
    cls = [c for c in pyc.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount'][0]
    print('co_code len:', len(cls.co_code))
    print('co_lines() 全部条目:')
    for start, end, line in cls.co_lines():
        print('  offset %-5d..%-5d line %s' % (start, end, line))
    print()
    # 与 dis 指令对齐，找出每个关键偏移的指令
    print('关键偏移指令:')
    for ins in dis.get_instructions(cls):
        if ins.offset in (132, 134, 136, 138, 140, 142, 528, 530, 532, 534, 536, 538, 540, 542, 544, 946, 948, 950, 952, 954, 956):
            print('  %-5d op=%-25s arg=%-20s line=%s' % (ins.offset, ins.opname, str(ins.argval)[:30], ins.starts_line))


if __name__ == '__main__':
    main()
