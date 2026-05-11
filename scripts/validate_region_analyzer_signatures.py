"""
方法签名验证器 - 验证区域分析器的主识别方法

验证每个区域类型有且只有一个主识别方法，防止补丁式编程。
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class MethodSignature:
    name: str
    lineno: int
    end_lineno: int
    region_type: Optional[str]
    is_primary: bool


@dataclass
class ValidationResult:
    region_type: str
    methods: List[MethodSignature]
    status: str
    message: str


class RegionAnalyzerSignatureValidator:
    """验证区域分析器的方法签名规范"""

    PRIMARY_IDENTIFY_METHODS: Dict[str, str] = {
        'TRY_EXCEPT': '_identify_try_except_regions',
        'TRY_FINALLY': '_identify_try_except_regions',
        'FOR_LOOP': '_identify_loop_regions',
        'WHILE_LOOP': '_identify_loop_regions',
        'WITH': '_identify_with_regions',
        'MATCH': '_identify_match_regions',
        'ASSERT': '_identify_assert_regions',
        'BOOL_OP': '_identify_boolop_regions',
        'TERNARY': '_identify_ternary_regions',
        'IF': '_identify_conditional_regions',
        'IF_THEN': '_identify_conditional_regions',
        'IF_THEN_ELSE': '_identify_conditional_regions',
        'IF_ELIF_CHAIN': '_identify_conditional_regions',
        'SEQUENCE': '_identify_sequence_regions',
        'BASIC': '_identify_sequence_regions',
    }

    FORBIDDEN_PATTERNS = [
        (r'_fix_', 'fix_pattern'),
        (r'_patch_', 'patch_pattern'),
        (r'_hack_', 'hack_pattern'),
        (r'_workaround_', 'workaround_pattern'),
        (r'_correct_', 'correct_pattern'),
        (r'_adjust_', 'adjust_pattern'),
        (r'_merge_', 'merge_pattern'),
        (r'_fallback_', 'fallback_pattern'),
    ]

    def __init__(self, source_file: str):
        self.source_file = Path(source_file)
        self.tree: Optional[ast.AST] = None
        self.source_lines: List[str] = []
        self.methods: List[Tuple[str, ast.FunctionDef]] = []
        self.validation_results: List[ValidationResult] = []
        self.violations: List[Dict] = []

    def parse(self) -> bool:
        if not self.source_file.exists():
            print(f"错误: 文件不存在 {self.source_file}")
            return False

        with open(self.source_file, 'r', encoding='utf-8') as f:
            source = f.read()

        self.source_lines = source.splitlines()

        try:
            self.tree = ast.parse(source, filename=str(self.source_file))
        except SyntaxError as e:
            print(f"语法错误: {e}")
            return False

        self.methods = self._extract_methods()
        return True

    def _extract_methods(self) -> List[Tuple[str, ast.FunctionDef]]:
        result = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                if node.name == 'RegionAnalyzer':
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            result.append((item.name, item))
        return result

    def _classify_identify_method(self, method_name: str) -> Optional[str]:
        if not method_name.startswith('_identify_'):
            return None

        method_lower = method_name.lower()

        if 'try' in method_lower or 'except' in method_lower or 'finally' in method_lower:
            return 'TRY_EXCEPT'
        if 'loop' in method_lower or 'for' in method_lower or 'while' in method_lower:
            return 'FOR_LOOP'
        if 'with' in method_lower:
            return 'WITH'
        if 'match' in method_lower or 'case' in method_lower:
            return 'MATCH'
        if 'assert' in method_lower:
            return 'ASSERT'
        if 'bool' in method_lower or 'chained' in method_lower or 'compare' in method_lower:
            return 'BOOL_OP'
        if 'ternary' in method_lower or 'if_exp' in method_lower:
            return 'TERNARY'
        if 'conditional' in method_lower or 'if' in method_lower or 'elif' in method_lower:
            return 'IF'
        if 'sequence' in method_lower or 'basic' in method_lower:
            return 'SEQUENCE'

        return None

    def validate(self) -> bool:
        identify_methods_by_type: Dict[str, List[MethodSignature]] = defaultdict(list)

        for name, node in self.methods:
            region_type = self._classify_identify_method(name)
            if region_type:
                sig = MethodSignature(
                    name=name,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    region_type=region_type,
                    is_primary=(name == self.PRIMARY_IDENTIFY_METHODS.get(region_type))
                )
                identify_methods_by_type[region_type].append(sig)

        for region_type, methods in sorted(identify_methods_by_type.items()):
            primary_method = self.PRIMARY_IDENTIFY_METHODS.get(region_type)
            method_names = [m.name for m in methods]

            if len(methods) == 0:
                result = ValidationResult(
                    region_type=region_type,
                    methods=methods,
                    status='MISSING',
                    message=f'缺少 {region_type} 区域类型的识别方法'
                )
                self.validation_results.append(result)
                self.violations.append({
                    'type': 'missing_method',
                    'region_type': region_type,
                    'expected': primary_method,
                    'severity': 'ERROR'
                })
            elif len(methods) == 1:
                if methods[0].name == primary_method:
                    result = ValidationResult(
                        region_type=region_type,
                        methods=methods,
                        status='OK',
                        message=f'✓ {region_type}: {methods[0].name}'
                    )
                else:
                    result = ValidationResult(
                        region_type=region_type,
                        methods=methods,
                        status='WARNING',
                        message=f'⚠ {region_type}: 方法 {methods[0].name} 不是标准命名 (应为 {primary_method})'
                    )
                    self.violations.append({
                        'type': 'non_standard_name',
                        'region_type': region_type,
                        'method': methods[0].name,
                        'expected': primary_method,
                        'severity': 'WARNING'
                    })
                self.validation_results.append(result)
            else:
                result = ValidationResult(
                    region_type=region_type,
                    methods=methods,
                    status='ERROR',
                    message=f'✗ {region_type}: 发现 {len(methods)} 个识别方法，应只有1个: {", ".join(method_names)}'
                )
                self.validation_results.append(result)
                self.violations.append({
                    'type': 'multiple_methods',
                    'region_type': region_type,
                    'methods': method_names,
                    'severity': 'ERROR'
                })

        for name, node in self.methods:
            for pattern, label in self.FORBIDDEN_PATTERNS:
                import re
                if re.search(pattern, name):
                    self.violations.append({
                        'type': 'forbidden_pattern',
                        'method': name,
                        'lineno': node.lineno,
                        'pattern': label,
                        'severity': 'ERROR'
                    })

        return all(v['severity'] != 'ERROR' for v in self.violations)

    def generate_report(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("  区域分析器 - 主识别方法签名验证报告")
        lines.append("=" * 70)
        lines.append(f"  文件: {self.source_file}")
        lines.append("")

        lines.append("  [1] 每个区域类型的识别方法")
        lines.append("-" * 70)
        for result in self.validation_results:
            status_icon = {
                'OK': '✓',
                'WARNING': '⚠',
                'ERROR': '✗',
                'MISSING': '?'
            }.get(result.status, '?')

            lines.append(f"    {status_icon} {result.status:8s} | {result.message}")

        lines.append("")
        lines.append("  [2] 违规详情")
        lines.append("-" * 70)

        error_count = sum(1 for v in self.violations if v['severity'] == 'ERROR')
        warning_count = sum(1 for v in self.violations if v['severity'] == 'WARNING')

        if not self.violations:
            lines.append("    ✓ 未发现违规")
        else:
            for v in self.violations:
                severity_icon = {'ERROR': '✗', 'WARNING': '⚠'}.get(v['severity'], '?')
                lines.append(f"    {severity_icon} [{v['severity']}] {v['type']}")

                if v['type'] == 'multiple_methods':
                    lines.append(f"        区域类型: {v['region_type']}")
                    lines.append(f"        发现方法: {', '.join(v['methods'])}")
                    lines.append(f"        规范: 每个区域类型应有且仅有一个主识别方法")
                elif v['type'] == 'missing_method':
                    lines.append(f"        区域类型: {v['region_type']}")
                    lines.append(f"        期望方法: {v['expected']}")
                elif v['type'] == 'forbidden_pattern':
                    lines.append(f"        方法: {v['method']}:{v['lineno']}")
                    lines.append(f"        匹配模式: {v['pattern']}")
                elif v['type'] == 'non_standard_name':
                    lines.append(f"        区域类型: {v['region_type']}")
                    lines.append(f"        当前方法: {v['method']}")
                    lines.append(f"        建议方法: {v['expected']}")

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  统计: {error_count} 个错误, {warning_count} 个警告")
        lines.append(f"  结论: {'✓ 通过验证' if error_count == 0 else '✗ 验证失败'}")
        lines.append("=" * 70)

        return '\n'.join(lines)

    def get_summary(self) -> Dict:
        return {
            'file': str(self.source_file),
            'total_methods': len(self.methods),
            'total_violations': len(self.violations),
            'errors': sum(1 for v in self.violations if v['severity'] == 'ERROR'),
            'warnings': sum(1 for v in self.violations if v['severity'] == 'WARNING'),
            'status': 'PASS' if all(v['severity'] != 'ERROR' for v in self.violations) else 'FAIL'
        }


def main():
    if len(sys.argv) < 2:
        source_file = 'core/cfg/region_analyzer.py'
    else:
        source_file = sys.argv[1]

    validator = RegionAnalyzerSignatureValidator(source_file)

    if not validator.parse():
        sys.exit(1)

    is_valid = validator.validate()
    print(validator.generate_report())

    if is_valid:
        print("\n验证通过: 每个区域类型有且只有一个主识别方法")
        sys.exit(0)
    else:
        print("\n验证失败: 存在违反规范的识别方法")
        sys.exit(1)


if __name__ == '__main__':
    main()
