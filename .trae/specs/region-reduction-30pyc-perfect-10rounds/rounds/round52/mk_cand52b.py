# -*- coding: utf-8 -*-
"""Emit the R52-B spec: chained-compare region must not claim the join block as its else arm."""
import io
import json

LF = chr(10)

ANCHOR = LF.join([
    '        else_blocks = _resolved_else_blocks',
    '        region = IfRegion(',
    '            region_type=RegionType.IF, entry=header, blocks=all_blocks,',
])

REPL = LF.join([
    '        else_blocks = _resolved_else_blocks',
    '        # [R52-B 同层归属判据 · 臂间正常流] 区域归约算法原则 2（两条臂互斥）：',
    '        # 一个块不可能既属 then 臂又属 else 臂，且 then 臂的任何块都不能以正常流',
    '        # 【进入】else 臂的头块——CPython 编译 `if A: T else: E`（比较链形态同此）',
    '        # 必然在 T 臂末发射一条越过 E 的 JUMP_FORWARD 落到两臂汇合点。若 T 臂中某块',
    '        # 把 E 的头块列为后继，则该头块就是「A 为假」时的落点、即两臂的汇合点本身；',
    '        # 把它当 else 臂会让发射侧凭空为 T 臂补一条原函数并不存在的越臂跳转',
    '        # （strict seq_len +1。靶 IQCommon/api/klinedata.pyc :: <module>._all_bars_of_cache',
    '        # orig=230 decomp=231：比较链 `if start_date < \'20050101\' <= end_date:` 的臂体块',
    '        # 246 以正常流落入块 250，而 250 是臂后那条兄弟语句 `if history_cache == 1:`',
    '        # 的条件块，本方法原先把它认领为 real_else=else_blocks[0]）。',
    '        # 命中时按「无 else 的比较链 if」归约：else_blocks 置空、merge_block 取该头块，',
    '        # 并把它从 all_blocks 摘出——其后语句保持未认领，由父层作兄弟节点发射',
    '        # （原则 4：父以子区域 entry 引用之）。判据只读 then/else 块集与 successors',
    '        # 关系，不读名字、常量、绝对偏移、指令数与历史清单；不命中时逐字节不变。',
    '        _r52b_else_head = else_blocks[0] if else_blocks else None',
    '        if _r52b_else_head is not None and _blocks:',
    '            if any(_r52b_else_head in (tb.successors or set()) for tb in _blocks):',
    '                for _r52b_b in list(else_blocks):',
    '                    if _r52b_b is not None:',
    '                        all_blocks.discard(_r52b_b)',
    '                else_blocks = []',
    '                merge_block = _r52b_else_head',
    '        region = IfRegion(',
    '            region_type=RegionType.IF, entry=header, blocks=all_blocks,',
])

spec = {'file': 'core/cfg/region_analyzer.py', 'anchor': ANCHOR, 'repl': REPL}
io.open(r'D:/Temp/r52gate/spec_r52b.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
src = io.open(r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py',
              encoding='utf-8', newline='').read().replace('\r\n', '\n')
print('anchor occurrences =', src.count(ANCHOR))
print('inserted lines =', len(REPL.split(LF)) - len(ANCHOR.split(LF)))
