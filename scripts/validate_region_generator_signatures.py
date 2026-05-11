"""
方法签名验证器 - 验证区域AST生成器的主生成方法

验证每个区域类型有且只有一个主生成方法，防止补丁式编程。
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


class RegionGeneratorSignatureValidator:
    """验证区域AST生成器的方法签名规范"""

    PRIMARY_GENERATE_METHODS: Dict[str, List[str]] = {
        'TRY_EXCEPT': ['_generate_try_except'],
        'TRY_FINALLY': ['_generate_try_finally'],
        'FOR_LOOP': ['_generate_for_loop'],
        'WHILE_LOOP': ['_generate_while_loop'],
        'WITH': ['_generate_with'],
        'MATCH': ['_generate_match'],
        'ASSERT': ['_generate_assert'],
        'BOOL_OP': ['_generate_boolop'],
        'TERNARY': ['_generate_ternary'],
        'IF': ['_generate_if'],
        'IF_THEN': ['_generate_if'],
        'IF_THEN_ELSE': ['_generate_if'],
        'IF_ELIF_CHAIN': ['_generate_if'],
        'SEQUENCE': ['_generate_basic'],
        'BASIC': ['_generate_basic'],
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
        (r'_from_block', 'from_block_pattern'),
        (r'_raw_', 'raw_pattern'),
        (r'_unsafe_', 'unsafe_pattern'),
    ]

    REGION_TYPE_KEYWORDS = {
        'TRY_EXCEPT': ['try', 'except', 'handler'],
        'TRY_FINALLY': ['try', 'finally', 'cleanup'],
        'FOR_LOOP': ['for', 'loop', 'iter'],
        'WHILE_LOOP': ['while', 'loop'],
        'WITH': ['with', 'context'],
        'MATCH': ['match', 'case', 'pattern'],
        'ASSERT': ['assert'],
        'BOOL_OP': ['bool', 'and', 'or', 'chained', 'compare'],
        'TERNARY': ['ternary', 'if_exp', 'conditional_expr'],
        'IF': ['if', 'branch', 'condition'],
        'IF_THEN': ['if', 'then'],
        'IF_THEN_ELSE': ['if', 'else', 'branch'],
        'IF_ELIF_CHAIN': ['elif', 'else_if'],
        'SEQUENCE': ['sequence', 'basic', 'linear'],
        'BASIC': ['basic', 'simple', 'linear'],
    }

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
                if node.name == 'RegionASTGenerator':
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            result.append((item.name, item))
        return result

    def _classify_generate_method(self, method_name: str) -> Optional[str]:
        if not method_name.startswith('_generate_'):
            return None

        method_lower = method_name.lower()

        for region_type, keywords in self.REGION_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in method_lower:
                    return region_type

        return None

    def validate(self) -> bool:
        generate_methods_by_type: Dict[str, List[MethodSignature]] = defaultdict(list)

        for name, node in self.methods:
            region_type = self._classify_generate_method(name)
            if region_type:
                primary_methods = self.PRIMARY_GENERATE_METHODS.get(region_type, [])
                is_primary = name in primary_methods
                sig = MethodSignature(
                    name=name,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    region_type=region_type,
                    is_primary=is_primary
                )
                generate_methods_by_type[region_type].append(sig)

        for region_type, methods in sorted(generate_methods_by_type.items()):
            primary_methods = self.PRIMARY_GENERATE_METHODS.get(region_type, [])
            method_names = [m.name for m in methods]

            if len(methods) == 0:
                result = ValidationResult(
                    region_type=region_type,
                    methods=methods,
                    status='MISSING',
                    message=f'缺少 {region_type} 区域类型的生成方法'
                )
                self.validation_results.append(result)
                self.violations.append({
                    'type': 'missing_method',
                    'region_type': region_type,
                    'expected': primary_methods[0] if primary_methods else 'N/A',
                    'severity': 'WARNING'
                })
            elif len(methods) == 1:
                if methods[0].is_primary:
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
                        message=f'⚠ {region_type}: 方法 {methods[0].name} 不是标准命名 (应为 {primary_methods[0] if primary_methods else "N/A"})'
                    )
                    self.violations.append({
                        'type': 'non_standard_name',
                        'region_type': region_type,
                        'method': methods[0].name,
                        'expected': primary_methods[0] if primary_methods else 'N/A',
                        'severity': 'WARNING'
                    })
                self.validation_results.append(result)
            else:
                primary_count = sum(1 for m in methods if m.is_primary)
                if primary_count == 1:
                    result = ValidationResult(
                        region_type=region_type,
                        methods=methods,
                        status='WARNING',
                        message=f'⚠ {region_type}: 发现 {len(methods)} 个生成方法，建议统一为: {", ".join(primary_methods) if primary_methods else methods[0].name}'
                    )
                    self.violations.append({
                        'type': 'multiple_methods_warning',
                        'region_type': region_type,
                        'methods': method_names,
                        'severity': 'WARNING'
                    })
                else:
                    result = ValidationResult(
                        region_type=region_type,
                        methods=methods,
                        status='ERROR',
                        message=f'✗ {region_type}: 发现 {len(methods)} 个主生成方法，应只有1个: {", ".join([m.name for m in methods if m.is_primary])}'
                    )
                    self.violations.append({
                        'type': 'multiple_primary_methods',
                        'region_type': region_type,
                        'methods': method_names,
                        'severity': 'ERROR'
                    })
                self.validation_results.append(result)

        for name, node in self.methods:
            import re
            for pattern, label in self.FORBIDDEN_PATTERNS:
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
        lines.append("  区域AST生成器 - 主生成方法签名验证报告")
        lines.append("=" * 70)
        lines.append(f"  文件: {self.source_file}")
        lines.append("")

        lines.append("  [1] 每个区域类型的生成方法")
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

                if v['type'] == 'multiple_primary_methods':
                    lines.append(f"        区域类型: {v['region_type']}")
                    lines.append(f"        发现主方法: {', '.join(v['methods'])}")
                    lines.append(f"        规范: 每个区域类型应有且仅有一个主生成方法")
                elif v['type'] == 'multiple_methods_warning':
                    lines.append(f"        区域类型: {v['region_type']}")
                    lines.append(f"        发现方法: {', '.join(v['methods'])}")
                    lines.append(f"        建议: 统一为一个主生成方法以保持一致性")
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
        source_file = 'core/cfg/region_ast_generator.py'
    else:
        source_file = sys.argv[1]

    validator = RegionGeneratorSignatureValidator(source_file)

    if not validator.parse():
        sys.exit(1)

    is_valid = validator.validate()
    print(validator.generate_report())

    if is_valid:
        print("\n验证通过: 每个区域类型有且只有一个主生成方法")
        sys.exit(0)
    else:
        print("\n验证失败: 存在违反规范的主生成方法")
        sys.exit(1)


if __name__ == '__main__':
    main()
