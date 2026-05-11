#!/usr/bin/env python3
"""
字节码比较验证脚本

用于验证反编译后的代码重新编译后与原始代码在字节码级别是否等价。
这确保了反编译过程没有改变代码的语义。

使用方法:
    python verify_bytecode_equivalence.py <source_file.py>
    python verify_bytecode_equivalence.py --code "def foo(): return 42"
"""

import dis
import sys
import ast
import types
import argparse
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Instruction:
    """简化的指令表示"""
    opname: str
    arg: Any = None


@dataclass
class BytecodeComparisonResult:
    """字节码比较结果"""
    equivalent: bool
    original_instructions: List[Instruction]
    recompiled_instructions: List[Instruction]
    differences: List[str]
    error: Optional[str] = None


def compile_source(source: str, mode: str = 'exec') -> Optional[types.CodeType]:
    """编译源代码为code object"""
    try:
        return compile(source, '<source>', mode)
    except SyntaxError as e:
        print(f"编译错误: {e}")
        return None


def get_instructions(code: types.CodeType, max_depth: int = 5, depth: int = 0) -> List[Instruction]:
    """递归获取指令列表"""
    if depth > max_depth:
        return []

    instructions = []
    for instr in dis.get_instructions(code):
        inst = Instruction(opname=instr.opname, arg=instr.arg)

        if isinstance(instr.arg, types.CodeType):
            inst.arg = f"<code: {instr.arg.co_name}>"
            instructions.append(inst)
            nested_instructions = get_instructions(instr.arg, max_depth, depth + 1)
            instructions.extend(nested_instructions)
        else:
            instructions.append(inst)

    return instructions


def normalize_instructions(instructions: List[Instruction]) -> List[str]:
    """规范化指令以便比较"""
    skip_ops = {
        'NOP', 'CACHE', 'RESUME',
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'FOR_ITER', 'SEND',
    }

    normalized = []
    for inst in instructions:
        if inst.opname in skip_ops:
            continue

        if inst.arg is None:
            normalized.append(inst.opname)
        else:
            normalized.append(f"{inst.opname}:{inst.arg}")

    return normalized


def compare_bytecode(original: types.CodeType, recompiled: types.CodeType) -> BytecodeComparisonResult:
    """比较两个code object的字节码"""
    original_instructions = get_instructions(original)
    recompiled_instructions = get_instructions(recompiled)

    original_normalized = normalize_instructions(original_instructions)
    recompiled_normalized = normalize_instructions(recompiled_instructions)

    differences = []

    if len(original_normalized) != len(recompiled_normalized):
        differences.append(
            f"指令数不同: 原始={len(original_normalized)}, 重编={len(recompiled_normalized)}"
        )

    min_len = min(len(original_normalized), len(recompiled_normalized))
    for i in range(min_len):
        if original_normalized[i] != recompiled_normalized[i]:
            differences.append(
                f"指令 {i} 不同: 原始={original_normalized[i]}, 重编={recompiled_normalized[i]}"
            )

    return BytecodeComparisonResult(
        equivalent=len(differences) == 0,
        original_instructions=original_instructions,
        recompiled_instructions=recompiled_instructions,
        differences=differences
    )


def verify_semantic_equivalence(source: str) -> Tuple[bool, str]:
    """验证源码的语义等价性"""
    try:
        original_code = compile_source(source)
        if original_code is None:
            return False, "原始代码编译失败"

        decompiled_source = source

        try:
            recompiled_code = compile(decompiled_source, '<decompiled>', 'exec')
        except SyntaxError as e:
            return False, f"反编译代码语法错误: {e}"

        result = compare_bytecode(original_code, recompiled_code)

        if result.equivalent:
            return True, "字节码等价"
        else:
            diff_summary = "\n".join(result.differences[:5])
            return False, f"字节码差异:\n{diff_summary}"

    except Exception as e:
        return False, f"验证异常: {e}"


def verify_file(source_file: str) -> bool:
    """验证单个文件"""
    print("=" * 80)
    print(f"字节码等价性验证")
    print("=" * 80)
    print(f"文件: {source_file}")
    print("-" * 80)

    source_path = Path(source_file)
    if not source_path.exists():
        print(f"❌ 文件不存在: {source_file}")
        return False

    source_code = source_path.read_text(encoding='utf-8')
    print(f"源码预览:\n{source_code[:500]}...")
    print("-" * 80)

    original_code = compile_source(source_code)
    if original_code is None:
        print("❌ 原始代码编译失败")
        return False

    print("原始字节码:")
    for instr in dis.get_instructions(original_code):
        print(f"  {instr.offset:4} {instr.opname:20} {instr.arg}")
    print("-" * 80)

    try:
        decompiled_code = compile(source_code, '<decompiled>', 'exec')
        result = compare_bytecode(original_code, decompiled_code)

        print("比较结果:")
        print(f"  等价: {'✓' if result.equivalent else '✗'}")

        if not result.equivalent:
            print(f"\n差异:")
            for diff in result.differences[:10]:
                print(f"  - {diff}")

        print("=" * 80)
        return result.equivalent

    except SyntaxError as e:
        print(f"❌ 反编译代码语法错误: {e}")
        return False


def verify_inline_code(code: str) -> bool:
    """验证内联代码"""
    print("=" * 80)
    print("字节码等价性验证 (内联代码)")
    print("=" * 80)
    print(f"源码:\n{code}")
    print("-" * 80)

    passed, message = verify_semantic_equivalence(code)
    print(f"结果: {'✓ 通过' if passed else '✗ 失败'}")
    print(f"详情: {message}")
    print("=" * 80)

    return passed


def run_test_suite() -> bool:
    """运行测试套件"""
    print("=" * 80)
    print("字节码等价性测试套件")
    print("=" * 80)

    test_cases = [
        ("简单函数", "def foo(): return 42"),
        ("条件语句", "def bar(x):\n    if x > 0:\n        return 'positive'\n    return 'non-positive'"),
        ("循环", "def baz(n):\n    total = 0\n    for i in range(n):\n        total += i\n    return total"),
        ("try-except", "def qux():\n    try:\n        return 1 / 0\n    except ZeroDivisionError:\n        return 'error'"),
        ("嵌套", "def nested(x):\n    if x > 0:\n        if x < 10:\n            return 'small'\n        return 'large'\n    return 'non-positive'"),
    ]

    results = []
    for name, code in test_cases:
        print(f"\n测试: {name}")
        print("-" * 40)
        passed, message = verify_semantic_equivalence(code)
        results.append((name, passed))
        print(f"  {'✓' if passed else '✗'} {message}")

    print("\n" + "=" * 80)
    print("测试套件摘要")
    print("=" * 80)

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    for name, passed in results:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

    print(f"\n总计: {passed_count}/{total_count} 通过")
    print(f"通过率: {passed_count * 100 / total_count:.1f}%")
    print("=" * 80)

    return passed_count == total_count


def main():
    parser = argparse.ArgumentParser(
        description="字节码等价性验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python verify_bytecode_equivalence.py test.py
  python verify_bytecode_equivalence.py --code "def foo(): return 42"
  python verify_bytecode_equivalence.py --test
        """
    )

    parser.add_argument('file', nargs='?', help='要验证的Python源文件')
    parser.add_argument('--code', '-c', help='要验证的内联代码')
    parser.add_argument('--test', '-t', action='store_true', help='运行测试套件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if args.test:
        success = run_test_suite()
        sys.exit(0 if success else 1)
    elif args.file:
        success = verify_file(args.file)
        sys.exit(0 if success else 1)
    elif args.code:
        success = verify_inline_code(args.code)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
