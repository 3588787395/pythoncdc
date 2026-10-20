import dis
import io
import marshal
import sys


def load_code(pyc):
    raw = open(pyc, 'rb').read()
    return marshal.loads(raw[16:])


def find(code, dotted):
    parts = dotted.split('.')
    cur = code
    for p in parts:
        if p == '<module>':
            continue
        nxt = None
        for c in cur.co_consts:
            if hasattr(c, 'co_name') and c.co_name == p:
                nxt = c
                break
        if nxt is None:
            raise KeyError('%s not under %s' % (p, cur.co_name))
        cur = nxt
    return cur


def show(label, code, limit=None, exceptions=False):
    print('--- %s' % label)
    ins = list(dis.get_instructions(code))
    if limit:
        ins = ins[:limit]
    for i in ins:
        arg = i.argval if not isinstance(i.argval, str) or len(str(i.argval)) < 60 else str(i.argval)[:57] + '...'
        print('%5d %-28s %s' % (i.offset, i.opname, arg))
    if exceptions:
        print('--- %s exception table' % label)
        for e in dis.Bytecode(code).exception_entries:
            print('  %d-%d -> %d depth=%d lasti=%s' % (e.start, e.end, e.target, e.depth, e.lasti))


def main(pyc, okpy, dotted):
    a = load_code(pyc)
    f1 = find(a, dotted)
    src = io.open(okpy, encoding='utf-8-sig').read()
    b = compile(src, okpy, 'exec')
    f2 = find(b, dotted)
    show('PYC ' + dotted, f1, exceptions=True)
    show('OK  ' + dotted, f2, exceptions=True)
    n1 = len(list(dis.get_instructions(f1)))
    n2 = len(list(dis.get_instructions(f2)))
    print('instr counts: pyc=%d ok=%d' % (n1, n2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
