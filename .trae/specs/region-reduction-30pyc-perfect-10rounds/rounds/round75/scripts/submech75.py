# -*- coding: utf-8 -*-
"""R75 diag1 · submech75.py — 71 失败单元子机理归属探针（只读）。

对每个失败单元（原 pyc 代码对象）跑 LIVE analyzer，采集结构证据：
  orphan   : 区域 parent=None 但 entry 落在别的区域 blocks 内（孤儿子块未发射候选）
  mergeabs : 后代区域 s 的 blocks 吸收了祖先区域 r 的 merge_block/exit（共享尾被吸收候选）
  outpred  : then/else 臂内存在「集外前驱」的块（W14-C 未剪枝的共享汇合点）
  stream   : orig vs ours 指令名流是否相同（相同 => 纯位移族）
  njump    : 参数（跳转目标等）差异条数
  ret      : RETURN_VALUE 计数 orig/ours
  reason   : fam75.json 的首分歧判词

输出 dump/submech75.txt（TSV）+ stdout 汇总。
用法：python -X utf8 submech75.py [unit-filter-substring]
"""
import collections
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
FAM = os.path.join(WORK, 'fam75.json')
OUT = os.path.join(WORK, 'dump', 'submech75.txt')


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


def ops(code):
    return [(i.offset, i.opname, i.arg) for i in dis.get_instructions(code)]


def analyze(code):
    """局部 import，避免 try 内 NameError"""
    sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
    cwd = os.getcwd()
    os.chdir(r'F:/Downloads/pythoncdc-main')
    try:
        from core.cfg import build_cfg
        from core.cfg.region_ast_generator import RegionASTGenerator
        cfg = build_cfg(code)
        gen = RegionASTGenerator(cfg,
                                 top_level_code=code if code.co_name == '<module>' else None)
        regions = gen.region_analyzer.analyze()
    finally:
        os.chdir(cwd)
    return regions


def off(r):
    e = getattr(r, 'entry', None)
    if e is None:
        e = r
    return getattr(e, 'start_offset', None)


