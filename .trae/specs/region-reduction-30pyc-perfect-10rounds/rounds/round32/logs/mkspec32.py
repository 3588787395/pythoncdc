# -*- coding: utf-8 -*-
"""Round 32 line C: write the R32-C candidate spec (POP_TOP is a statement terminator in the
comprehension prefix scanner) and allow the harness to patch that third core file.

  python -X utf8 mkspec32.py
"""
import io
import json
import os
import sys

DST = r'D:/Temp/r32gate/c1'
SEP = chr(92)
sys.stdout.reconfigure(encoding='utf-8')

ANCHOR = ("        for instr in pre_instrs:\n"
          "            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):\n"
          "                continue\n")
REPL = ("        for instr in pre_instrs:\n"
        "            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):\n"
        "                continue\n"
        "            if instr.opname == 'POP_TOP':\n"
        "                # [R32-C 同层判据 · 原则 1 块 = 前导语句 + 尾终止] POP_TOP 是「栈上的值被\n"
        "                # 丢弃」的语句终止符，不是填充指令 —— 调用方把「pre_comp_instrs 末尾是\n"
        "                # STORE/POP_TOP/IMPORT」当作语句边界，本扫描器却把同一 op 当噪声滤掉，\n"
        "                # 两侧必须同层一致。它闭合此前累积的栈上表达式并作为 Expr 语句发射；累积\n"
        "                # 段为空（该行没有值被丢弃）时与既有行为逐字节相同。\n"
        "                if current_instrs:\n"
        "                    _r32c_expr = self.expr_reconstructor.reconstruct(current_instrs)\n"
        "                    if _r32c_expr:\n"
        "                        stmts.append({'type': 'Expr', 'value': _r32c_expr})\n"
        "                current_instrs = []\n"
        "                continue\n")

rel = 'core/cfg/comprehension_generator.py'
src = io.open(r'F:/Downloads/pythoncdc-main' + SEP + rel.replace('/', SEP), encoding='utf-8').read()
assert src.count(ANCHOR) == 1, src.count(ANCHOR)
spec = {'file': rel, 'edits': [{'anchor': ANCHOR, 'repl': REPL}]}
io.open(DST + '/spec_r32c.json', 'w', encoding='utf-8', newline='').write(
    json.dumps(spec, ensure_ascii=False, indent=1))

h = io.open(DST + '/r32c.py', encoding='utf-8', newline='').read()
old = "    assert rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py'), rel"
assert h.count(old) == 1
new = ("    assert rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',\n"
       "                    'core/cfg/comprehension_generator.py'), rel")
io.open(DST + '/r32c.py', 'w', encoding='utf-8', newline='').write(h.replace(old, new))
print('spec written (repl adds %d lines); harness extended to %s'
      % (REPL.count('\n') - ANCHOR.count('\n'), rel))
