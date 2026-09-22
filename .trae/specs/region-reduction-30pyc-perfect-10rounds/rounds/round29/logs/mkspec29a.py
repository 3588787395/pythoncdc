# -*- coding: utf-8 -*-
"""Round 29 candidate R29-A spec: 原则-2 arm-exclusive claim at the IF_THEN/IF_THEN_ELSE
construction boundary of core/cfg/region_analyzer.py.

Measured trigger (probe arm p29d, this session, load_daily :: <module>):
  site=17888 entry=740 merge=2626 else=[2456, 2478, 2562]
                         then=[..., 2198, 1932, 2022, 2478, 2086, 2176, 2562]
i.e. blocks 2478 and 2562 are claimed by BOTH arms of the SAME IfRegion, and the
generator's `_process_if_blocks` iterates each arm sorted by start_offset, so the
then arm emits the join block @2478 (the post-if statement) before the else arm has
finished -- the count-neutral transposition measured as [913,913,jump=1,true=19].

The predicate reads only block identity/ownership (the two arm lists of the region
being built) and never offsets-as-constants, names, or counts; `all_blocks` is the
union of the two lists so the block is not lost, only un-double-claimed: removal-only.

  python -X utf8 mkspec29a.py            # writes spec json, prints accounting
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r29gate'
REL = 'core/cfg/region_analyzer.py'
sys.stdout.reconfigure(encoding='utf-8')

raw = io.open(os.path.join(REPO, REL.replace('/', os.sep)), 'rb').read()
src = raw.decode('utf-8-sig')
nl = '\r\n' if '\r\n' in src else '\n'
u = src.replace('\r\n', '\n')
lines = u.split('\n')

ANCHOR = '        region_type = RegionType.IF_THEN_ELSE if else_blocks else RegionType.IF_THEN'
idx = [i for i, l in enumerate(lines) if l == ANCHOR]
assert len(idx) == 1, 'anchor occurrences=%d' % len(idx)
i = idx[0]
print('anchor context:')
for k in range(i - 2, i + 3):
    print('  %d|%s' % (k + 1, lines[k][:100]))
assert lines[i + 1].startswith('        all_blocks'), lines[i + 1][:80]

GUARD = [
    "        # 区域归约算法原则 2（每块唯一归属）：两条臂是互斥的控制流路径，同一个块",
    "        # 不可能既是 then 体又是 else 体。被两臂同时认领的块只能是由两臂共同到达的",
    "        # 汇合点——它按定义位于两臂入口之后，两臂中任一臂把它当作自己的体内块都是",
    "        # 越界吸收。实测形状（fly/dumpload/load_daily.pyc :: <module>）：",
    "        # IfRegion(entry=740) 的 then=[…,2176,2478,2562] 与 else=[2456,2478,2562]",
    "        # 共享 2478/2562，而 `_process_if_blocks` 对每条臂按 start_offset 升序发射，",
    "        # 于是 then 臂先于 else 臂发射了 if/else 之后的语句块 2478，实测为指令数不变、",
    "        # 只有一个跳转槽错位的同形块换位（orig 的 `JUMP_FORWARD→2478` + 2456 臂体整体",
    "        # 后移，逐字重现在 2538）。判据只读块自身的归属状态（两臂列表的交），不读",
    "        # 偏移常量／名字／条数；all_blocks 是两臂之并，从 then 臂摘出不丢失任何块，",
    "        # 只是取消双重认领——只删不增，不命中时行为逐字节不变。",
    "        if then_blocks and else_blocks:",
    "            _arm_shared = set(then_blocks) & set(else_blocks)",
    "            if _arm_shared:",
    "                then_blocks = [b for b in then_blocks if b not in _arm_shared]",
]

anchor_txt = ANCHOR
assert u.count(anchor_txt) == 1, 'anchor-with-context occurrences=%d' % u.count(anchor_txt)
repl = '\n'.join(GUARD) + '\n' + ANCHOR
edits = [{'anchor': anchor_txt, 'repl': repl}]
for k, e in enumerate(edits):
    assert u.count(e['anchor']) == 1 and u.count(e['repl']) == 0, k
patched = u.replace(anchor_txt, repl)
assert patched != u
io.open('%s/spec29a.json' % OUT, 'w', encoding='utf-8').write(
    json.dumps({'file': REL, 'edits': edits}, ensure_ascii=False))
print('spec written: %s, inserted lines=%d, nl=%s, BOM=%s'
      % (REL, len(GUARD), 'CRLF' if nl == '\r\n' else 'LF', raw[:3] == b'\xef\xbb\xbf'))
