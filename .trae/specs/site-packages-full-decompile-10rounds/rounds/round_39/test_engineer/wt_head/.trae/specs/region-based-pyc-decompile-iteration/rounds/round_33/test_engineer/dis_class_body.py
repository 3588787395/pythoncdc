"""Round 33: 对比 PtradeAccount 类体字节码差异（471 vs 467）。"""
import sys, marshal, types, py_compile, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def main():
    pyc = load_code(PYC)
    cfile = py_compile.compile(OK, doraise=True, quiet=2)
    ok = load_code(cfile)
    a = [c for c in pyc.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount'][0]
    b = [c for c in ok.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount'][0]
    print('pyc len:', len(a.co_code), ' ok len:', len(b.co_code))
    # 按 2 字节指令对齐（3.11 指令 2 字节 + 8 字节 cache，dis 的 offset 是真实偏移）
    pa, pb = a.co_code, b.co_code
    i = j = 0
    diff_rows = []
    while i < len(pa) and j < len(pb):
        if pa[i:i+2] == pb[j:j+2]:
            i += 2; j += 2
            continue
        # 检查是否 NOP(0x09) 缺失
        if pa[i] == 0x09:  # pyc 有 NOP
            diff_rows.append(('PYC-ONLY NOP @pyc=%d' % i, 'NOP', '--'))
            i += 2
            continue
        if pb[j] == 0x09:  # ok 有 NOP
            diff_rows.append(('OK-ONLY NOP @ok=%d' % j, '--', 'NOP'))
            j += 2
            continue
        diff_rows.append(('MISMATCH @pyc=%d/@ok=%d' % (i, j),
                          '0x%02x %s' % (pa[i], dis.opname[pa[i]]),
                          '0x%02x %s' % (pb[j], dis.opname[pb[j]])))
        i += 2; j += 2
    print('差异行:')
    for r in diff_rows[:25]:
        print('  ', r)
    print('... 共', len(diff_rows), '行差异')
    # 对比 NOP 位置
    pyc_nops = [k for k in range(0, len(pa), 2) if pa[k] == 0x09]
    ok_nops = [k for k in range(0, len(pb), 2) if pb[k] == 0x09]
    print('\npyc NOP offsets:', pyc_nops)
    print('ok  NOP offsets:', ok_nops)
    print('差异:', [x for x in pyc_nops if x not in ok_nops], 'OK多出:', [x for x in ok_nops if x not in pyc_nops])


if __name__ == '__main__':
    main()
