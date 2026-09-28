# -*- coding: utf-8 -*-
"""R75 diag1 · q4575.py — Q4 控制组判决 + Q5 跨文件同构聚类（只读）。

输入（均已有读数）：
  fam75.json / dump/submech75.txt / center/dump/crosstab75.txt /
  center/dump/exctable_diff75.txt / center/dump/tryverdict75.txt
输出：dump/q45_75.md
用法：python -X utf8 q4575.py
"""
import io
import json
import os
import sys
import collections

WORK = r'D:/Temp/opencode/r75gate/diag1'
CENTER = r'D:/Temp/opencode/r75gate/center'
SITE = 'F:/Downloads/pythoncdc-main/site-packages/'
OUT = os.path.join(WORK, 'dump', 'q45_75.md')
sys.path.insert(0, WORK)
import inside75 as I75  # noqa: E402  复用 load_pyc/find/et_entries/et_depth/try_nodes/lines_of

sys.stdout.reconfigure(encoding='utf-8')

CTRL = [  # BRIEF Q4 点名的 et>0 但首分歧在区外的单元
    ('klinedata.pyc', '<module>.get_kline_by_count_new'),
    ('trade_info_utils.pyc', '<module>.kill_trade_process'),
    ('trade_info_utils.pyc', '<module>.get_trade_status'),
    ('quote.pyc', '<module>.Quote.check_frequency'),
    ('quote.pyc', '<module>.Quote.run_individual_transform'),
    ('ptradeAccount.pyc', '<module>.PtradeAccount.order_response_order_update'),
    ('ptradeAccount.pyc', '<module>.PtradeAccount.trade_response_order_update'),
]
HEAD = ['trade_live_broker.pyc', 'quote.pyc', 'trade_info_utils.pyc']


def read_lines(p):
    return io.open(p, encoding='utf-8').read().splitlines()


def probe(key, REL, F):
    """重算控制组单元的原/产品异常表（条目数、嵌套深度、字节是否全同）与产品 ast.Try。"""
    rel = REL.get(key[0])
    if not rel:
        return {'err': 'no rel for %s' % key[0]}
    pyc = SITE + rel
    ok = pyc.replace('.pyc', 'OK.py')
    if not os.path.exists(ok):
        return {'err': 'missing %s' % ok}
    nm = key[1]
    k = nm.split('.', 1)[1] if nm.startswith('<module>.') else nm
    co = I75.load_pyc(pyc)
    c_o = co if k == '<module>' else I75.find(co, k)
    src = io.open(ok, encoding='utf-8').read()
    kc = compile(src, ok, 'exec')
    c_p = kc if k == '<module>' else I75.find(kc, k)
    if c_o is None or c_p is None:
        return {'err': 'codeobj miss o=%s p=%s' % (c_o is not None, c_p is not None)}
    eo, ep = I75.et_entries(c_o), I75.et_entries(c_p)
    do, dp = I75.et_depth(eo), I75.et_depth(ep)
    beq = getattr(c_o, 'co_exceptiontable', b'') == getattr(c_p, 'co_exceptiontable', b'')
    tn = I75.try_nodes(src, k)
    lb = F.get(key, {}).get('lineB')
    inl = bool(isinstance(lb, int) and any(
        t['lineno'] <= lb <= (t['end'] or t['lineno']) for t in tn))
    return dict(eo=len(eo), ep=len(ep), do=do, dp=dp, beq=beq, try_n=len(tn),
                try_nest=max([t['depth'] for t in tn] or [0]), inl=inl, lineB=lb,
                lineA=F.get(key, {}).get('lineA'))


