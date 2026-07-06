#!/usr/bin/env python3
"""
CI检测脚本 - 扫描指定文件中的硬编码操作码引用

用途：
- 在CI流水线中运行，防止硬编码操作码回归
- 检测逻辑判断中直接使用的操作码名称字符串
- 区分合法使用（注释、日志、AST类型）和违规使用（条件判断）

用法：
    python scripts/check_hardcoded_opcodes.py [--files FILE1 FILE2 ...] [--strict]

退出码：
    0 - 无硬编码操作码
    1 - 发现硬编码操作码
"""

import re
import sys
import argparse
from pathlib import Path

# ============================================================
# Python 3.8-3.11 完整操作码集合（来自 dis 模块）
# 理论依据：Python 官方 dis 模块定义的标准操作码集
# ============================================================

ALL_PYTHON_OPCODES = frozenset({
    'POP_TOP', 'ROT_TWO', 'ROT_THREE', 'DUP_TOP', 'DUP_TOP_TWO',
    'ROT_N', 'ROT_FOUR',
    'NOP', 'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT',
    'UNARY_INVERT', 'BINARY_SUBSCR', 'STORE_SUBSCR', 'DELETE_SUBSCR',
    'BINARY_LSHIFT', 'BINARY_RSHIFT', 'BINARY_AND', 'BINARY_XOR',
    'BINARY_OR', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY',
    'INPLACE_MATRIX_MULTIPLY', 'INPLACE_POWER', 'INPLACE_DIVIDE',
    'INPLACE_FLOOR_DIVIDE', 'INPLACE_TRUE_DIVIDE', 'INPLACE_MODULO',
    'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR',
    'INPLACE_OR', 'STORE_NAME', 'DELETE_NAME', 'UNPACK_SEQUENCE',
    'UNPACK_EX', 'FOR_ITER', 'GET_ITER', 'GET_AITER', 'GET_ANEXT',
    'BEFORE_ASYNC_WITH', 'END_ASYNC_FOR',
    'STORE_ATTR', 'DELETE_ATTR', 'STORE_GLOBAL', 'DELETE_GLOBAL',
    'LOAD_CONST', 'LOAD_NAME', 'BUILD_TUPLE', 'BUILD_LIST',
    'BUILD_SET', 'BUILD_MAP', 'BUILD_CONST_KEY_MAP', 'BUILD_STRING',
    'LOAD_ATTR', 'COMPARE_OP', 'IMPORT_NAME', 'IMPORT_FROM',
    'IMPORT_STAR', 'JUMP_FORWARD', 'JUMP_IF_FALSE_OR_POP',
    'JUMP_IF_TRUE_OR_POP', 'JUMP_ABSOLUTE', 'POP_JUMP_IF_FALSE',
    'POP_JUMP_IF_TRUE', 'LOAD_GLOBAL', 'IS_OP', 'CONTAINS_OP',
    'RERAISE', 'WITH_EXCEPT_START', 'GET_YIELD_FROM_ITER',
    'PRINT_EXPR', 'LOAD_BUILD_CLASS', 'SETUP_ANNOTATIONS',
    'RETURN_VALUE', 'IMPORT_FROM_EXTRA', 'YIELD_VALUE', 'YIELD_FROM',
    'CALL', 'CALL_FUNCTION', 'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
    'CALL_FUNCTION_EX_KW', 'SEND', 'MAKE_FUNCTION', 'BUILD_SLICE',
    'COPY', 'BINARY_OP', 'SWAP', 'CACHE', 'PUSH_NULL',
    'LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_MERGE',
    'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE', 'MATCH_KEYS',
    'MATCH_JMP_NOT_NONE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NOT_NONE', 'CHECK_EXC_MATCH',
    'CHECK_EG_MATCH', 'PUSH_EXC_INFO', 'POP_EXCEPT', 'RETURN_CONST',
    'RAISE_VARARGS', 'RETURN_GENERATOR', 'RESUME',
    'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
    'PRECALL', 'FORMAT_VALUE', 'LOAD_METHOD',
    'LOAD_FAST', 'STORE_FAST', 'DELETE_FAST',
    'LOAD_DEREF', 'STORE_DEREF', 'DELETE_DEREF',
    'LOAD_ASSERTION_ERROR',
    'LOAD_CLOSURE', 'GEN_START', 'BINARY_SUBSCR_ADAPTIVE',
    'BINARY_SLICE', 'STORE_SLICE', 'DELETE_SLICE',
    'SETUP_FINALLY', 'SETUP_EXCEPT', 'SETUP_WITH', 'SETUP_ASYNC_WITH',
    'BEFORE_WITH', 'JUMP_NOT_EXC_MATCH', 'JUMP_BACKWARD_NO_INTERRUPT',
    'COPY_FREE_VARS', 'KW_NAMES',
})

# 合法的上下文模式（这些不应被标记为违规）
VALID_CONTEXT_PATTERNS = [
    r'#.*opname\s*==\s*[\'"]\w+[\'"]',
    r'#.*opname\s*in\s*\(',
    r'""".*?"""',
    r"'''.*?'''",
    r'def test_\w+.*:',
    r'class \w+Test',
    r'\bassert\b.*opname',
    r'logging\.\w+\(.*opname',
    r'log\.\w+\(.*opname',
    r'logger\.\w+\(.*opname',
]


