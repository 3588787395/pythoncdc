#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AT-01/AT-05 守卫活性探针：检验 `IfRegion.get_offset_range` 的「更近循环」守卫
是否在**实际调用时刻**可判定。

论断（待验）：`IfRegion.get_offset_range`（region_analyzer.py:446-479）在判定
「是否存在更近的 LoopRegion」时扫描 `analyzer.regions`（:460）；而
`analyzer.regions` 在 `RegionAnalyzer.__init__`（:1227）被初始化为 `[]`，
直到 `analyze()` 的 `self.regions = all_regions`（:1987）才被填充。
`_build_region_hierarchy`（:1960 调用）先于 :1987 ⇒ 守卫在调用时刻读到空表，
恒判 `_has_closer_loop = False` ⇒ 守卫为**死代码**。

用法：python -X utf8 l0_guard_liveness_probe.py --dir <probes dir> [--out <json>]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from l0_partition_probe import iter_code_objects, build_code  # noqa: E402


def probe(code):
    from core.cfg import build_cfg
    from core.cfg import region_analyzer as RA
    cfg = build_cfg(code)
    analyzer = RA.RegionAnalyzer(cfg)

    stats = {'calls': 0, 'calls_with_empty_regions': 0, 'expansion_fired': 0,
             'closer_loop_found': 0, 'regions_len_at_call': []}

    orig_get_range = RA.IfRegion.get_offset_range

    def patched(self, an):
        stats['calls'] += 1
        n = len(an.regions)
        stats['regions_len_at_call'].append(n)
        if n == 0:
            stats['calls_with_empty_regions'] += 1
        # 复制上游逻辑，仅为统计 expansion / closer_loop 两个分支
        if not self.blocks:
            return (0, 0)
        offsets = [b.start_offset for b in self.blocks]
        for _tb in (self.then_blocks or []):
            for _succ in _tb.successors:
                _sr = an.block_to_region.get(_succ)
                if (isinstance(_sr, RA.TryExceptRegion) and _sr.entry is _succ
                        and _sr is not self):
                    _has_closer_loop = False
                    base = (min(offsets), max(offsets)) if offsets else (0, 0)
                    _te = an._get_region_offset_range(_sr)
                    _exp = (min(base[0], _te[0]), max(base[1], _te[1]))
                    for _lr in an._filter_regions(an.regions, RA.LoopRegion):
                        if _lr is not self and _lr.entry:
                            _lrng = an._get_region_offset_range(_lr)
                            if (not (_lrng[0] >= _te[0] and _lrng[1] <= _te[1])
                                    and _lrng[0] >= _exp[0] and _lrng[1] <= _exp[1]
                                    and (_lrng[1] - _lrng[0]) < (_exp[1] - _exp[0])):
                                _has_closer_loop = True
                                break
                    if _has_closer_loop:
                        stats['closer_loop_found'] += 1
                    else:
                        stats['expansion_fired'] += 1
                        for _cb in _sr.try_blocks:
                            offsets.append(_cb.start_offset)
                        for _, _, _hb in _sr.except_handlers:
                            for _h in _hb:
                                offsets.append(_h.start_offset)
                        for _eb in (_sr.else_blocks or []):
                            offsets.append(_eb.start_offset)
                        for _fb in (_sr.finally_blocks or []):
                            offsets.append(_fb.start_offset)
        return (min(offsets), max(offsets))

    RA.IfRegion.get_offset_range = patched
    try:
        analyzer.analyze()
    finally:
        RA.IfRegion.get_offset_range = orig_get_range
    return stats


def main():
    args = sys.argv[1:]
    srcdir = None
    out = None
    i = 0
    while i < len(args):
        if args[i] == '--dir':
            srcdir = args[i + 1]; i += 2
        elif args[i] == '--out':
            out = args[i + 1]; i += 2
        else:
            i += 1
    if not srcdir:
        print(__doc__)
        return 2
    srcdir = os.path.abspath(srcdir)
    rows = []
    for name in sorted(os.listdir(srcdir)):
        if not name.endswith('.pyc'):
            continue
        code = build_code(os.path.join(srcdir, name))
        for co in iter_code_objects(code):
            try:
                st = probe(co)
            except Exception as exc:
                st = {'error': '%s: %s' % (type(exc).__name__, exc)}
            row = {'pyc': name, 'code': getattr(co, 'co_name', '?')}
            row.update(st)
            rows.append(row)
            print('[%s::%s] calls=%s empty_regions=%s expansion=%s closer_loop=%s' % (
                name, row['code'], st.get('calls'), st.get('calls_with_empty_regions'),
                st.get('expansion_fired'), st.get('closer_loop_found')))
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print('-> wrote %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
