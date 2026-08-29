"""探测 CPython 3.11 何时用 BUILD_MAP 0 + MAP_ADD 序列构造 dict 字面量。"""
import dis
import types


def find(co, name, out):
    for x in co.co_consts:
        if isinstance(x, types.CodeType):
            if x.co_name == name:
                out.append(x)
            find(x, name, out)


def main():
    for n in (2, 5, 8, 9, 10, 12, 16, 17, 20, 30):
        items = ', '.join("'k%d': self._a%d" % (i, i) for i in range(n))
        src = 'class A:\n    def save(self):\n        return {%s}\n' % items
        co = compile(src, '<t>', 'exec')
        o = []
        find(co, 'save', o)
        ins = list(dis.get_instructions(o[0]))
        ops = {}
        for x in ins:
            if x.opname.startswith('BUILD_MAP') or x.opname == 'MAP_ADD':
                ops[x.opname] = ops.get(x.opname, 0) + 1
        print('n=%2d  %s' % (n, ops))

    # 再看：dict 中夹带三元表达式时
    print()
    print('--- 含三元表达式的 dict（规模递增）---')
    for n in (2, 5, 9, 10, 17):
        parts = []
        for i in range(n):
            if i == n // 2:
                parts.append("'k%d': self._a%d if self._a%d is not None else None" % (i, i, i))
            else:
                parts.append("'k%d': self._a%d" % (i, i))
        src = 'class A:\n    def save(self):\n        return {%s}\n' % ', '.join(parts)
        co = compile(src, '<t>', 'exec')
        o = []
        find(co, 'save', o)
        ins = list(dis.get_instructions(o[0]))
        ops = {}
        for x in ins:
            if x.opname.startswith('BUILD_MAP') or x.opname == 'MAP_ADD':
                ops[x.opname] = ops.get(x.opname, 0) + 1
        print('n=%2d  %s' % (n, ops))


if __name__ == '__main__':
    main()
