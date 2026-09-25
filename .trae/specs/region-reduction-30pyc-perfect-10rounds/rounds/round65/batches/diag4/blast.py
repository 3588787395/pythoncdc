# -*- coding: utf-8 -*-
"""blast: cheap blast-radius scan.  For each pyc, run ONLY build_cfg+RegionAnalyzer.analyze
for every code object and count [R64-diag1] pop events, flagging those where the n1
operand-rejoin exemption would suppress the pop.  No AST generation, no compile.
Repo is read-only; nothing is written except stdout/jsonl given by the caller.

usage: python -X utf8 blast.py <list.txt> [--out=blast.jsonl] [--nshard=N --shard=I]
"""
import io
import json
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')

POP_LINE = 25601


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    return None


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def main():
    listfile = sys.argv[1]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[2:])
    out = kw.get('out')
    nshard = int(kw.get('nshard', 1))
    shard = int(kw.get('shard', 0))
    paths = [l.strip() for l in io.open(listfile, encoding='utf-8') if l.strip()]
    paths = [q for i, q in enumerate(paths) if i % nshard == shard]

    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer
    import core.cfg.region_analyzer as RA
    JUMPS = RA.FORWARD_CONDITIONAL_JUMP_OPS | RA.SHORT_CIRCUIT_JUMP_OPS

    fh = io.open(out, 'w', encoding='utf-8') if out else None
    for p in paths:
        root = load_pyc(p)
        if root is None:
            continue
        tot = {'pops': 0, 'rejoin': 0, 'pops_with_rejoin': []}
        for code in walk(root, []):
            try:
                cfg = build_cfg(code)
            except Exception:
                continue
            state = {'n': 0}

            def trace(frame, event, arg):
                f = frame.f_code
                if not f.co_filename.replace('\\', '/').endswith('core/cfg/region_analyzer.py'):
                    return None
                if f.co_name == '_detect_boolop_conditional_chain' and event == 'line' \
                        and frame.f_lineno == POP_LINE:
                    chain = frame.f_locals['chain']
                    T = frame.f_locals.get('_r64_T')
                    ft = frame.f_locals.get('ft_succ')
                    cj = frame.f_locals.get('_r64_cj')
                    cur = frame.f_locals.get('current')
                    rejoin = False
                    for s in (ft, cj):
                        if s is None:
                            continue
                        sl = s.get_last_instruction()
                        if (sl is not None and sl.opname in JUMPS
                                and getattr(sl, 'argval', None) is not None
                                and cfg.get_block_by_offset(sl.argval) is T):
                            rejoin = True
                    tot['pops'] += 1
                    if rejoin:
                        tot['rejoin'] += 1
                        tot['pops_with_rejoin'].append([code.co_name, code.co_firstlineno,
                                                        [getattr(b, 'start_offset', None) for b, _ in chain],
                                                        getattr(T, 'start_offset', None),
                                                        getattr(cur, 'start_offset', None)])
                return trace
            sys.settrace(trace)
            try:
                RegionAnalyzer(cfg).analyze()
            except Exception:
                pass
            finally:
                sys.settrace(None)
        rel = p.replace('\\', '/')
        r0 = r'F:/Downloads/pythoncdc-main/site-packages/'
        if rel.startswith(r0):
            rel = rel[len(r0):]
        rec = {'pyc': p, 'rel': rel, 'pops': tot['pops'], 'rejoin': tot['rejoin'],
               'sites': tot['pops_with_rejoin']}
        line = json.dumps(rec, ensure_ascii=False)
        if fh:
            fh.write(line + '\n')
            fh.flush()
        if tot['rejoin']:
            print('AFFECTED %-58s pops=%d rejoin=%d' % (rel[:58], tot['pops'], tot['rejoin']))
            for s in tot['pops_with_rejoin'][:6]:
                print('      %s@%s chain=%s T=%s current=%s' % (s[0], s[1], s[2], s[3], s[4]))
    if fh:
        fh.close()
    print('scan done: %d files' % len(paths))


if __name__ == '__main__':
    main()
