#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**PIPELINE-DEFECT 归因的复核**。

`miss_attribution.py` 的 `judge` 指纹把 `opname` 与 `argval` 放进同一个元组比较，
而附件判据 `equivalence_check.py:50-51` 对**无条件跳转**只比 `argval`
⇒ 无条件跳转的 opname 差异会被本工具误记为 PIPELINE-DEFECT。

本脚本复核：对每一条 PIPELINE-DEFECT 记录，检查「把无条件跳转的 opname/opcode 抹平后
两侧是否相同」：
  * 相同 ⇒ 该例应改判为 **JUMP-DIRECTION-BLIND**（对应破口 B196）
  * 仍不同 ⇒ 才是真正的判据管线缺陷

用法：
  python -X utf8 pipeline_defect_recheck.py <miss_attribution.json> [...]
"""
from __future__ import annotations

import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import miss_attribution as MA  # noqa: E402

JUDGE_FIELDS = MA.JUDGE_FIELDS


def fp_nojumpop(pyc_path, PYCFile, patches):
    """与 MA 的 'judge' 相同，但把无条件跳转的 opname/opcode 抹平。"""
    f = PYCFile(pyc_path)
    f.apply_patches(list(patches))
    out = []
    for bc in f.iter_bytecodes():
        items = []
        for i in bc:
            av = i.argval
            if isinstance(av, types.CodeType):
                av = ('code', av.co_name)
            opname = getattr(i, 'opname', None)
            opcode = getattr(i, 'opcode', None)
            if i.is_uncond_jump:
                opname, opcode = '<uncond-jump>', '<uncond-jump>'
            items.append((opname, opcode) + tuple(getattr(i, k, None)
                                                  for k in JUDGE_FIELDS[2:]) + (av,))
        out.append((bc.name, items))
    out.sort(key=lambda r: (r[0], repr(r[1])))
    return out


def main():
    PYCFile, patches = MA.load_pyc()
    import py_compile
    import tempfile
    tmp = tempfile.mkdtemp(prefix='pdrecheck_')
    sys.path.insert(0, HERE)
    import mutation_lib

    for path in sys.argv[1:]:
        d = json.load(open(path, encoding='utf-8'))
        rows = [r for r in d['rows'] if r.get('attribution') == 'PIPELINE-DEFECT']
        print('== %s : PIPELINE-DEFECT rows = %d' % (os.path.basename(path), len(rows)))
        jump = 0
        other = []
        for r in rows:
            prod = r['pyc'][:-4] + 'OK.py'
            raw = open(prod, 'rb').read()
            mut, _ = mutation_lib.apply_mutation(r['family'], raw)
            if mut is None:
                continue
            mpy = os.path.join(tmp, 'm.py')
            open(mpy, 'wb').write(mut)
            mpyc = os.path.join(tmp, 'm.pyc')
            py_compile.compile(mpy, cfile=mpyc, doraise=True, optimize=0)
            a = fp_nojumpop(r['pyc'], PYCFile, patches)
            b = fp_nojumpop(mpyc, PYCFile, patches)
            if a == b:
                jump += 1
            else:
                other.append((r['family'], r['pyc']))
        print('   抹平无条件跳转 opname 后两侧相同 => JUMP-DIRECTION-BLIND : %d' % jump)
        print('   仍不同（真·管线缺陷）                                    : %d' % len(other))
        for fam, p in other[:10]:
            print('     ', fam, p)


if __name__ == '__main__':
    main()
