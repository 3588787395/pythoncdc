"""Round 33: 精确对比 ptradeAccount 类体（递归 code object 级别）字节码一致性。

same_code 的 co_consts 比较对含嵌套 code object 的 consts 用身份比较恒失败，
本脚本递归对比所有嵌套 code object 的 co_code/co_names/co_varnames/co_consts
（consts 中非 code object 按值比较，code object 递归比较），给出真实一致性结论。
"""
import sys, os, types, marshal, py_compile

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
OK_PY = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccountOK.py"


def load_code(p):
    with open(p, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def cmp_consts(o_c, d_c, path, diffs):
    if len(o_c) != len(d_c):
        diffs.append('%s: co_consts len %d != %d' % (path, len(o_c), len(d_c)))
        return
    for i, (a, b) in enumerate(zip(o_c, d_c)):
        if isinstance(a, types.CodeType) or isinstance(b, types.CodeType):
            if isinstance(a, types.CodeType) and isinstance(b, types.CodeType):
                cmp_code(a, b, '%s.consts[%d]=%s' % (path, i, a.co_name), diffs)
            else:
                diffs.append('%s.consts[%d]: code object 类型不匹配 %r vs %r' % (path, i, type(a), type(b)))
        else:
            if a != b:
                diffs.append('%s.consts[%d]: %r != %r' % (path, i, a, b))


def cmp_code(o, d, path, diffs):
    if o.co_code != d.co_code:
        diffs.append('%s: co_code 不一致 (%d vs %d bytes)' % (path, len(o.co_code), len(d.co_code)))
    if o.co_names != d.co_names:
        diffs.append('%s: co_names %r != %r' % (path, o.co_names, d.co_names))
    if o.co_varnames != d.co_varnames:
        diffs.append('%s: co_varnames %r != %r' % (path, o.co_varnames, d.co_varnames))
    if o.co_freevars != d.co_freevars:
        diffs.append('%s: co_freevars %r != %r' % (path, o.co_freevars, d.co_freevars))
    if o.co_cellvars != d.co_cellvars:
        diffs.append('%s: co_cellvars %r != %r' % (path, o.co_cellvars, d.co_cellvars))
    cmp_consts(o.co_consts, d.co_consts, path, diffs)


def main():
    orig = load_code(PYC)
    cfile = py_compile.compile(OK_PY, doraise=True, quiet=2)
    dec = load_code(cfile)
    print('模块级 co_code 一致:', orig.co_code == dec.co_code)
    diffs = []
    cmp_code(orig, dec, '<module>', diffs)
    print('模块级差异数:', len(diffs))
    for d in diffs[:10]:
        print('  ', d)
    # 找类体
    o_cls = [c for c in orig.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount']
    d_cls = [c for c in dec.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount']
    if o_cls and d_cls:
        diffs2 = []
        cmp_code(o_cls[0], d_cls[0], 'PtradeAccount', diffs2)
        print('\nPtradeAccount 类体差异数:', len(diffs2))
        for d in diffs2[:15]:
            print('  ', d)
        if not diffs2:
            print('  >>> 类体全部一致（co_code/co_names/co_varnames/co_freevars/co_cellvars/递归 consts）<<<')
    # 统计类体内方法逐一对比
    if o_cls and d_cls:
        o_methods = {}
        def collect(co, acc):
            for c in co.co_consts:
                if isinstance(c, types.CodeType):
                    acc[c.co_name] = c
                    collect(c, acc)
        om, dm = {}, {}
        collect(o_cls[0], om)
        collect(d_cls[0], dm)
        mm, mi = [], []
        for name in om:
            if name not in dm:
                mi.append(name + ': MISSING in dec')
                continue
            d2 = []
            cmp_code(om[name], dm[name], name, d2)
            if d2:
                mi.append(name + ': ' + '; '.join(d2[:2]))
            else:
                mm.append(name)
        print('\n类体内方法: 匹配 %d / 不匹配 %d' % (len(mm), len(mi)))
        for x in mi[:10]:
            print('  MISMATCH', x)


if __name__ == '__main__':
    main()
