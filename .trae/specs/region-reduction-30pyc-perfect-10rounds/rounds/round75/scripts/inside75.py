# -*- coding: utf-8 -*-
"""R75 diag1 · inside75.py — 9 个「首分歧在异常区内」单元的行级根因对照（只读）。

对每个 in_try 单元给出：
  * 原 pyc：co_exceptiontable 条目（start/end/target/depth）→ 行号区间、handler 数、嵌套深度
  * 产品：编译 OK.py 得到的异常表（同口径）+ OK.py AST 里 ast.Try 的行区间/handler/嵌套
  * fam75 的 lineA/lineB（首分歧行）与 verdict
输出 dump/inside75.md。
用法：python -X utf8 inside75.py
"""
import ast
import dis
import io
import json
import marshal
import os
import sys
import types

WORK = r'D:/Temp/opencode/r75gate/diag1'
G3 = (r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/'
      r'rounds/round74/logs/gate/G3v_pycverify_r74.json')
CROSSTAB = r'D:/Temp/opencode/r75gate/center/dump/crosstab75.txt'
FAM = os.path.join(WORK, 'fam75.json')
OUT = os.path.join(WORK, 'dump', 'inside75.md')
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(p):
    data = io.open(p, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('unmarshal fail %s' % p)


def walk(code, pref=''):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            f = (pref + '.' + c.co_name).lstrip('.')
            yield f, c
            for x in walk(c, f):
                yield x


def find(code, nm):
    for f, c in walk(code):
        if f == nm:
            return c
    return None


def lines_of(code):
    """offset -> line map via co_lines()；line=None 的区间前后回填"""
    raw = [(s, e, ln) for s, e, ln in code.co_lines()]
    m = {}
    for i, (s, e, ln) in enumerate(raw):
        if ln is None:
            ln = next((r[2] for r in raw[i + 1:] if r[2] is not None), None)
            if ln is None:
                ln = next((r[2] for r in reversed(raw[:i]) if r[2] is not None), None)
        for o in range(s, e):
            m[o] = ln
    return m


def et_entries(code):
    out = []
    for e in dis._parse_exception_table(code):
        out.append((e.start, e.end, e.target, getattr(e, 'depth', None)))
    return out


def et_depth(entries):
    """range-overlap nesting depth of exception table entries"""
    if not entries:
        return 0
    best = 0
    for i, (s, e, t, d) in enumerate(entries):
        depth = 1
        for j, (s2, e2, t2, d2) in enumerate(entries):
            if i == j:
                continue
            if s2 <= s and e <= e2 and not (s2 == s and e == e2):
                depth += 1
        best = max(best, depth)
    return best


def try_nodes(src, qualname):
    """AST Try 节点（按 qualname 定位函数体），返回行区间与嵌套"""
    tree = ast.parse(src)
    target = None
    if qualname == '<module>':
        target = tree
    else:
        parts = [p for p in qualname.split('.') if p and p != '<module>']
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[-1]:
                target = node
                break
            if isinstance(node, ast.ClassDef) and node.name == parts[0]:
                for n2 in ast.walk(node):
                    if isinstance(n2, (ast.FunctionDef, ast.AsyncFunctionDef)) and n2.name == parts[-1]:
                        target = n2
                        break
    if target is None:
        return []
    res = []

    def rec(n, d):
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch, ast.Try):
                handlers = [(h.lineno, getattr(h, 'end_lineno', h.lineno), h.type and ast.unparse(h.type))
                            for h in ch.handlers]
                res.append(dict(depth=d + 1, lineno=ch.lineno, end=getattr(ch, 'end_lineno', None),
                                body=(ch.body[0].lineno, ch.body[-1].lineno),
                                handlers=handlers, orelse=(ch.orelse[0].lineno, ch.orelse[-1].lineno) if ch.orelse else None,
                                final=(ch.finalbody[0].lineno, ch.finalbody[-1].lineno) if ch.finalbody else None))
                rec(ch, d + 1)
            else:
                rec(ch, d)

    rec(target, 0)
    return res


