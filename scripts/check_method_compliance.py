#!/usr/bin/env python3
"""CFG Method Compliance Checker

A comprehensive Python method compliance checking tool for inspecting methods
in the core/cfg/ directory. Checks method length, cyclomatic complexity,
hardcoded opcodes, and coordinator method compliance.
"""

import ast
import os
import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
import argparse


@dataclass
class MethodInfo:
    """方法信息数据类"""
    file_path: str
    class_name: Optional[str]
    method_name: str
    start_line: int
    end_line: int
    length: int
    complexity: int = 0
    is_coordinator: bool = False
    violations: List[str] = field(default_factory=list)
    hardcoded_opcodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'file_path': self.file_path,
            'class_name': self.class_name,
            'method_name': self.method_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'length': self.length,
            'complexity': self.complexity,
            'is_coordinator': self.is_coordinator,
            'violations': self.violations,
            'hardcoded_opcodes': self.hardcoded_opcodes
        }


class ComplexityVisitor(ast.NodeVisitor):
    """计算圈复杂度的AST访问器

    基于McCabe圈复杂度算法，通过遍历AST节点计算复杂度。
    每个决策点（if、for、while等）都会增加复杂度值。

    Attributes:
        complexity (int): 当前累计的圈复杂度值
    """

    KNOWN_OPCODES = [
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'FOR_ITER',
        'GET_ANEXT', 'BEFORE_WITH', 'WITH_EXCEPT_START',
        'SETUP_FINALLY', 'SETUP_WITH', 'SETUP_ASYNC_WITH',
        'SETUP_EXCEPT', 'SETUP_LOOP',
        'MATCH_CLASS', 'MATCH_KEYS', 'MATCH_MAPPING',
        'MATCH_SEQUENCE', 'MATCH_VALUE',
        'SEND', 'YIELD_FROM'
    ]

    def __init__(self):
        super().__init__()
        self.complexity = 1

    def visit_If(self, node):
        """访问If节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        """访问For循环节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        """访问异步For循环节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        """访问While循环节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        """访问异常处理节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        """访问With上下文管理器节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        """访问异步With节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Assert(self, node):
        """访问断言节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        """访问布尔操作节点（and/or），每个短路逻辑增加复杂度

        Args:
            node: BoolOp AST节点
        """
        num_operands = len(node.values)
        if num_operands > 1:
            self.complexity += (num_operands - 1)
        self.generic_visit(node)

    def visit_Lambda(self, node):
        """访问Lambda表达式节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        """访问列表推导式节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        """访问集合推导式节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_DictComp(self, node):
        """访问字典推导式节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        """访问生成器表达式节点，增加复杂度"""
        self.complexity += 1
        self.generic_visit(node)

    def visit_Expr(self, node):
        """访问表达式节点，检查是否包含硬编码操作码"""
        self._check_for_hardcoded_opcode(node)
        self.generic_visit(node)

    def _check_for_hardcoded_opcode(self, node):
        """检查节点中是否包含硬编码的Python操作码名称

        通过分析字符串常量来检测可能的硬编码操作码引用。

        Args:
            node: 要检查的AST节点
        """
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            opcode_str = node.value.value.upper()
            for opcode in self.KNOWN_OPCODES:
                if opcode in opcode_str:
                    return True
        return False


