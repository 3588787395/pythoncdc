"""逐指令追踪表达式重建器的栈深变化（用于定位三元喂入 MAP_ADD 契约破坏点）。

用法: D:/Python/python.exe trace_stack.py [offset_lo] [offset_hi]
"""
import sys
import types
import marshal

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.ast_generator_v2 import ExpressionReconstructor


def node_desc(n):
    if isinstance(n, dict):
        t = n.get('type', '?')
        if t == 'Dict':
            return 'Dict(%d)' % len(n.get('keys', []))
        if t == 'Constant':
            return 'Const(%r)' % (n.get('value'),)
        if t == 'Name':
            return 'Name(%s)' % n.get('id')
        if t == 'Compare':
            return 'Compare'
        if t == 'Attribute':
            return 'Attr(%s)' % n.get('attr')
        return t
    return type(n).__name__


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9

    pyc = ROOT + r'\site-packages\IQEngine\account\order.pyc'
    with open(pyc, 'rb') as f:
        f.read(16)
        orig = marshal.load(f)

    def find(co, name, out):
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                if c.co_name == name:
                    out.append(c)
                find(c, name, out)

    o = []
    find(orig, 'save', o)
    co = o[0]

    import dis
    ins = list(dis.get_instructions(co))
    print('原始 save() %d 条指令' % len(ins))

    r = ExpressionReconstructor()
    for x in ins:
        before = len(r.stack)
        r._process_instruction(x)
        after = len(r.stack)
        off = x.offset
        if lo <= off <= hi:
            top = ''
            if after:
                top = node_desc(r.stack[-1])
            second = ''
            if after >= 2:
                second = node_desc(r.stack[-2])
            print('%4d %-34s %2d->%-2d  top=%-24s below=%s'
                  % (off, x.opname + (' ' + str(x.argval) if x.arg is not None else ''),
                     before, after, top, second))


if __name__ == '__main__':
    main()
