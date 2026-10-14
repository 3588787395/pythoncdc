"""Round-1 diagnostic helper (read-only; no production code touched).

Usage:
  python -X utf8 test_repros/round1/_diag.py dump <pyc|py> <name>
  python -X utf8 test_repros/round1/_diag.py diff <orig.pyc> <prod.py> <name>
  python -X utf8 test_repros/round1/_diag.py tree <pyc|py>
"""
import dis
import marshal
import sys
import types


def _mod_from_pyc(path):
    with open(path, 'rb') as f:
        return marshal.loads(f.read()[16:])


def _mod_from_py(path):
    with open(path, encoding='utf-8') as f:
        return compile(f.read(), path, 'exec')


def load_code(path):
    return _mod_from_pyc(path) if path.endswith('.pyc') else _mod_from_py(path)


def walk(code, prefix=''):
    out = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            name = f'{prefix}{c.co_name}'
            out.append((name, c))
            out.extend(walk(c, name + '.'))
    return out


def find(code, name):
    for n, c in walk(code):
        if n == name or n.endswith('.' + name) or c.co_name == name:
            return c
    return None


def norm(c):
    seq = []
    for ins in dis.get_instructions(c):
        if ins.opname == 'CACHE':
            continue
        seq.append((ins.opname, ins.argval, ins.offset))
    return seq


def cmd_dump(pyc, name):
    code = load_code(pyc)
    c = find(code, name)
    if c is None:
        print('NOT FOUND', name, '->', [n for n, _ in walk(code)])
        return
    print(f'=== {name} from {pyc} ===')
    dis.dis(c)


def cmd_tree(pyc):
    for n, c in walk(load_code(pyc)):
        print(f'{n}  args={c.co_argcount} nlocals={c.co_nlocals} insns={len(norm(c))}')


def cmd_diff(orig, prod, name):
    co = find(load_code(orig), name)
    cp = find(load_code(prod), name)
    if co is None or cp is None:
        print('MISSING', 'orig' if co is None else 'prod', name)
        if co is None:
            print('orig names:', [n for n, _ in walk(load_code(orig))])
        if cp is None:
            print('prod names:', [n for n, _ in walk(load_code(prod))])
        return
    a, b = norm(co), norm(cp)
    print(f'orig {name}: {len(a)} insns | prod {name}: {len(b)} insns')
    n = min(len(a), len(b))
    first = None
    for i in range(n):
        if (a[i][0], a[i][1]) != (b[i][0], b[i][1]):
            first = i
            break
    if first is None and len(a) != len(b):
        first = n
    if first is None:
        print('NO linear divergence (identical up to CACHE/offsets)')
        return
    lo = max(0, first - 8)
    print(f'--- FIRST divergence at linear index {first} ---')
    for tag, seq in (('ORIG', a), ('PROD', b)):
        print(f'  [{tag}]')
        for j in range(lo, min(len(seq), first + 12)):
            mark = '>>' if j == first else '  '
            op, av, off = seq[j]
            print(f'   {mark} idx{j:4d} off{off:5d} {op:<28} {av!r}')
    print('  tail orig ops:', [x[0] for x in a[first + 12:]][:24])
    print('  tail prod ops:', [x[0] for x in b[first + 12:]][:24])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'dump':
        cmd_dump(sys.argv[2], sys.argv[3])
    elif cmd == 'tree':
        cmd_tree(sys.argv[2])
    elif cmd == 'diff':
        cmd_diff(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(__doc__)