def structural(regions):
    """返回 (orphan, mergeabs, outpred) 三个计数与证据行

    orphan  : parent=None 但 entry 落在别的区域 blocks 内（孤儿子块未挂树）
    mergeabs: 后代区域 s 的 blocks 吸收了祖先区域 r 的 merge_block/exit（共享尾被吸进臂内）
    outpred : 臂内块存在「整个区域之外」的前驱（W14-C 应剪而未剪的共享汇合点）
    """
    orphan = 0
    mergeabs = 0
    outpred = 0
    ev = []
    blocks_of = {}
    for r in regions:
        blocks_of[id(r)] = set(getattr(b, 'start_offset', None) for b in (getattr(r, 'blocks', None) or []))
    ent = {}
    for r in regions:
        ent[id(r)] = off(r)
    # 1) orphan-child: child region whose parent's emission block sets
    #    （R74 abs2 口径：blocks/then/else/body/elif/cond/orelse/finalbody/
    #     handler/try）与 child 自身块集无交集 → 父沿子区域发射路径走不到它
    emit_fields = ('blocks', 'then_blocks', 'else_blocks', 'body_blocks',
                   'elif_conditions', 'cond_blocks', 'orelse_blocks',
                   'finalbody_blocks', 'handler_blocks', 'try_blocks',
                   'loop_exit_block', 'tail_block', 'header_block')
    for r in regions:
        p = getattr(r, 'parent', None)
        if p is None:
            continue
        rset = blocks_of[id(r)]
        pset = set()
        for f in emit_fields:
            v = getattr(p, f, None)
            if v is None:
                continue
            if isinstance(v, (list, set, tuple)):
                for x in v:
                    pset.add(getattr(x, 'start_offset', None))
            else:
                pset.add(getattr(v, 'start_offset', None))
        pset.discard(None)
        if rset and not (rset & pset):
            orphan += 1
            ev.append('ORPHAN %s@%s parent=%s@%s child_blocks=%s parent_emit_head=%s'
                      % (type(r).__name__, off(r), type(p).__name__, off(p),
                         sorted(x for x in rset if x is not None)[:8],
                         sorted(pset)[:8]))
    # 1b) parentless region whose entry sits strictly inside another region
    for r in regions:
        if getattr(r, 'parent', None) is not None:
            continue
        e = ent[id(r)]
        if e is None:
            continue
        for q in regions:
            if q is r or off(q) == e:
                continue
            if e in blocks_of[id(q)]:
                orphan += 1
                ev.append('ORPHAN_PARENTLESS %s@%s entry inside %s@%s'
                          % (type(r).__name__, off(r), type(q).__name__, off(q)))
                break
    # 2) mergeabs: strictly-descendant region s absorbs ancestor r's merge/exit
    for r in regions:
        rm = getattr(r, 'merge_block', None)
        rex = getattr(r, 'exit', None)
        cand = set()
        for b in (rm, rex):
            if b is not None:
                cand.add(getattr(b, 'start_offset', None))
        cand.discard(None)
        if not cand:
            continue
        rb = blocks_of[id(r)]
        for s in regions:
            if s is r:
                continue
            se = ent[id(s)]
            if se is None or se == ent[id(r)]:
                continue
            sb = blocks_of[id(s)]
            if not sb or not (sb & cand):
                continue
            if se in rb:
                inter = sb & cand
                mergeabs += 1
                ev.append('MERGEABS r=%s@%s merge=%s  s=%s@%s hit=%s'
                          % (type(r).__name__, off(r), sorted(cand),
                             type(s).__name__, off(s), sorted(inter)))
                break
    # 3) outpred: arm block whose predecessor is outside the WHOLE region
    for r in regions:
        rb = blocks_of[id(r)]
        rentry = off(r)
        rcond = off(getattr(r, 'condition_block', None) or r)
        for fld in ('then_blocks', 'else_blocks'):
            arm = getattr(r, fld, None)
            if not arm:
                continue
            for b in arm:
                bo = getattr(b, 'start_offset', None)
                ext = [p for p in (getattr(b, 'predecessors', None) or [])
                       if getattr(p, 'start_offset', None) not in rb
                       and getattr(p, 'start_offset', None) not in (rentry, rcond)]
                if ext:
                    outpred += 1
                    ev.append('OUTPRED_EXT %s@%s %s blk=%s preds=%s'
                              % (type(r).__name__, off(r), fld, bo,
                                 sorted(getattr(p, 'start_offset', None) for p in ext)))
                    break
    return orphan, mergeabs, outpred, ev


