#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**PIPELINE-DEFECT 残留差异的逐指令定位**。

`pipeline_defect_recheck.py` 把「归一化后两侧仍不同」的 PIPELINE-DEFECT 拆成两类：
  * 抹平**无条件跳转 opname** 后相同 ⇒ JUMP-DIRECTION-BLIND（破口 B196 的面）
  * 抹平后**仍不同** ⇒ 真·判据管线缺陷（本脚本定位到**具体指令与具体字段**）

本脚本对后者逐指令对比（判据字段集 + argval），打印第一处不一致的
code object / offset / opname / argval 两侧取值 ⇒ 给出可复现的根因坐标。

输出：`_out/pipeline_defect_detail.json`（+ 标准输出摘要）
用法：python -X utf8 pipeline_defect_detail.py [miss_attribution.json ...]
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
OUT = os.path.join(ROUND4, '_out')
sys.path.insert(0, HERE)
import miss_attribution as MA  # noqa: E402
import mutation_lib  # noqa: E402
import pipeline_defect_recheck as PDR  # noqa: E402


def fp_uncond_argval_only(pyc_path, PYCFile, patches):
    """最严格的一档：对**无条件跳转**只保留 argval（等价于判据 eq:50-51 的早退分支
    实际比较的全部内容），其余指令保留判据字段集 + argval。"""
    f = PYCFile(pyc_path)
    f.apply_patches(list(patches))
    out = []
    for bc in f.iter_bytecodes():
        items = []
        for i in bc:
            av = i.argval
            if isinstance(av, types.CodeType):
                av = ('code', av.co_name)
            if i.is_uncond_jump:
                items.append(('<uncond-jump>', av))
            else:
                items.append(tuple(getattr(i, k, None) for k in MA.JUDGE_FIELDS) + (av,))
        out.append((bc.name, items))
    out.sort(key=lambda r: (r[0], repr(r[1])))
    return out


def diff_detail(a, b):
    """a/b：[(bc_name, [(opname, opcode, optype, real_size, has_arg,
                        has_extended_arg, offset, is_jump_target, argval), ...]), ...]
    返回第一处不一致的坐标。"""
    names = sorted({n for n, _ in a} | {n for n, _ in b})
    da = dict(a)
    db = dict(b)
    for n in names:
        ia = da.get(n) or []
        ib = db.get(n) or []
        if len(ia) != len(ib):
            return {'code_object': n, 'kind': 'length', 'a_len': len(ia), 'b_len': len(ib)}
        for k, (x, y) in enumerate(zip(ia, ib)):
            if x != y:
                diffs = []
                labels = ['opname', 'opcode', 'optype', 'real_size', 'has_arg',
                          'has_extended_arg', 'offset', 'is_jump_target', 'argval']
                for lbl, xv, yv in zip(labels, x, y):
                    if xv != yv:
                        diffs.append({'field': lbl, 'a': repr(xv)[:120],
                                      'b': repr(yv)[:120]})
                return {'code_object': n, 'kind': 'field', 'index': k, 'diffs': diffs}
    return {'kind': 'equal'}


def main() -> int:
    PYCFile, patches = MA.load_pyc()
    tmp = tempfile.mkdtemp(prefix='pddetail_')
    paths = sys.argv[1:] or [os.path.join(OUT, 'miss_attribution.json'),
                             os.path.join(OUT, 'miss_attribution_extra.json')]
    report = []
    for path in paths:
        d = json.load(open(path, encoding='utf-8'))
        rows = [r for r in d['rows'] if r.get('attribution') == 'PIPELINE-DEFECT']
        for r in rows:
            prod = r['pyc'][:-4] + 'OK.py'
            if not os.path.isfile(prod):
                continue
            raw = open(prod, 'rb').read()
            mut, site = mutation_lib.apply_mutation(r['family'], raw)
            if mut is None:
                continue
            mpy = os.path.join(tmp, 'm.py')
            open(mpy, 'wb').write(mut)
            mpyc = os.path.join(tmp, 'm.pyc')
            py_compile.compile(mpy, cfile=mpyc, doraise=True, optimize=0)
            a = PDR.fp_nojumpop(r['pyc'], PYCFile, patches)
            b = PDR.fp_nojumpop(mpyc, PYCFile, patches)
            if a == b:
                # 仅 opname/opcode 不同 ⇒ JUMP-DIRECTION-BLIND（eq:50-51 早退分支）
                c = fp_uncond_argval_only(r['pyc'], PYCFile, patches)
                e = fp_uncond_argval_only(mpyc, PYCFile, patches)
                report.append({'source': os.path.basename(path), 'family': r['family'],
                               'pyc': r['pyc'], 'site': site,
                               'bucket': 'JUMP-DIRECTION-BLIND' if c == e
                               else 'JUMP-ATTRLIST-BLIND',
                               'detail': diff_detail(c, e) if c != e else None})
                continue
            # 抹平 opname/opcode 后仍不同 ⇒ 再看「只保留 argval」是否相同
            c = fp_uncond_argval_only(r['pyc'], PYCFile, patches)
            e = fp_uncond_argval_only(mpyc, PYCFile, patches)
            det = diff_detail(a, b)
            report.append({'source': os.path.basename(path), 'family': r['family'],
                           'pyc': r['pyc'], 'site': site,
                           'bucket': 'JUMP-ATTRLIST-BLIND' if c == e else 'TRUE-PIPELINE-DEFECT',
                           'detail': det})
    out = os.path.join(OUT, 'pipeline_defect_detail.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'rows': report, 'count': len(report),
                   'buckets': {b: sum(1 for r in report if r['bucket'] == b)
                               for b in sorted({r['bucket'] for r in report})}},
                  f, ensure_ascii=False, indent=1)
    import collections
    buckets = collections.Counter(r['bucket'] for r in report)
    print('PIPELINE-DEFECT 例数：%d' % len(report))
    for b, n in sorted(buckets.items()):
        print('  %-26s %d' % (b, n))
    seen = set()
    for r in report:
        key = (r['pyc'], r['bucket'])
        if key in seen:
            continue
        seen.add(key)
        print('  %-40s %-26s %s' % (os.path.basename(r['pyc']), r['bucket'],
                                    json.dumps(r['detail'], ensure_ascii=False)[:200] if r['detail'] else ''))
    print('-> %s' % out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
