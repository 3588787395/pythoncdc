"""Round-3 file-3 helper: positional code-object pairing + raw instruction dump for
duplicate-named nested code objects (<genexpr>). Read-only, test-side.
Usage: python -X utf8 test_repros/round3/_r3diag_f3.py <orig.pyc> <prod.py> <parent-suffix> [occurrence]
"""
import dis
import io
import marshal
import pathlib
import sys
import types

ROOT = pathlib.Path(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main')


def load(p):
    p = str(ROOT / p) if not p.startswith('D:') else p
    if p.endswith('.pyc'):
        with open(p, 'rb') as f:
            return marshal.loads(f.read()[16:])
    with open(p, encoding='utf-8-sig') as f:
        return compile(f.read(), p, 'exec')


def walk(code, prefix=''):
    out = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            n = f'{prefix}{c.co_name}'
            out.append((n, c))
            out.extend(walk(c, n + '.'))
    return out


def dump(code, title):
    buf = io.StringIO()
    print(f'--- {title}: {code.co_name} argcount={code.co_argcount} '
          f'n={len(list(dis.get_instructions(code)))}', file=buf)
    for i in dis.get_instructions(code):
        if i.opname == 'CACHE':
            continue
        av = i.argval
        if isinstance(av, types.CodeType):
            av = f'<code {av.co_name}>'
        print(f'{i.offset:>5} {i.opname:<34} {av!r:<28} ln={i.starts_line}', file=buf)
    return buf.getvalue()


if __name__ == '__main__':
    orig, prod, suffix = sys.argv[1], sys.argv[2], sys.argv[3]
    occ = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    o = [x for x in walk(load(orig)) if x[0].endswith(suffix)]
    p = [x for x in walk(load(prod)) if x[0].endswith(suffix)]
    print(f'ORIG occurrences={len(o)} PROD occurrences={len(p)} for suffix {suffix}')
    for k, (on, oc) in enumerate(o):
        pc = p[k][1] if k < len(p) else None
        print(f'===== pair {k}  {on}  insns orig={len(list(dis.get_instructions(oc)))} '
              f'prod={len(list(dis.get_instructions(pc))) if pc else "MISSING"}')
        if pc is None:
            continue
        oa = [(i.opname, i.offset) for i in dis.get_instructions(oc) if i.opname != 'CACHE']
        pa = [(i.opname, i.offset) for i in dis.get_instructions(pc) if i.opname != 'CACHE']
        fd = next(((k2, oa[k2], pa[k2]) for k2 in range(min(len(oa), len(pa))) if oa[k2][0] != pa[k2][0]), None)
        print(f'  names orig={oc.co_names} prod={pc.co_names}')
        print('  first opcode-position divergence:', fd)
        if fd is None and len(oa) == len(pa):
            continue
        lo = max(0, (fd[0] if fd else 0) - 2)
        print(dump(oc, f'ORIG pair{k}').splitlines()[lo:lo + 26])
        print(dump(pc, f'PROD pair{k}').splitlines()[lo:lo + 26])
