# -*- coding: utf-8 -*-
"""Build spec_c1c.json: the landing form of R30-C1 = the measured (comment-free) 6-line patch
plus a house-style 判据 comment block.  The code lines are copied verbatim from spec_c1.json so
the landing cannot drift from what was measured."""
import io
import json

BASE = json.load(io.open(r'D:/Temp/r30gate/c1/spec_c1.json', encoding='utf-8'))
e = BASE['edits'][0]
anchor, repl = e['anchor'], e['repl']
prefix = ('            if break_blocks:\n'
          '                for break_block in break_blocks:\n')
assert anchor.startswith(prefix)
suffix = anchor[len(prefix):]
assert repl == prefix + repl[len(prefix):-len(suffix)] + suffix, 'measured patch is not an insertion'
INSERTED = repl[len(prefix):-len(suffix)]
assert INSERTED.count('\n') == 6 and INSERTED.startswith('                    _r30c1_last'), INSERTED

COMMENT = '\n'.join([
    '                    # R30-C1（原则 2 每块唯一归属 · break 角色侧）：候选 break 块是离开本区域的',
    '                    # 块，若它的终止指令属于向后跳转类而落点又不是本区域的头部，那条边就是**外层**',
    '                    # loop 的回边而不是本 loop 的 break 出口 —— 不核验、不并入区域块集，它也就不被',
    '                    # 内层渲染的批量入账变成无人发射的块。只读块自身（终止指令的 opname 类＋落点与',
    '                    # 头部的同一性），不读偏移常量／名字／条数；只删不增，不命中时逐字节不变。',
]) + '\n'

out = {'file': BASE['file'],
       'edits': [{'anchor': anchor, 'repl': prefix + COMMENT + INSERTED + suffix}]}
p = r'D:/Temp/r30gate/c1/spec_c1c.json'
io.open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False))
u = json.load(io.open(p, encoding='utf-8'))
n_ins = u['edits'][0]['repl'].count('\n') - u['edits'][0]['anchor'].count('\n')
print('wrote %s  inserted lines = %d (5 comment + 6 code)' % (p, n_ins))
assert n_ins == 11, n_ins
