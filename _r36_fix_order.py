#!/usr/bin/env python3
"""Apply R36 fix-3: move BoolOpRegion/TernaryRegion collection before IfRegion in else branch."""

FILE = r"f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py"

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Move the BoolOpRegion/TernaryRegion collection (phase 3) to BEFORE IfRegion (phase 2).
# The issue: value-context chained compare IfRegions claim their merge_block
# (which is also the BoolOpRegion's entry) via _claimed_blocks_c3, preventing
# BoolOpRegion collection. By collecting BoolOpRegion first, its entry is
# claimed, and then the IfRegion whose entry is different (the condition_block)
# can still be processed normally.

old = """            # 第一阶段：复合子区域（Try/With/Loop）
            for child in (region.children or []):
                if not isinstance(child, (TryExceptRegion, WithRegion, LoopRegion)):
                    continue
                _try_collect_c3(child)
            # 第二阶段：IfRegion 子区域（含 R10-N4 修复，识别嵌套 if/elif）
            for child in (region.children or []):
                if not isinstance(child, IfRegion):
                    continue
                # 跳过 is_empty_then_chained_compare 的子 IfRegion
                # 这种子区域是链式比较模式的内部结构，不是真正的 if 语句
                # （镜像 then 分支 L8462-8465）。
                if getattr(child, 'is_empty_then_chained_compare', False):
                    for b in child.blocks:
                        self.generated_blocks.add(b)
                    continue
                _try_collect_c3(child)
            # [R36 fix-2] Third phase: BoolOpRegion / TernaryRegion children.
            # Value-expression regions in the else branch (e.g. `return
            # (a < b < c) or (d < e < f)`) are not collected by phases 1/2.
            # Without this, their blocks are processed as sequential blocks,
            # producing garbage statements. Collecting them allows
            # _generate_region -> _generate_boolop to properly rebuild the
            # expression (including _try_build_chained_compare_in_boolop).
            for child in (region.children or []):
                if not isinstance(child, (BoolOpRegion, TernaryRegion)):
                    continue
                _try_collect_c3(child)
            _entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}"""

new = """            # 第一阶段：复合子区域（Try/With/Loop）
            for child in (region.children or []):
                if not isinstance(child, (TryExceptRegion, WithRegion, LoopRegion)):
                    continue
                _try_collect_c3(child)
            # [R36 fix-3] Second phase: BoolOpRegion / TernaryRegion children.
            # Must be collected BEFORE IfRegion children. Value-context chained
            # compare IfRegions have merge_block == BoolOpRegion entry. If
            # IfRegion is collected first, it claims the merge_block via
            # _claimed_blocks_c3, preventing BoolOpRegion collection.
            # By collecting BoolOpRegion first, its entry is claimed, and then
            # the value-context IfRegion (whose entry is its condition_block,
            # not the merge_block) can be skipped properly.
            for child in (region.children or []):
                if not isinstance(child, (BoolOpRegion, TernaryRegion)):
                    continue
                _try_collect_c3(child)
            # 第三阶段：IfRegion 子区域（含 R10-N4 修复，识别嵌套 if/elif）
            for child in (region.children or []):
                if not isinstance(child, IfRegion):
                    continue
                # 跳过 is_empty_then_chained_compare 的子 IfRegion
                # 这种子区域是链式比较模式的内部结构，不是真正的 if 语句
                # （镜像 then 分支 L8462-8465）。
                if getattr(child, 'is_empty_then_chained_compare', False):
                    for b in child.blocks:
                        self.generated_blocks.add(b)
                    continue
                _try_collect_c3(child)
            _entry_to_child_c3 = {c.entry: c for c in _reachable_children_c3}"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fix applied: moved BoolOpRegion/TernaryRegion collection before IfRegion")
else:
    print("ERROR: old string not found!")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
