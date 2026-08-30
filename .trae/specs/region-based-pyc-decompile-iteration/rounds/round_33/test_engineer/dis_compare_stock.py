"""Round 33: 精确对比 stock_order_response_transform 的 pyc vs OK 字节码。"""
import sys, marshal, types, py_compile, dis

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'
OK  = ROOT + r'\site-packages\fly\simtradding\ptradeAccountOK.py'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk_code(co, pf, out):
    if co.co_name != '<module>':
        out[pf + co.co_name] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk_code(c, pf + co.co_name + '.', out)


def main():
    pyc = load_code(PYC)
    cfile = py_compile.compile(OK, doraise=True, quiet=2)
    ok = load_code(cfile)
    pf, of = {}, {}
    walk_code(pyc, '', pf)
    walk_code(ok, '', of)
    name = '<module>.PtradeAccount.stock_order_response_transform'
    a, b = pf[name], of[name]
    print('=== pyc 反汇编 ===')
    dis.dis(a)
    print()
    print('=== OK 反汇编 ===')
    dis.dis(b)


if __name__ == '__main__':
    main()