class HardcodedOpcodeDetector:
    """硬编码操作码检测器

    理论依据：基于静态分析理论，通过正则表达式匹配源代码中的
    操作码字符串字面量，识别可能违反域隔离原则的硬编码引用。
    """

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.violations = []

        # 匹配 opname == 'OPCODE' 或 opname in ('OPCODE1', 'OPCODE2') 模式
        self.opcode_compare_pattern = re.compile(
            r'''(?x)
            (?:opname|instr\.opname|instruction\.opname|i\.opname)
            \s*
            (?:
                ==\s*['"](\w{3,})['"]
                |
                !=\s*['"](\w{3,})['"]
            )
            '''
        )

        self.opcode_in_pattern = re.compile(
            r'''(?x)
            (?:opname|instr\.opname|instruction\.opname|i\.opname)
            \s+in\s+
            \(
                [^)]*
                ['"](\w{3,})['"]
                [^)]*
            \)
            '''
        )

        # 匹配字符串中的独立操作码引用
        self.standalone_opcode_pattern = re.compile(
            r'''(?x)
            ['"]([A-Z][A-Z0-9_]{2,})['"]
            '''
        )

    def _is_valid_context(self, line: str) -> bool:
        """检查是否在合法上下文中（注释、文档字符串、测试等）"""
        stripped = line.strip()
        if stripped.startswith('#'):
            return True
        for pattern in VALID_CONTEXT_PATTERNS:
            if re.search(pattern, line):
                return True
        return False

    def _is_python_opcode(self, name: str) -> bool:
        """检查是否是Python标准操作码"""
        return name in ALL_PYTHON_OPCODES

    def check_file(self, filepath: Path) -> list:
        """检查单个文件中的硬编码操作码

        Args:
            filepath: 待检查的文件路径

        Returns:
            list: 违规列表，每个元素是 (行号, 行内容, 违规类型)
        """
        violations = []
        content = filepath.read_text(encoding='utf-8')
        lines = content.splitlines()

        for lineno, line in enumerate(lines, start=1):

            # 跳过空行和纯注释行
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # 跳过合法上下文
            if self._is_valid_context(line):
                continue

            # 检查 opname == 'OPCODE' 模式
            for match in self.opcode_compare_pattern.finditer(line):
                opcode_name = match.group(1) or match.group(2)
                if opcode_name and self._is_python_opcode(opcode_name):
                    violations.append({
                        'file': str(filepath),
                        'line': lineno,
                        'content': stripped[:120],
                        'opcode': opcode_name,
                        'pattern': 'equality_check',
                    })

            # 检查 opname in ('OPCODE1', ...) 模式
            for match in self.opcode_in_pattern.finditer(line):
                opcode_name = match.group(1)
                if opcode_name and self._is_python_opcode(opcode_name):
                    violations.append({
                        'file': str(filepath),
                        'line': lineno,
                        'content': stripped[:120],
                        'opcode': opcode_name,
                        'pattern': 'membership_check',
                    })

        return violations

    def check_files(self, filepaths: list[Path]) -> int:
        """检查多个文件

        Returns:
            int: 总违规数
        """
        total_violations = []
        for fp in filepaths:
            if not fp.exists():
                print(f"[WARN] File not found: {fp}", file=sys.stderr)
                continue
            vils = self.check_file(fp)
            total_violations.extend(vils)

        self.violations = total_violations
        return len(total_violations)


def print_report(violations: list, verbose: bool = True):
    """打印检测报告

    Args:
        violations: 违规列表
        verbose: 是否输出详细信息
    """
    if not violations:
        print("[PASS] No hardcoded opcodes found.")
        return

    print(f"\n[FAIL] Found {len(violations)} hardcoded opcode reference(s):")
    print("=" * 80)

    # 按文件分组
    by_file = {}
    for v in violations:
        by_file.setdefault(v['file'], []).append(v)

    for fpath, fv in sorted(by_file.items()):
        print(f"\n  File: {fpath}")
        print(f"  Violations: {len(fv)}")
        if verbose:
            for v in fv:
                marker = "==" if v['pattern'] == 'equality_check' else "in"
                print(f"    L{v['line']:>5}: opname {marker} '{v['opcode']}'")
                print(f"           {v['content']}")

    print("\n" + "=" * 80)
    print("Remediation:")
    print("  Replace with OpcodeFeatureDetector static methods:")
    print("    from core.cfg.opcode_feature_detector import OpcodeFeatureDetector as _D")
    print("    # Instead of: opname == 'FOR_ITER'")
    print("    # Use:         _D.is_loop_iteration_opname(opname)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Detect hardcoded opcode references in source files'
    )
    parser.add_argument(
        '--files', '-f', nargs='+', default=None,
        help='Files to check (default: region_analyzer.py and region_ast_generator.py)'
    )
    parser.add_argument(
        '--strict', '-s', action='store_true',
        help='Strict mode: also flag subset checks like STORE_FAST/NAME/GLOBAL'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Only output summary'
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent

    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = [
            base_dir / 'core' / 'cfg' / 'region_analyzer.py',
            base_dir / 'core' / 'cfg' / 'region_ast_generator.py',
        ]

    detector = HardcodedOpcodeDetector(strict=args.strict)
    count = detector.check_files(targets)

    if count > 0:
        print_report(detector.violations, verbose=not args.quiet)
        sys.exit(1)
    else:
        print("[PASS] No hardcoded opcodes found.")
        sys.exit(0)


if __name__ == '__main__':
    main()
