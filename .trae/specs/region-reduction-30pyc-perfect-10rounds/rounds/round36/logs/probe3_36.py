# -*- coding: utf-8 -*-
"""Round 36 probe #3: does the R35-B family (duplicated cleanup epilogue) have residuals in the
current pool, and in which direction?

For every defective function of the deficit-1 and deficit-2 pools, read the *landed* products that
are already tracked in site-packages, recompile them (explicit cfile in this scratch dir), diff them
against the original code objects with the strict ruler, and classify each non-equal hunk:

  EPILOGUE  hunk ops are a subset of {POP_EXCEPT, LOAD_CONST, RETURN_VALUE, RETURN_CONST, POP_TOP,
            RERAISE, COPY, SWAP, PUSH_EXC_INFO, END_FOR} and contain >=1 POP_EXCEPT
  other     anything else

Prints per function: delta, hunk kinds, how many POP_EXCEPT the original has vs the product, and how
many `return None` statements the product text holds at the function's own indent -- the two numbers
that decide whether R35-B suppressed too much or too little. Read-only for the repo.
"""
import difflib
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r36gate/r36'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

CLEAN_OPS = {'POP_EXCEPT', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST', 'POP_TOP', 'RERAISE',
             'COPY', 'SWAP', 'PUSH_EXC_INFO', 'END_FOR', 'JUMP_BACKWARD', 'EXTENDED_ARG'}

rows = []
for lst in ('d1list.txt', 'd2list.txt'):
    for p in [l.strip() for l in io.open(os.path.join(ROOT, lst), encoding='utf-8') if l.strip()]:
        recs = [json.loads(l) for l in io.open(os.path.join(
            ROOT, 'landed_d1.jsonl' if lst == 'd1list.txt' else 'landed_d2.jsonl'), encoding='utf-8')]
        rec = [r for r in recs if r['path'].replace('\\', '/').endswith(p.replace('\\', '/').split('site-packages/')[-1])]
        assert rec, p
        names = {m[0] for m in (rec[0].get('mism') or [])}
        if not names:
            continue
        py = p[:-4] + 'OK.py'
        cfile = os.path.join(ROOT, 'probe3_' + os.path.basename(p)[:-4] + '.pyc')
        import py_compile
        py_compile.compile(py, cfile=cfile, doraise=True, quiet=2)
        om, dm = r10._load_map(p), r10._load_map(cfile)
        text = io.open(py, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
        for name in sorted(names):
            key = [k for k in om if k.split('.')[-1] == name]
            if not key or key[0] not in dm:
                rows.append('%-46s %-30s MISSING side' % (os.path.basename(p), name))
                continue
            o, d = om[key[0]], dm[key[0]]
            fo, fd = r10.filtered(o), r10.filtered(d)
            tok = lambda x: ('<J>', r10._norm_jump_op(x.opname)) if r10._is_jump(x.opname) \
                else (x.opname)
            to, td = [tok(x) for x in fo], [tok(x) for x in fd]
            hunks = [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in
                     difflib.SequenceMatcher(None, to, td, autojunk=False).get_opcodes()
                     if t != 'equal']
            cls = []
            for t, i1, i2, j1, j2 in hunks:
                seg = to[i1:i2] + td[j1:j2]
                ep = bool(seg) and set(seg) <= CLEAN_OPS and any(
                    x == 'POP_EXCEPT' for x in to[i1:i2]) and any(x == 'POP_EXCEPT' for x in td[j1:j2])
                cls.append('%s%s@%d(%d->%d)' % (t[0] + t[:3], '|EPI' if ep else '',
                                                fo[i1].offset if i1 < len(fo) else -1,
                                                i2 - i1, j2 - j1))
            pe_o = sum(1 for x in to if x == 'POP_EXCEPT')
            pe_d = sum(1 for x in td if x == 'POP_EXCEPT')
            rn_o = sum(1 for x in to if x == 'RETURN_VALUE')
            rn_d = sum(1 for x in td if x == 'RETURN_VALUE')
            ind = next((len(text[k]) - len(text[k].lstrip()) for k in range(len(text) - 1)
                        if text[k].strip().startswith('def %s(' % name)), None)
            body = []
            if ind is not None:
                k = next(k for k in range(len(text)) if text[k].strip().startswith('def %s(' % name))
                for l in text[k + 1:]:
                    if l.strip():
                        if (len(l) - len(l.lstrip())) <= ind:
                            break
                        body.append(l)
            rn_txt = sum(1 for l in body if l.strip() == 'return None')
            rows.append('%-34s %-30s delta=%+4d  POP_EXCEPT %3d->%-3d  RETURN %3d->%-3d  '
                        'retNone_txt=%-3d hunks=%s' % (
                            os.path.basename(p), name, len(td) - len(fo), pe_o, pe_d, rn_o, rn_d,
                            rn_txt, ' '.join(cls)[:200]))

out = '\n'.join(rows) + '\n'
io.open(os.path.join(ROOT, 'probe3_epilogue_residuals.txt'), 'w', encoding='utf-8',
        newline='\n').write(out)
print(out)
print('%d functions read' % len(rows))
