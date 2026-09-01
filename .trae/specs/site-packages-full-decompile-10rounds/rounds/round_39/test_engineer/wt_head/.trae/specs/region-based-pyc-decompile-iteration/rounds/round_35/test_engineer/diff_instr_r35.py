"""对比 change_2str_of_time_2_datetime 原始与反编译字节码,输出差异明细。"""
import sys, marshal, types, dis, py_compile
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

TARGET = 'change_2str_of_time_2_datetime'
ORIG_PYC = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\datetime_func.pyc'
OK_PY = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\datetime_funcOK.py'


def load_code(path, header=True):
    with open(path, 'rb') as f:
        if header:
            f.read(16)
        return marshal.load(f)


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r:
                return r
    return None


def extract(fn):
    return [(ins.offset, ins.opname, ins.argval) for ins in dis.get_instructions(fn)]


def main():
    orig = load_code(ORIG_PYC)
    o_fn = find_code(orig, TARGET)
    cfile = py_compile.compile(OK_PY, doraise=True, quiet=2)
    decomp = load_code(cfile)
    d_fn = find_code(decomp, TARGET)
    if o_fn is None or d_fn is None:
        print('NOT FOUND: orig=%s decomp=%s' % (o_fn is not None, d_fn is not None))
        return

    ol = extract(o_fn)
    dl = extract(d_fn)
    print('== %s: orig=%d decomp=%d ==' % (TARGET, len(ol), len(dl)))

    # 指令级逐条对比(带行号锚定的错位检测)
    print('\n--- 逐条对比(offset 对齐,显示 argval 差异) ---')
    om = {o[0]: o for o in ol}
    dm = {d[0]: d for d in dl}
    all_off = sorted(set(om.keys()) | set(dm.keys()))
    for off in all_off:
        o = om.get(off)
        d = dm.get(off)
        if o is None:
            print('  decomp-only @%-4d %-28s %s' % (d[0], d[1], str(d[2])[:14]))
        elif d is None:
            print('  orig-only   @%-4d %-28s %s' % (o[0], o[1], str(o[2])[:14]))
        else:
            mark = '  ' if o[1] == d[1] and str(o[2]) == str(d[2]) else '>>'
            if mark == '>>':
                print('%s orig@%-4d %-28s %-14s | decomp@%-4d %-28s %-14s' % (
                    mark, o[0], o[1], str(o[2])[:14], d[0], d[1], str(d[2])[:14]))

    print('\n--- 反编译反汇编全文 ---')
    for ins in dis.get_instructions(d_fn):
        print('  %-4d %-28s %s' % (ins.offset, ins.opname, ins.argval))


if __name__ == '__main__':
    main()