def main():
    ct = [l.split('\t') for l in io.open(CROSSTAB, encoding='utf-8').read().splitlines() if l.strip()]
    intry = [r for r in ct if len(r) >= 5 and r[4] == '1']
    fam = {(x['file'], x['name']): x for x in json.load(io.open(FAM, encoding='utf-8'))}
    g = json.load(io.open(G3, encoding='utf-8'))
    rows = {}
    for r in g['rows']:
        if r['status'] != 'success':
            rows[r['pyc']] = r
    out = ['# R75 diag1 · 9 个 inside-try 单元行级对照（dump/inside75.md）', '',
           '口径：原 pyc 异常表 `dis._parse_exception_table`；产品侧 = OK.py 重编译 code 的异常表 + '
           '`ast.Try` 行区间；行号取 `co_lines()`；`lineA/lineB` 取 `center/fam75.json` 首分歧行。', '']
    recs = []
    for rel, unit, famc, verdict in [(r[0], r[1], r[2], r[3]) for r in intry]:
        pyc = 'F:/Downloads/pythoncdc-main/site-packages/' + rel
        ok = pyc.replace('.pyc', 'OK.py')
        if not os.path.exists(ok):
            out.append('## %s | %s\n\nMISSING %s\n' % (rel, unit, ok))
            continue
        key = unit.split('.', 1)[1] if unit.startswith('<module>.') else unit
        oc = load_pyc(pyc)
        code_o = oc if key == '<module>' else find(oc, key)
        src = io.open(ok, encoding='utf-8').read()
        kc = compile(src, ok, 'exec')
        code_p = kc if key == '<module>' else find(kc, key)
        f = fam.get((rel, unit), {})
        out.append('## %s | %s' % (rel, unit))
        out.append('')
        out.append('- family=%s verdict=%s lenA=%s lenB=%s lineA=%s lineB=%s'
                   % (famc, f.get('verdict'), f.get('lenA'), f.get('lenB'),
                      f.get('lineA'), f.get('lineB')))
        out.append('- firstA=`%s`  firstB=`%s`' % (f.get('firstA'), f.get('firstB')))
        if code_o is None or code_p is None:
            out.append('- CODEOBJ MISS o=%s p=%s' % (code_o is None, code_p is None))
            out.append('')
            continue
        lo, lp = lines_of(code_o), lines_of(code_p)
        eo, ep = et_entries(code_o), et_entries(code_p)
        tgt_o = sorted({e[2] for e in eo})
        tgt_p = sorted({e[2] for e in ep})
        out.append('- **orig ET**: entries=%d distinct_targets=%d nest=%d  byte_len=%d'
                   % (len(eo), len(tgt_o), et_depth(eo), len(getattr(code_o, 'co_exceptiontable', b''))))
        out.append('  - ' + '; '.join('[L%s-L%s -> handler L%s d%s]'
                                      % (lo.get(e[0]), lo.get(e[1] - 1), lo.get(e[2]), e[3])
                                      for e in eo))
        out.append('- **prod ET**: entries=%d distinct_targets=%d nest=%d  byte_len=%d  bytes_equal=%s'
                   % (len(ep), len(tgt_p), et_depth(ep),
                      len(getattr(code_p, 'co_exceptiontable', b'')),
                      getattr(code_o, 'co_exceptiontable', b'') == getattr(code_p, 'co_exceptiontable', b'')))
        out.append('  - ' + '; '.join('[L%s-L%s -> handler L%s d%s]'
                                      % (lp.get(e[0]), lp.get(e[1] - 1), lp.get(e[2]), e[3])
                                      for e in ep))
        tn = try_nodes(src, key)
        out.append('- **prod ast.Try**: n=%d nest_max=%d' % (len(tn), max([t['depth'] for t in tn] or [0])))
        for t in tn:
            out.append('  - Try L%s-L%s depth=%s body=L%s handlers=%s orelse=%s final=%s'
                       % (t['lineno'], t['end'], t['depth'], t['body'],
                          [(h[0], h[1], h[2]) for h in t['handlers']], t['orelse'], t['final']))
        la, lb = f.get('lineA'), f.get('lineB')
        if isinstance(lb, int):
            ls = src.splitlines()
            out.append('- **product lines around lineB=%s**:' % lb)
            for i in range(max(1, lb - 3), min(len(ls), lb + 4) + 1):
                mark = '>>' if i == lb else '  '
                out.append('  %s %4d %s' % (mark, i, ls[i - 1][:160]))
        bytes_eq = getattr(code_o, 'co_exceptiontable', b'') == getattr(code_p, 'co_exceptiontable', b'')
        tn2 = try_nodes(src, key)
        lb2 = f.get('lineB')
        in_try_line = bool(isinstance(lb2, int) and any(
            t['lineno'] <= lb2 <= (t['end'] or t['lineno']) for t in tn2))
        if bytes_eq:
            verdict4 = '异常表字节相同 ⇒ 根因不在 try，try 是**载体**'
        elif len(eo) != len(ep):
            verdict4 = '异常表条目数 %d→%d ⇒ try 边界/层次有差，try 结构是差异来源之一' % (len(eo), len(ep))
        else:
            verdict4 = '条目数相同(=%d)但字节不同 ⇒ handler 落点/depth 有差，try 结构是差异来源之一' % len(eo)
        recs.append(dict(rel=rel, unit=unit, fam=famc, lineA=f.get('lineA'), lineB=lb2,
                         eo=len(eo), ep=len(ep), bytes_eq=bytes_eq,
                         try_n=len(tn2), try_nest=max([t['depth'] for t in tn2] or [0]),
                         in_try_line=in_try_line, firstB=f.get('firstB'),
                         verdict4=verdict4))
        out.append('')
    out.append('## 10. 汇总与逐单元判决（本批 9 个）')
    out.append('')
    out.append('| file | unit | family | ET orig→prod | bytes_equal | prod ast.Try n/nest | '
               'lineB 在 try 内 | lineA/lineB | 判决 |')
    out.append('|---|---|---|---|---|---|---|---|---|')
    for r in recs:
        out.append('| %s | %s | %s | %d→%d | %s | %d/%d | %s | %s/%s | %s |' % (
            r['rel'], r['unit'].split('.')[-1], r['fam'], r['eo'], r['ep'],
            r['bytes_eq'], r['try_n'], r['try_nest'], r['in_try_line'],
            r['lineA'], r['lineB'], r['verdict4']))
    out.append('')
    n_same = sum(1 for r in recs if r['bytes_eq'])
    out.append('- 异常表字节相同的 %d/%d：**try 是载体**（根因在 try 内的区域归约），'
               '这些单元不必动 try 生成路径。' % (n_same, len(recs)))
    out.append('- 异常表有差的 %d/%d：条目数差 %d 个、仅字节差 %d 个 → 需在 fix 批按 '
               '`lineB` 落点逐条对照 handler 起止行。' % (
                   len(recs) - n_same, len(recs),
                   sum(1 for r in recs if not r['bytes_eq'] and r['eo'] != r['ep']),
                   sum(1 for r in recs if not r['bytes_eq'] and r['eo'] == r['ep'])))
    out.append('- `lineB` 落在产品 `ast.Try` 行区间内的 %d/%d（首分歧即产品 try 的行上）；'
               '其余单元首分歧在 try 之外的语句行。' % (
                   sum(1 for r in recs if r['in_try_line']), len(recs)))
    out.append('')
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    print('wrote', OUT, 'sections', len(intry))
    for r in recs:
        print('  %-46s ET %d->%d bytes_eq=%s try=%d/%d inTryLine=%s | %s' % (
            r['unit'].split('.')[-1], r['eo'], r['ep'], r['bytes_eq'],
            r['try_n'], r['try_nest'], r['in_try_line'], r['verdict4'][:44]))


if __name__ == '__main__':
    main()