class ComplianceChecker:
    """合规性检查器主类

    负责扫描目录中的Python文件，提取方法信息，
    并执行各种合规性检查。

    Attributes:
        directory (Path): 要检查的目录路径
        max_length (int): 方法最大允许行数
        max_complexity (int): 最大允许圈复杂度
        coordinator_max_length (int): 协调器方法最大允许行数
        methods (List[MethodInfo]): 提取的所有方法信息列表
        errors (List[str]): 处理过程中遇到的错误信息
    """

    COORDINATOR_PATTERNS = [
        r'_identify_\w+_regions',
        r'_generate_\w+'
    ]

    def __init__(self, directory: str, max_length: int = 100,
                 max_complexity: int = 10, verbose: bool = False):
        """初始化合规性检查器

        Args:
            directory: 要检查的目录路径
            max_length: 方法最大允许行数（默认100）
            max_complexity: 最大允许圈复杂度（默认10）
            verbose: 是否显示详细信息
        """
        self.directory = Path(directory)
        self.max_length = max_length
        self.max_complexity = max_complexity
        self.coordinator_max_length = 80
        self.verbose = verbose
        self.methods: List[MethodInfo] = []
        self.errors: List[str] = []

    def check_directory(self) -> Dict:
        """主入口：检查目录下所有Python文件

        遍历指定目录中的所有.py文件，解析AST并提取方法信息，
        然后执行各种合规性检查。

        Returns:
            包含完整检查结果的字典，包括统计信息和违规详情
        """
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {self.directory}")

        if not self.directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.directory}")

        python_files = list(self.directory.rglob('*.py'))

        if self.verbose:
            print(f"Found {len(python_files)} Python files in {self.directory}")

        for py_file in python_files:
            try:
                self._process_file(py_file)
            except SyntaxError as e:
                error_msg = f"Syntax error in {py_file}: {e}"
                self.errors.append(error_msg)
                if self.verbose:
                    print(f"Warning: {error_msg}")
            except Exception as e:
                error_msg = f"Error processing {py_file}: {e}"
                self.errors.append(error_msg)
                if self.verbose:
                    print(f"Warning: {error_msg}")

        return self.generate_report()

    def _process_file(self, file_path: Path):
        """处理单个Python文件

        解析文件的AST，提取所有函数和方法定义，
        并计算它们的长度和复杂度。

        Args:
            file_path: Python文件路径
        """
        source_code = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source_code, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_name = self._get_class_name(tree, node)
                method_info = self._extract_method_info(
                    file_path, class_name, node, source_code
                )
                if method_info:
                    self.methods.append(method_info)

    def _get_class_name(self, tree: ast.AST, func_node) -> Optional[str]:
        """获取函数所在的类名

        遍历AST树查找包含该函数定义的类。

        Args:
            tree: 完整的AST树
            func_node: 函数/方法定义节点

        Returns:
            类名字符串，如果不在类中则返回None
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is func_node:
                        return node.name
        return None

    def _extract_method_info(self, file_path: Path, class_name: Optional[str],
                             func_node, source_code: str) -> Optional[MethodInfo]:
        """从AST节点提取方法信息

        计算方法的起始行、结束行、长度、圈复杂度，
        并检测硬编码的操作码。

        Args:
            file_path: 文件路径
            class_name: 所属类名
            func_node: 函数定义AST节点
            source_code: 文件源代码

        Returns:
            MethodInfo对象，包含完整的方法信息
        """
        start_line = func_node.lineno
        end_line = getattr(func_node, 'end_lineno', start_line)
        length = end_line - start_line + 1

        visitor = ComplexityVisitor()
        visitor.visit(func_node)
        complexity = visitor.complexity

        hardcoded_opcodes = self.check_hardcoded_opcodes(func_node)
        is_coordinator = self.is_coordinator_method(func_node.name)

        method_info = MethodInfo(
            file_path=str(file_path),
            class_name=class_name,
            method_name=func_node.name,
            start_line=start_line,
            end_line=end_line,
            length=length,
            complexity=complexity,
            is_coordinator=is_coordinator,
            hardcoded_opcodes=hardcoded_opcodes
        )

        self._check_compliance(method_info)
        return method_info

    def calculate_complexity(self, node) -> int:
        """计算给定AST节点的圈复杂度

        使用ComplexityVisitor遍历节点并返回复杂度值。

        Args:
            node: 要计算复杂度的AST节点

        Returns:
            圈复杂度整数值
        """
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity

    def check_hardcoded_opcodes(self, node) -> List[str]:
        """检测硬编码的Python操作码

        扫描AST节点中的字符串常量，查找已知的Python字节码操作码名称。
        排除文档字符串和注释中的合法引用。

        Args:
            node: 要检查的AST节点

        Returns:
            发现的硬编码操作码名称列表
        """
        found_opcodes = []
        source_lines = []

        try:
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                with open(node.__dict__.get('_file_path', ''), 'r') as f:
                    all_lines = f.readlines()
                    source_lines = all_lines[node.lineno - 1:node.end_lineno]
        except Exception:
            pass

        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                if self._is_docstring(child, node):
                    continue

                value_upper = child.value.upper()
                for opcode in ComplexityVisitor.KNOWN_OPCODES:
                    if opcode in value_upper and opcode not in found_opcodes:
                        context = self._get_string_context(child, source_lines)
                        if not self._is_legitimate_reference(opcode, context):
                            found_opcodes.append(opcode)

        return found_opcodes

    def _is_docstring(self, const_node, parent_node) -> bool:
        """检查字符串常量是否是文档字符串

        Args:
            const_node: 常量节点
            parent_node: 父级函数/方法节点

        Returns:
            如果是docstring则返回True
        """
        if not isinstance(parent_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False

        if not parent_node.body:
            return False

        first_stmt = parent_node.body[0]
        return (isinstance(first_stmt, ast.Expr) and
                isinstance(first_stmt.value, ast.Constant) and
                first_stmt.value is const_node)

    def _get_string_context(self, const_node, source_lines: List[str]) -> str:
        """获取字符串常量的上下文环境

        用于判断字符串的使用场景，帮助排除合法引用。

        Args:
            const_node: 常量节点
            source_lines: 源代码行列表

        Returns:
            包含字符串的上下文文本
        """
        line_num = getattr(const_node, 'lineno', 0)
        if 0 < line_num <= len(source_lines):
            return source_lines[line_num - 1]
        return ''

    def _is_legitimate_reference(self, opcode: str, context: str) -> bool:
        """判断操作码引用是否是合法的

        排除文档、注释、日志等场景中的合法引用。

        Args:
            opcode: 操作码名称
            context: 字符串出现的上下文

        Returns:
            如果是合法引用则返回True
        """
        legitimate_patterns = [
            r'#.*' + re.escape(opcode),
            r'docstring|documentation|document',
            r'logging|log\.|logger\.',
            r'print\(.*' + re.escape(opcode),
            r'"""[\s\S]*?"""',
            r"'''[\s\S]*?'''"
        ]

        for pattern in legitimate_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return True

        return False

    def is_coordinator_method(self, name: str) -> bool:
        """判断方法是否是协调器方法

        基于命名规范识别协调器方法：
        - _identify_xxx_regions() 格式的方法
        - _generate_xxx() 格式的方法

        Args:
            name: 方法名称

        Returns:
            如果符合协调器命名规范则返回True
        """
        for pattern in self.COORDINATOR_PATTERNS:
            if re.match(pattern, name):
                return True
        return False

    def _check_compliance(self, method: MethodInfo):
        """检查单个方法的合规性

        根据配置的阈值检查方法长度、复杂度、硬编码操作码等，
        并将违规信息记录到方法对象的violations列表中。

        Args:
            method: 要检查的方法信息对象
        """
        if method.length > self.max_length:
            method.violations.append(
                f"Exceeds max length ({method.length} > {self.max_length})"
            )

        if method.complexity > self.max_complexity:
            method.violations.append(
                f"High complexity ({method.complexity} > {self.max_complexity})"
            )

        if method.hardcoded_opcodes:
            method.violations.append(
                f"Contains hardcoded opcodes: {', '.join(method.hardcoded_opcodes)}"
            )

        if method.is_coordinator:
            if method.length > self.coordinator_max_length:
                method.violations.append(
                    f"Coordinator exceeds thin limit "
                    f"({method.length} > {self.coordinator_max_length})"
                )

    def generate_report(self) -> Dict:
        """生成完整的合规性检查报告

        统计所有方法的检查结果，生成包含统计信息和详细违规列表的报告。

        Returns:
            完整的报告字典
        """
        total_methods = len(self.methods)
        violating_methods = [m for m in self.methods if m.violations]

        avg_length = (
            sum(m.length for m in self.methods) / total_methods
            if total_methods > 0 else 0
        )
        avg_complexity = (
            sum(m.complexity for m in self.methods) / total_methods
            if total_methods > 0 else 0
        )

        violations_by_type = {}
        for method in self.methods:
            for violation in method.violations:
                violation_type = violation.split(':')[0] if ':' in violation else violation
                if violation_type not in violations_by_type:
                    violations_by_type[violation_type] = []
                violations_by_type[violation_type].append(method)

        report = {
            'summary': {
                'total_methods': total_methods,
                'total_violations': len(violating_methods),
                'avg_length': round(avg_length, 2),
                'avg_complexity': round(avg_complexity, 2),
                'max_length_found': max((m.length for m in self.methods), default=0),
                'max_complexity_found': max((m.complexity for m in self.methods), default=0),
                'coordinator_count': sum(1 for m in self.methods if m.is_coordinator),
                'errors_count': len(self.errors)
            },
            'violating_methods': [m.to_dict() for m in violating_methods],
            'violations_by_type': {
                k: [m.to_dict() for m in v]
                for k, v in violations_by_type.items()
            },
            'all_methods': [m.to_dict() for m in self.methods],
            'errors': self.errors,
            'config': {
                'directory': str(self.directory),
                'max_length': self.max_length,
                'max_complexity': self.max_complexity,
                'coordinator_max_length': self.coordinator_max_length
            }
        }

        return report


def format_text_report(report: Dict, verbose: bool = False) -> str:
    """格式化文本报告

    将报告字典转换为人类可读的文本格式输出。

    Args:
        report: 完整的报告字典
        verbose: 是否显示详细信息

    Returns:
        格式化后的文本报告字符串
    """
    lines = []
    lines.append("=" * 80)
    lines.append("CFG METHOD COMPLIANCE REPORT")
    lines.append("=" * 80)
    lines.append("")

    summary = report['summary']
    config = report['config']

    lines.append("CONFIGURATION:")
    lines.append(f"  Directory:     {config['directory']}")
    lines.append(f"  Max Length:    {config['max_length']} lines")
    lines.append(f"  Max Complexity:{config['max_complexity']}")
    lines.append(f"  Coordinator Max Length: {config['coordinator_max_length']} lines")
    lines.append("")

    lines.append("-" * 80)
    lines.append("SUMMARY:")
    lines.append("-" * 80)
    lines.append(f"  Total Methods:       {summary['total_methods']}")
    lines.append(f"  Violating Methods:   {summary['total_violations']}")
    lines.append(f"  Average Length:      {summary['avg_length']:.2f} lines")
    lines.append(f"  Average Complexity:  {summary['avg_complexity']:.2f}")
    lines.append(f"  Max Length Found:    {summary['max_length_found']} lines")
    lines.append(f"  Max Complexity Found:{summary['max_complexity_found']}")
    lines.append(f"  Coordinator Methods: {summary['coordinator_count']}")
    lines.append(f"  Errors Encountered:  {summary['errors_count']}")
    lines.append("")

    if report['violating_methods']:
        lines.append("-" * 80)
        lines.append("VIOLATING METHODS:")
        lines.append("-" * 80)

        for i, method in enumerate(report['violating_methods'], 1):
            class_prefix = f"{method['class_name']}." if method['class_name'] else ""
            full_name = f"{class_prefix}{method['method_name']}"

            lines.append(f"\n{i}. {full_name}")
            lines.append(f"   File:     {method['file_path']}")
            lines.append(f"   Lines:    {method['start_line']}-{method['end_line']} "
                         f"({method['length']} lines)")
            lines.append(f"   Complexity: {method['complexity']}")
            if method['is_coordinator']:
                lines.append(f"   ★ Coordinator Method")
            if method['hardcoded_opcodes']:
                lines.append(f"   ⚠ Hardcoded Opcodes: {', '.join(method['hardcoded_opcodes'])}")
            lines.append("   Violations:")

            for violation in method['violations']:
                lines.append(f"     • {violation}")

            if verbose:
                lines.append(f"\n   Full Details:")
                lines.append(f"     - Start Line: {method['start_line']}")
                lines.append(f"     - End Line: {method['end_line']}")
                lines.append(f"     - Length: {method['length']} lines")
                lines.append(f"     - Cyclomatic Complexity: {method['complexity']}")

        lines.append("")
    else:
        lines.append("\n✓ No violations found! All methods comply with the standards.")
        lines.append("")

    if report['errors']:
        lines.append("-" * 80)
        lines.append("ERRORS ENCOUNTERED:")
        lines.append("-" * 80)
        for error in report['errors']:
            lines.append(f"  • {error}")
        lines.append("")

    if verbose and report['all_methods']:
        lines.append("=" * 80)
        lines.append("ALL METHODS (VERBOSE)")
        lines.append("=" * 80)
        for i, method in enumerate(report['all_methods'], 1):
            class_prefix = f"{method['class_name']}." if method['class_name'] else ""
            status = "✓" if not method['violations'] else "✗"
            coord_tag = " [COORD]" if method['is_coordinator'] else ""
            lines.append(
                f"{i:3d}. {status} {class_prefix}{method['method_name']}{coord_tag}"
                f" - L{method['length']:4d}/C{method['complexity']:2d}"
            )
        lines.append("")

    lines.append("=" * 80)
    if summary['total_violations'] == 0:
        lines.append("RESULT: ✓ PASS - All methods are compliant")
    else:
        lines.append(f"RESULT: ✗ FAIL - {summary['total_violations']} method(s) have violations")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    """主函数：命令行接口入口

    解析命令行参数，执行合规性检查，并输出结果。
    根据是否存在违规项设置适当的退出码。

    Exit Codes:
        0: 无违规或仅有警告
        1: 存在违规项
        2: 参数错误或运行时错误
    """
    parser = argparse.ArgumentParser(
        description='CFG Method Compliance Checker - Check Python methods for compliance '
                    'with coding standards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --directory ./core/cfg/
  %(prog)s --directory ./core/cfg/ --max-length 80 --max-complexity 8
  %(prog)s --directory ./core/cfg/ --format json --output report.json
  %(prog)s --directory ./core/cfg/ --verbose
        """
    )

    parser.add_argument(
        '--directory', '-d',
        required=True,
        type=str,
        help='Directory to check (required)'
    )
    parser.add_argument(
        '--max-length', '-l',
        type=int,
        default=100,
        help='Maximum allowed method length in lines (default: 100)'
    )
    parser.add_argument(
        '--max-complexity', '-c',
        type=int,
        default=10,
        help='Maximum allowed cyclomatic complexity (default: 10)'
    )
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='Output format: text or json (default: text)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file path (optional, default: stdout)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )

    args = parser.parse_args()

    try:
        checker = ComplianceChecker(
            directory=args.directory,
            max_length=args.max_length,
            max_complexity=args.max_complexity,
            verbose=args.verbose
        )

        if args.verbose:
            print(f"\nStarting compliance check on: {args.directory}")
            print(f"Max length: {args.max_length}, Max complexity: {args.max_complexity}\n")

        report = checker.check_directory()

        if args.format == 'json':
            output = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            output = format_text_report(report, verbose=args.verbose)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding='utf-8')
            if args.verbose:
                print(f"Report written to: {args.output}")
        else:
            print(output)

        exit_code = 1 if report['summary']['total_violations'] > 0 else 0
        sys.exit(exit_code)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except PermissionError as e:
        print(f"Permission denied: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