def main():
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    fam = { (x['file'], x['name']): x for x in json.load(io.open(FAM, encoding='utf-8')) }
    g = json.load(io.open(G3, encoding='utf-8'))
    fail = [r for r in g['rows'] if r['status'] != 'success']
    rows = []
    stats = collections.Counter()
    for r in fail:
        pyc = r['pyc']
        rel = pyc.replace('F:/Downloads/pythoncdc-main/site-packages/', '')
        ok = pyc.replace('.pyc', 'OK.py')
        oc_all = load_pyc(pyc)
        try:
            kc_all = compile(io.open(ok, encoding='utf-8').read(), ok, 'exec')
        except Exception as e:
            kc_all = None
        for f in r['failures']:
            nm = f.split('Failure:')[0].strip().lstrip('*').rstrip(':')
            key = nm.split('.', 1)[1] if nm.startswith('<module>.') else nm
            oc = oc_all if key == '<module>' else find(oc_all, key)
            kc = kc_all if (key == '<module>' and kc_all) else (find(kc_all, key) if kc_all else None)
            if oc is None:
                continue
            fam_e = fam.get((rel, nm), {})
            if filt and filt not in rel and filt not in nm:
                continue
            a = ops(oc)
            b = ops(kc) if kc is not None else []
            ro = sum(1 for x in a if x[1] == 'RETURN_VALUE')
            rk = sum(1 for x in b if x[1] == 'RETURN_VALUE')
            stream = (len(a) == len(b)) and all(x[1] == y[1] for x, y in zip(a, b))
            lim = min(len(a), len(b))
            nj = sum(1 for i in range(lim) if a[i][2] != b[i][2])
            if stream and nj == 0:
                cls_stream = 'SAME'
            elif stream:
                cls_stream = 'STREAM_EQ'
            else:
                cls_stream = 'STREAM_NE'
            try:
                regions = analyze(oc)
                orphan, mergeabs, outpred, ev = structural(regions)
            except Exception as e:
                regions, orphan, mergeabs, outpred, ev = [], -1, -1, -1, ['ANALYZE_FAIL %r' % (e,)]
            reason = fam_e.get('reason', '')
            if 'lands on DIFFERENT instr' in reason:
                mcls = 'C-target-diff-instr'
            elif 'lands on SAME instr' in reason:
                mcls = 'C2-target-same-instr'
            elif reason.startswith('opname'):
                mcls = 'C3-opname-diff'
            elif 'target instr same but len' in reason:
                mcls = 'D-or-len'
            else:
                mcls = '?'
            if mergeabs > 0:
                cls = 'a-shared-merge-absorbed'
            elif orphan > 0:
                cls = 'b-orphan-child'
            elif outpred > 0:
                cls = 'a2-shared-tail-extpred'
            elif mcls in ('C-target-diff-instr', 'C3-opname-diff'):
                cls = 'c-target-diff-instr'
            elif mcls in ('C2-target-same-instr', 'D-or-len'):
                cls = 'd-displacement'
            else:
                cls = 'other'
            rows.append(dict(file=rel, unit=nm, family=fam_e.get('family', '?'),
                             cls=cls,
                             verdict=fam_e.get('verdict', '?'),
                             lenA=fam_e.get('lenA'), lenB=fam_e.get('lenB'),
                             firstA=fam_e.get('firstA', ''), firstB=fam_e.get('firstB', ''),
                             lineA=fam_e.get('lineA'), lineB=fam_e.get('lineB'),
                             reason=reason, mcls=mcls, stream=cls_stream,
                             njump=nj, ret='%d/%d' % (ro, rk),
                             orphan=orphan, mergeabs=mergeabs, outpred=outpred,
                             ev=' || '.join(ev[:6])))
            stats[(fam_e.get('family', '?'), cls_stream, mcls)] += 1
    head = ('file\tunit\tfamily\tcls\tverdict\tlenA\tlenB\tmcls\tstream\tnjump\tret\t'
            'orphan\tmergeabs\toutpred\tlineA\tlineB\tfirstA\tfirstB\treason\tevidence')
    lines = [head]
    for d in rows:
        lines.append('\t'.join(str(d[k]) for k in
                               ('file', 'unit', 'family', 'cls', 'verdict', 'lenA', 'lenB', 'mcls',
                                'stream', 'njump', 'ret', 'orphan', 'mergeabs', 'outpred',
                                'lineA', 'lineB', 'firstA', 'firstB', 'reason', 'ev')))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('rows=%d -> %s' % (len(rows), OUT))
    agg = collections.Counter()
    for d in rows:
        agg[(d['family'], d['cls'])] += 1
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
        print('%3d  %s' % (v, k))
    print('--- structural flags ---')
    fl = collections.Counter()
    for d in rows:
        fl[(d['family'], 'orphan>0' if d['orphan'] > 0 else 'orphan=0',
            'mergeabs>0' if d['mergeabs'] > 0 else 'mergeabs=0',
            'outpred>0' if d['outpred'] > 0 else 'outpred=0')] += 1
    for k, v in sorted(fl.items(), key=lambda kv: -kv[1]):
        print('%3d  %s' % (v, k))
    print('--- flag incidence (units with count>0) ---')
    inc = collections.Counter()
    for d in rows:
        for k in ('orphan', 'mergeabs', 'outpred'):
            try:
                if int(d[k]) > 0:
                    inc[(d['family'], k)] += 1
            except ValueError:
                inc[(d['family'], k + '_fail')] += 1
    for k, v in sorted(inc.items()):
        print('%3d  %s' % (v, k))
    print('--- class x family ---')
    cf = collections.Counter((d['family'], d['cls']) for d in rows)
    for k, v in sorted(cf.items()):
        print('%3d  %s' % (v, k))


if __name__ == '__main__':
    main()
