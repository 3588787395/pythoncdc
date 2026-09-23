# -*- coding: utf-8 -*-
"""Write the spec for the nested-ternary-in-comprehension candidate (anchor-checked)."""
import io
import json

REPO = r'F:\Downloads\pythoncdc-main'
P = 'core/cfg/comprehension_generator.py'
src = io.open(REPO + '/' + P, encoding='utf-8', newline='').read().replace(chr(13), '')

ANCHOR = (
    "        # 重建false值表达式\n"
    "        false_expr = self.expr_reconstructor.reconstruct(false_instrs)\n"
    "        if false_expr is None:\n"
    "            return None\n")

REPL = (
    "        # 重建false值表达式。嵌套三元链归约（innermost→outermost）：CPython 对\n"
    "        # `a if c else (b if d else e)` 在 false 区域内再生成一次「条件 → 前向条件跳转\n"
    "        # → true 臂 → JUMP_FORWARD 到同一个 merge」，即 false 区域本身又是一个三元区域。\n"
    "        # 识别条件：false_instrs 内含至少一条前向条件跳转（BACKWARD 条件是推导式的 filter\n"
    "        # 回边，不算）。归约方式：以 false_start 为新的扫描起点递归调用本方法，先把内层\n"
    "        # 三元归约为一个 IfExp 抽象节点，再由外层持有为 orelse——内层区域整体作为父节点的\n"
    "        # 一个抽象结点，符合「每块唯一归属」。AST 映射：IfExp(test, body, IfExp(...))。\n"
    "        # 递归返回 None（内层并非三元，或通用重建器本就能处理）时逐字回落到原路径，\n"
    "        # 因此该判据是严格附加的，不改变任何现有可正常重建的产物结构。\n"
    "        false_expr = None\n"
    "        if any(_fi.opname in CONDITIONAL_JUMP_OPS and 'BACKWARD' not in _fi.opname\n"
    "               for _fi in false_instrs):\n"
    "            false_expr = self._detect_comp_ternary(all_instrs, false_start - 1, append_idx)\n"
    "        if false_expr is None:\n"
    "            false_expr = self.expr_reconstructor.reconstruct(false_instrs)\n"
    "            if false_expr is None:\n"
    "                return None\n")

n = src.count(ANCHOR)
print('anchor occurrences =', n)
assert n == 1, 'anchor is not unique — pick a longer anchor'
assert src.count(REPL) == 0
json.dump({'file': P, 'edits': [{'anchor': ANCHOR, 'repl': REPL}]},
          io.open(r'D:/Temp/r54mine55/spec_c54comp.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('spec written ; repl lines =', REPL.count(chr(10)))
