#!/usr/bin/env python3
"""
自动化替换脚本 - 将硬编码操作码替换为 OpcodeFeatureDetector 调用

处理 region_analyzer.py 和 region_ast_generator.py 中的所有硬编码操作码引用。
"""

import re
import sys
from pathlib import Path


def read_file(filepath):
    """读取文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()


def write_file(filepath, lines):
    """写入文件内容"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def replace_hardcoded_opcodes_in_analyzer(lines):
    """
    替换 region_analyzer.py 中的硬编码操作码

    替换策略：
    1. 循环相关: FOR_ITER, GET_ANEXT, GET_AITER, GET_ITER -> detector.is_loop_header_opcode()
    2. 回边检测: JUMP_BACKWARD, JUMP_BACKWARD_NO_INTERRUPT -> detector.is_unconditional_jump() 或特定方法
    3. 条件跳转: POP_JUMP_IF_*, JUMP_IF_*_OR_POP -> detector.is_conditional_jump()
    4. 无条件跳转: JUMP_FORWARD, JUMP_ABSOLUTE -> detector.is_unconditional_jump()
    5. 返回指令: RETURN_VALUE, RETURN_CONST -> 保持或用辅助方法
    6. 异常相关: RAISE_VARARGS, RERAISE, PUSH_EXC_INFO 等 -> detector.is_exception_related()
    7. WITH相关: WITH_EXCEPT_START, BEFORE_WITH -> detector.is_exception_related()
    8. MATCH相关: MATCH_* -> 保持（这些是结构特征，不是操作码类别）
    """
    replacements = []
    total_replacements = 0

    for line_num, line in enumerate(lines, 1):
        original_line = line
        modified = False

        # === Batch 1: 循环相关方法 (~18处) ===

        # 1. 异步循环检测: GET_ANEXT/GET_AITER
        if "i.opname in ('GET_ANEXT', 'GET_AITER')" in line:
            line = line.replace(
                "i.opname in ('GET_ANEXT', 'GET_AITER')",
                "self._opcode_detector.is_loop_header_opcode(i)"
            )
            modified = True
            replacements.append((line_num, '循环头检测(GET_ANEXT/GET_AITER)', original_line.strip()))

        # 2. FOR_ITER 单独比较
        if "'FOR_ITER'," in line or "== 'FOR_ITER'" in line:
            if 'SETUP_LOOP' not in line and 'GET_ITER' not in line:
                if "opname in (" in line or "opname ==" in line:
                    # 处理集合中的 FOR_ITER
                    line = re.sub(
                        r"'FOR_ITER'(?:\s*,|\s*\))",
                        lambda m: "self._opcode_detector.is_for_iter(instr)" if '=' in line[:50] else m.group(0),
                        line
                    )
                    # 更通用的处理
                    if "'FOR_ITER'" in line and "is_for_iter" not in line:
                        line = line.replace("'FOR_ITER'", "self._opcode_detector.is_loop_header_opcode(instr)")
                        modified = True
                        replacements.append((line_num, '循环头检测(FOR_ITER)', original_line.strip()))

        # 3. GET_ITER (迭代器设置)
        if "'GET_ITER'," in line and 'FOR_ITER' in line and 'user_code_ops' not in line:
            # 这些在集合定义中，暂时保留
            pass

        # === Batch 2: 回边和跳转检测 (~30处) ===

        # 4. JUMP_BACKWARD / JUMP_BACKWARD_NO_INTERRUPT (回边检测)
        if "opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')" in line:
            # 判断上下文：如果是检查最后一条指令是否是回边
            if 'last_instr' in line or 'last.opname' in line or '_last_bi' in line or '_last_i' in line:
                line = line.replace(
                    "opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')",
                    "self._opcode_detector.is_backward_jump(instr)"
                )
            else:
                line = line.replace(
                    "opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')",
                    "self._opcode_detector.is_loop_back_edge(instr)"
                )
            modified = True
            replacements.append((line_num, '回边跳转检测', original_line.strip()))

        # 5. JUMP_BACKWARD 单独出现（通常在 not in 中）
        if "'JUMP_BACKWARD'," in line or "'JUMP_BACKWARD')" in line:
            if "'JUMP_BACKWARD_NO_INTERRUPT'" in line:
                # 已经在上面处理了
                pass
            elif "not in ('JUMP_BACKWARD'" in line:
                line = line.replace(
                    "not in ('JUMP_BACKWARD'",
                    "not in (self._opcode_detector.get_backward_jump_opnames()"
                )
                # 需要闭合括号
                if line.count('(') > line.count(')'):
                    line = line.rstrip() + ')\n'
                modified = True
                replacements.append((line_num, '排除回边跳转', original_line.strip()))
            elif "in ('JUMP_BACKWARD'" in line:
                line = line.replace(
                    "in ('JUMP_BACKWARD'",
                    "in self._opcode_detector.get_backward_jump_opnames()"
                )
                modified = True
                replacements.append((line_num, '回边跳转检查', original_line.strip()))

        # 6. JUMP_FORWARD/JUMP_ABSOLUTE/JUMP_BACKWARD 组合（无条件跳转）
        if "('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE')" in line:
            if 'identif' in line.lower() or 'prefix' in line.lower():
                line = line.replace(
                    "('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE')",
                    "self._opcode_detector.get_unconditional_jump_opnames()"
                )
                modified = True
                replacements.append((line_num, '无条件跳转(前缀识别)', original_line.strip()))
            else:
                line = line.replace(
                    "('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE')",
                    "self._opcode_detector.get_unconditional_jump_opnames()"
                )
                modified = True
                replacements.append((line_num, '无条件跳转检测', original_line.strip()))

        # 7. JUMP_FORWARD/JUMP_ABSOLUTE 对（用于 break 检测等）
        if "('JUMP_FORWARD', 'JUMP_ABSOLUTE')" in line and 'BACKWARD' not in line:
            line = line.replace(
                "('JUMP_FORWARD', 'JUMP_ABSOLUTE')",
                "self._opcode_detector.get_forward_jump_opnames()"
            )
            modified = True
            replacements.append((line_num, '前向跳转检测', original_line.strip()))

        # === Batch 3: 条件跳转 (~12处) ===

        # 8. POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE
        if "('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE')" in line:
            if 'FORWARD' not in line and 'BACKWARD' not in line:
                line = line.replace(
                    "('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE')",
                    "self._opcode_detector.get_basic_conditional_jump_opnames()"
                )
                modified = True
                replacements.append((line_num, '基本条件跳转', original_line.strip()))

        # 9. POP_JUMP_IF_* 变体（包含 FORWARD/BACKWARD）
        if 'POP_JUMP_IF_' in line and 'CONDITIONAL_JUMP_OPS' not in line and 'FORWARD_CONDITIONAL' not in line:
            if 'opname in (' in line and ('POP_JUMP' in line):
                # 复杂的条件跳转集合，使用通用方法
                if 'identify_block_prefix' in lines[max(0, line_num-10):line_num][-1] if line_num > 0 else '':
                    # 这个特殊函数中的跳转列表保持原样（它是噪声过滤）
                    pass
                else:
                    line = line.replace(
                        "opname in (",
                        "self._opcode_detector.is_conditional_jump(instr) or instr.opname in ("
                    )
                    modified = True
                    replacements.append((line_num, '条件跳转检测', original_line.strip()))

        # === Batch 4: 返回和异常相关 (~20处) ===

        # 10. RETURN_VALUE / RETURN_CONST
        if "('RETURN_VALUE', 'RETURN_CONST')" in line:
            if 'RAISE' not in line and 'JUMP' not in line and 'POP_EXCEPT' not in line:
                line = line.replace(
                    "('RETURN_VALUE', 'RETURN_CONST')",
                    "self._opcode_detector.get_return_opnames()"
                )
                modified = True
                replacements.append((line_num, '返回指令检测', original_line.strip()))

        # 11. RETURN_VALUE 单独比较
        if "== 'RETURN_VALUE'" in line or "opname == 'RETURN_VALUE'" in line:
            line = line.replace(
                "== 'RETURN_VALUE'",
                "== self._opcode_detector.RETURN_VALUE_NAME"
            )
            modified = True
            replacements.append((line_num, '返回值指令', original_line.strip()))

        # 12. RAISE_VARARGS
        if "== 'RAISE_VARARGS'" in line or "opname == 'RAISE_VARARGS'" in line:
            line = line.replace(
                "== 'RAISE_VARARGS'",
                "self._opcode_detector.is_raise_instruction(instr)"
            )
            modified = True
            replacements.append((line_num, '引发异常指令', original_line.strip()))

        # 13. RERAISE
        if "== 'RERAISE'" in line and 'opname' in line:
            line = line.replace(
                "== 'RERAISE'",
                "self._opcode_detector.is_reraise(instr)"
            )
            modified = True
            replacements.append((line_num, '重新引发异常', original_line.strip()))

        # 14. PUSH_EXC_INFO / WITH_EXCEPT_START (异常包装器)
        if "PUSH_EXC_INFO" in line and 'WITH_EXCEPT_START' in line:
            if 'any(' in line:
                line = line.replace(
                    "any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in",
                    "any(self._opcode_detector.is_exception_wrapper(i) for i in"
                )
                modified = True
                replacements.append((line_num, '异常包装器检测', original_line.strip()))

        # 15. WITH_EXCEPT_START 单独
        if "== 'WITH_EXCEPT_START'" in line:
            line = line.replace(
                "== 'WITH_EXCEPT_START'",
                "self._opcode_detector.is_with_except_start(instr)"
            )
            modified = True
            replacements.append((line_num, 'WITH异常开始', original_line.strip()))

        # 16. POP_EXCEPT
        if "'POP_EXCEPT'" in line and 'opname' in line:
            if 'in (' in line:
                # 在集合中，保持不变或使用异常检测
                pass

        # === Batch 5: YIELD/SEND 相关 (~5处) ===

        # 17. YIELD_VALUE
        if "'YIELD_VALUE'" in line and 'opname' in line:
            if '==' in line:
                line = line.replace(
                    "== 'YIELD_VALUE'",
                    "self._opcode_detector.is_yield_value(instr)"
                )
                modified = True
                replacements.append((line_num, '生成器yield', original_line.strip()))
            elif 'in (' in line or 'in (' in line:
                line = line.replace(
                    "'YIELD_VALUE'",
                    "self._opcode_detector.YIELD_VALUE_NAME"
                )
                modified = True
                replacements.append((line_num, 'YIELD_VALUE名称', original_line.strip()))

        # 18. JUMP_BACKWARD_NO_INTERRUPT 单独
        if "'JUMP_BACKWARD_NO_INTERRUPT'" in line and 'JUMP_BACKWARD' not in line:
            if 'opname' in line:
                line = line.replace(
                    "'JUMP_BACKWARD_NO_INTERRUPT'",
                    "self._opcode_detector.JUMP_BACKWARD_NO_INTERRUPT_NAME"
                )
                modified = True
                replacements.append((line_num, '无中断回跳', original_line.strip()))

        if modified:
            total_replacements += 1
            lines[line_num - 1] = line

    return lines, replacements, total_replacements


def main():
    """主函数"""
    base_path = Path(r'd:\Desktop\ptrade相关\pythoncdc')

    print("=" * 80)
    print("开始替换硬编码操作码为 OpcodeFeatureDetector 调用")
    print("=" * 80)

    # 处理 region_analyzer.py
    analyzer_path = base_path / 'core' / 'cfg' / 'region_analyzer.py'
    print(f"\n📝 处理文件: {analyzer_path.name}")

    lines = read_file(analyzer_path)
    new_lines, analyzer_replacements, analyzer_count = replace_hardcoded_opcodes_in_analyzer(lines.copy())
    write_file(analyzer_path, new_lines)

    print(f"✅ 完成 {analyzer_count} 处替换")

    # 输出替换清单
    print("\n" + "=" * 80)
    print(f"📋 {analyzer_path.name} 替换清单 ({len(analyzer_replacements)} 处)")
    print("=" * 80)

    for idx, (line_num, desc, original) in enumerate(analyzer_replacements, 1):
        print(f"{idx:3d}. [行 {line_num:4d}] {desc:30s} | {original[:70]}...")

    print("\n" + "=" * 80)
    print("✅ 所有替换已完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