def main():
    fam = json.load(io.open(os.path.join(WORK, 'fam75.json'), encoding='utf-8'))
    F = {(e['file'].split('/')[-1], e['name']): e for e in fam}

    sub = {}
    hdr = None
    for ln in read_lines(os.path.join(WORK, 'dump', 'submech75.txt')):
        if not ln.strip() or ln.startswith('#'):
            continue
        p = ln.split('\t')
        if hdr is None and p[0] == 'file':
            hdr = p
            continue
        if hdr:
            sub[(p[0].split('/')[-1], p[1])] = dict(zip(hdr, p))

    intry = {}
    REL = {}
    for ln in read_lines(os.path.join(CENTER, 'dump', 'crosstab75.txt')):
        p = ln.split('\t')
        if len(p) >= 5:
            base = p[0].split('/')[-1]
            intry[(base, p[1])] = p[4]
            REL[base] = p[0]

    et = {}
    for ln in read_lines(os.path.join(CENTER, 'dump', 'exctable_diff75.txt')):
        if ' | ' not in ln:
            continue
        a, b, c, d = [x.strip() for x in ln.split(' | ')]
        et[(a, b)] = (c, d)

    tv = {}
    for ln in read_lines(os.path.join(CENTER, 'dump', 'tryverdict75.txt')):
        if ' | ' not in ln:
            continue
        a, b, c = [x.strip() for x in ln.split(' | ')]
        kv = dict(x.split('=') for x in c.split() if '=' in x)
        tv[(a, b)] = kv

    def row(key):
        f = F.get(key, {})
        s = sub.get(key, {})
        e = et.get(key, ('?', '?'))
        t = tv.get(key, {})
        return dict(
            file=key[0], unit=key[1],
            family=f.get('family', s.get('family', '?')),
            cls=s.get('cls', '?'),
            reason=f.get('reason', ''),
            intry=intry.get(key, '?'),
            et=e[0], etdet=e[1],
            ett=t.get('et', '?'), nest=t.get('nest', '?'),
            prodnest=t.get('prodTryNest', '?'),
            orphan=s.get('orphan', '?'), mergeabs=s.get('mergeabs', '?'),
            outpred=s.get('outpred', '?'),
            lineA=f.get('lineA'), lineB=f.get('lineB'),
            firstA=f.get('firstA'), firstB=f.get('firstB'),
            lenA=f.get('lenA'), lenB=f.get('lenB'),
        )

    out = ['# R75 diag1 · Q4 控制组判决 + Q5 跨文件同构聚类（dump/q45_75.md）', '',
           'Q4 判据（只读读数，不改判据）：`et` = `exctable_diff75` 异常表 SAME/DIFF；'
           '`ett/nest/prodnest` = `tryverdict75` 原异常表条目数/原表嵌套深度/产品 AST `ast.Try` 嵌套深度；'
           '`intry` = 首分歧是否落在异常区内；`cls` = `dump/submech75.txt` 子机理归属。', '']

    out.append('## Q4 · 7 个点名单元（et>0、首分歧在区外）逐个判决')
    out.append('')
    out.append('| file | unit | cls | ET ents o→p | ET depth o→p | ET bytes_eq | '
               'prod ast.Try n/nest | intry | lineB 在产品 try 内 | lineA/lineB |')
    out.append('|---|---|---|---|---|---|---|---|---|---|')
    verdicts = []
    for key in CTRL:
        r = row(key)
        pr = probe(key, REL, F)
        if 'err' in pr:
            out.append('| %s | %s | %s | PROBE-ERR %s | | | | | | |' % (
                r['file'], r['unit'].split('.')[-1], r['cls'], pr['err']))
            verdicts.append((r, '读数失败：%s' % pr['err']))
            continue
        out.append('| %s | %s | %s | %d→%d | %d→%d | %s | %d/%d | %s | %s | %s/%s |' % (
            r['file'], r['unit'].split('.')[-1], r['cls'],
            pr['eo'], pr['ep'], pr['do'], pr['dp'], pr['beq'],
            pr['try_n'], pr['try_nest'], r['intry'], pr['inl'],
            pr['lineA'], pr['lineB']))
        # 判决：层数/条目是否变多 > 字节是否全同 > 并列
        extra = (pr['dp'] > pr['do']) or (pr['ep'] > pr['eo'])
        if extra:
            v = ('try 是**根因**：产品异常表比原品多层/多条目（ents %d→%d、嵌套深度 %d→%d、'
                 '产品 ast.Try n=%d nest=%d，原表 nest=%s）——用户裁定的「嵌套 try-except」'
                 '在此单元成立；区域归约信号并存 cls=%s，但先修 try 层'
                 % (pr['eo'], pr['ep'], pr['do'], pr['dp'], pr['try_n'], pr['try_nest'],
                    r['nest'], r['cls']))
        elif pr['beq']:
            v = ('try 是**载体**：原/产品 `co_exceptiontable` 字节全同（ents=%d、depth=%d、'
                 '产品 ast.Try n=%d），差异全在 try 内的控制流落点 ⇒ 根因=区域归约 cls=%s'
                 % (pr['eo'], pr['do'], pr['try_n'], r['cls']))
        elif (pr['eo'], pr['do']) == (pr['ep'], pr['dp']):
            v = ('并列：条目数与嵌套深度都相同（%d/%d）但字节不同 ⇒ handler 的 start/end/target 有漂移；'
                 '区域归约信号 cls=%s；tiebreak：lineB=%s %s 产品 try 行区间'
                 % (pr['eo'], pr['do'], r['cls'], pr['lineB'],
                    '在' if pr['inl'] else '不在'))
        else:
            v = ('并列：ents %d→%d depth %d→%d 字节不同但产品未多建层；区域归约信号 cls=%s；'
                 'tiebreak lineB=%s %s 产品 try 行区间'
                 % (pr['eo'], pr['ep'], pr['do'], pr['dp'], r['cls'], pr['lineB'],
                    '在' if pr['inl'] else '不在'))
        verdicts.append((r, v))
    out.append('')
    n_root = sum(1 for r, v in verdicts if '是**根因**' in v)
    n_carrier = sum(1 for r, v in verdicts if '是**载体**' in v)
    out.append('- 计数：**try=根因 %d / try=载体 %d / 并列 %d**（共 7）'
               % (n_root, n_carrier, 7 - n_root - n_carrier))
    out.append('')
    for r, v in verdicts:
        out.append('- **%s / %s** → %s' % (r['file'], r['unit'].split('.')[-1], v))
    out.append('')

    # 汇总：全部 71 单元的 et × intry × cls 交叉
    out.append('## Q4 · 附：71 单元 `exctable × intry × cls` 交叉（全量读数）')
    out.append('')
    tab = collections.Counter()
    for key in sorted(F):
        r = row(key)
        tab[(r['et'], r['intry'], r['cls'])] += 1
    out.append('| exctable | intry | cls | n |')
    out.append('|---|---|---|---|')
    for k, v in sorted(tab.items()):
        out.append('| %s | %s | %s | %d |' % (k[0], k[1], k[2], v))
    out.append('')

    # Q5 聚类
    out.append('## Q5 · 跨文件同构聚类（trade_live_broker / quote / trade_info_utils 三大头部）')
    out.append('')
    out.append('聚类键（放宽后）= `(family, cls, lenA-lenB, 首异 opname, 首异跳转 opname)`；'
               '`reason` 内嵌具体 idx/长度不入键。只列**跨 ≥2 个文件**的簇（跨文件同构的定义）。')
    out.append('')
    groups = collections.defaultdict(list)
    for key in sorted(F):
        r = row(key)
        if r['file'] not in HEAD:
            continue
        fa = (r['firstA'] or '').split(' ')
        try:
            dlen = int(r['lenA']) - int(r['lenB'])
        except (TypeError, ValueError):
            dlen = None
        sig = (r['family'], r['cls'], dlen,
               fa[1] if len(fa) > 1 else '',
               fa[0] if fa else '')
        groups[sig].append(r)
    n = 0
    for sig, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        files = {x['file'] for x in rs}
        if len(files) < 2:
            continue
        n += 1
        out.append('### 簇 %d · n=%d files=%s' % (n, len(rs), sorted(files)))
        out.append('- key = family=%s cls=%s lenA-lenB=%s first=%s %s' % sig)
        for x in rs:
            out.append('  - %-22s %-54s lineA=%s lineB=%s orphan=%s mergeabs=%s outpred=%s' % (
                x['file'], x['unit'], x['lineA'], x['lineB'],
                x['orphan'], x['mergeabs'], x['outpred']))
        out.append('')
    if not n:
        out.append('（放宽后仍无跨 ≥2 文件的簇 ⇒ 三大头部的残留单元**不同构**，'
                   '各自形状独立，不存在一处修多支的共同修法。）')
        out.append('')
    # 机制级聚类：family × cls 跨文件
    out.append('### 机制级聚类：`(family, cls)` 跨文件（全量 71，列 ≥2 文件的机制）')
    out.append('')
    m = collections.defaultdict(list)
    for key in sorted(F):
        r = row(key)
        m[(r['family'], r['cls'])].append(r)
    n2 = 0
    for sig, rs in sorted(m.items(), key=lambda kv: -len(kv[1])):
        files = sorted({x['file'] for x in rs})
        if len(files) < 2:
            continue
        n2 += 1
        out.append('- **%s / %s** · n=%d · files=%d %s' % (
            sig[0], sig[1], len(rs), len(files), files))
        for x in rs:
            out.append('    - %-22s %-54s lineA=%s lineB=%s' % (
                x['file'], x['unit'], x['lineA'], x['lineB']))
    out.append('')
    out.append('- 机制级跨文件簇共 %d 个（覆盖 %d/%d 单元）；'
               '同 (family,cls) 即「同一区域归约缺陷在不同文件的投影」，'
               '修一处应同簇多支同时受益。' % (
                   n2, sum(len(rs) for sig, rs in m.items() if len({x['file'] for x in rs}) >= 2),
                   len(F)))
    out.append('')
    # family × cls × file 交叉
    out.append('### 三大头部 `family × cls` 交叉（同构性的粗粒度读数）')
    out.append('')
    tab2 = collections.Counter()
    for key in sorted(F):
        r = row(key)
        if r['file'] in HEAD:
            tab2[(r['family'], r['cls'], r['file'])] += 1
    out.append('| family | cls | ' + ' | '.join(HEAD) + ' | 合计 |')
    out.append('|---|---|' + '---|' * (len(HEAD) + 1))
    seen = sorted({(a, b) for a, b, _ in tab2})
    for a, b in seen:
        cells = [tab2.get((a, b, f), 0) for f in HEAD]
        out.append('| %s | %s | %s | %d |' % (a, b, ' | '.join(str(c) for c in cells), sum(cells)))
    out.append('')
    # 单文件残留统计
    out.append('### 全部 71 单元按文件分布')
    cnt = collections.Counter(k[0] for k in F)
    for f, c in cnt.most_common(15):
        mark = ' <- 三大头部' if f in HEAD else ''
        out.append('- %-34s %d%s' % (f, c, mark))
    out.append('')

    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    print('wrote', OUT, 'cross-file clusters:', n)
    for r, v in verdicts:
        print('  %-22s %-44s cls=%-24s -> %s' % (
            r['file'], r['unit'].split('.')[-1], r['cls'], v[:64]))


if __name__ == '__main__':
    main()
