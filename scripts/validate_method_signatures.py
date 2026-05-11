"""
方法签名验证器 - 统一验证入口

验证区域分析器和区域AST生成器的方法签名规范：
1. 每个区域类型有且只有一个主识别方法
2. 每个区域类型有且只有一个主生成方法

防止补丁式编程模式。
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import re


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


class SignatureValidator:
    """统一方法签名验证器"""

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

    PRIMARY_GENERATE_METHODS: Dict[str, List[str]] = {
        'TRY_EXCEPT': ['_generate_try_except'],
        'TRY_FINALLY': ['_generate_try_except'],
        'FOR_LOOP': ['_generate_loop', '_generate_for_loop'],
        'WHILE_LOOP': ['_generate_loop', '_generate_while_loop'],
        'WITH': ['_generate_with'],
        'MATCH': ['_generate_match'],
        'ASSERT': ['_generate_assert'],
        'BOOL_OP': ['_generate_boolop'],
        'TERNARY': ['_generate_ternary'],
        'IF': ['_generate_if'],
        'IF_THEN': ['_generate_if'],
        'IF_THEN_ELSE': ['_generate_if'],
        'IF_ELIF_CHAIN': ['_generate_if'],
        'SEQUENCE': ['_generate_basic', '_generate_basic_region'],
        'BASIC': ['_generate_basic', '_generate_basic_region'],
    }

    FORBIDDEN_PATTERNS = [
        (r'_fix_', 'fix_pattern'),
        (r'_patch_', 'patch_pattern'),
        (r'_hack_', 'hack_pattern'),
        (r'_workaround_', 'workaround_pattern'),
        (r'_correct_', 'correct_pattern'),
        (r'_adjust_', 'adjust_pattern'),
    ]

    WARN_PATTERNS = [
        (r'_merge_', 'merge_pattern'),
        (r'_fallback_', 'fallback_pattern'),
        (r'_from_block', 'from_block_pattern'),
        (r'_raw_', 'raw_pattern'),
        (r'_unsafe_', 'unsafe_pattern'),
    ]

    IDENTIFY_TYPE_KEYWORDS = {
        'TRY_EXCEPT': ['try', 'except', 'finally', 'handler'],
        'FOR_LOOP': ['loop', 'for', 'while'],
        'WITH': ['with', 'context'],
        'MATCH': ['match', 'case'],
        'ASSERT': ['assert'],
        'BOOL_OP': ['bool', 'chained', 'compare'],
        'TERNARY': ['ternary', 'if_exp'],
        'IF': ['conditional', 'if', 'elif'],
        'SEQUENCE': ['sequence', 'basic', 'linear'],
    }

    GENERATE_TYPE_KEYWORDS = {
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

    def __init__(self, analyzer_file: str, generator_file: str):
        self.analyzer_file = Path(analyzer_file)
        self.generator_file = Path(generator_file)
        self.analyzer_tree: Optional[ast.AST] = None
        self.generator_tree: Optional[ast.AST] = None
        self.source_lines: Dict[str, List[str]] = {}
        self.analyzer_methods: List[Tuple[str, ast.FunctionDef]] = []
        self.generator_methods: List[Tuple[str, ast.FunctionDef]] = []
        self.validation_results: List[ValidationResult] = []
        self.violations: List[Dict] = []

    def parse(self) -> bool:
        if not self.analyzer_file.exists():
            print(f"错误: 文件不存在 {self.analyzer_file}")
            return False
        if not self.generator_file.exists():
            print(f"错误: 文件不存在 {self.generator_file}")
            return False

        for file_path in [self.analyzer_file, self.generator_file]:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            self.source_lines[str(file_path)] = source.splitlines()

            try:
                tree = ast.parse(source, filename=str(file_path))
                if 'analyzer' in file_path.name.lower():
                    self.analyzer_tree = tree
                else:
                    self.generator_tree = tree
            except SyntaxError as e:
                print(f"语法错误 {file_path}: {e}")
                return False

        self.analyzer_methods = self._extract_methods(self.analyzer_tree, 'RegionAnalyzer')
        self.generator_methods = self._extract_methods(self.generator_tree, 'RegionASTGenerator')
        return True

    def _extract_methods(self, tree: ast.AST, class_name: str) -> List[Tuple[str, ast.FunctionDef]]:
        result = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result.append((item.name, item))
        return result

    def _classify_identify_method(self, method_name: str) -> Optional[str]:
        if not method_name.startswith('_identify_'):
            return None
        method_lower = method_name.lower()

        if any(kw in method_lower for kw in ['try', 'except', 'finally', 'handler']):
            return 'TRY_EXCEPT'
        if any(kw in method_lower for kw in ['loop', 'for', 'while']):
            return 'FOR_LOOP'
        if any(kw in method_lower for kw in ['with', 'context']):
            return 'WITH'
        if any(kw in method_lower for kw in ['match', 'case']):
            return 'MATCH'
        if 'assert' in method_lower:
            return 'ASSERT'
        if any(kw in method_lower for kw in ['bool', 'chained', 'compare']):
            return 'BOOL_OP'
        if any(kw in method_lower for kw in ['ternary', 'if_exp']):
            return 'TERNARY'
        if any(kw in method_lower for kw in ['conditional', 'if', 'elif']):
            return 'IF'
        if any(kw in method_lower for kw in ['sequence', 'basic', 'linear']):
            return 'SEQUENCE'

        return None

    def _classify_generate_method(self, method_name: str) -> Optional[str]:
        if not method_name.startswith('_generate_'):
            return None
        method_lower = method_name.lower()

        for region_type, keywords in self.GENERATE_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in method_lower:
                    return region_type

        return None

    def validate(self) -> bool:
        self.validation_results = []
        self.violations = []

        self._validate_identify_methods()
        self._validate_generate_methods()
        self._check_patterns()

        return all(v['severity'] != 'ERROR' for v in self.violations)

    def _validate_identify_methods(self):
        identify_methods_by_type: Dict[str, List[MethodSignature]] = defaultdict(list)

        for name, node in self.analyzer_methods:
            region_type = self._classify_identify_method(name)
            if region_type:
                primary = self.PRIMARY_IDENTIFY_METHODS.get(region_type)
                sig = MethodSignature(
                    name=name, lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    region_type=region_type, is_primary=(name == primary)
                )
                identify_methods_by_type[region_type].append(sig)

        for region_type in sorted(self.PRIMARY_IDENTIFY_METHODS.keys()):
            methods = identify_methods_by_type.get(region_type, [])
            primary = self.PRIMARY_IDENTIFY_METHODS.get(region_type)
            method_names = [m.name for m in methods]

            if len(methods) == 0:
                self.validation_results.append(ValidationResult(
                    region_type=region_type, methods=[],
                    status='OK',
                    message=f'(统一由 {primary} 处理)'
                ))
            elif len(methods) == 1:
                if methods[0].name == primary:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='OK',
                        message=f'识别: {methods[0].name}'
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='OK',
                        message=f'识别: {methods[0].name} (兼容模式)'
                    ))
            else:
                primary_methods = [m for m in methods if m.name == primary]
                if len(primary_methods) == 1:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='WARNING',
                        message=f'识别: 发现 {len(methods)} 个方法，主方法: {primary}'
                    ))
                    self.violations.append({
                        'type': 'multiple_identify_methods', 'category': 'analyzer',
                        'region_type': region_type, 'methods': method_names,
                        'primary': primary, 'severity': 'WARNING'
                    })
                else:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='ERROR',
                        message=f'识别: 发现 {len(methods)} 个方法: {", ".join(method_names)}'
                    ))
                    self.violations.append({
                        'type': 'multiple_primary_identify', 'category': 'analyzer',
                        'region_type': region_type, 'methods': method_names, 'severity': 'ERROR'
                    })

    def _validate_generate_methods(self):
        generate_methods_by_type: Dict[str, List[MethodSignature]] = defaultdict(list)

        for name, node in self.generator_methods:
            region_type = self._classify_generate_method(name)
            if region_type:
                primaries = self.PRIMARY_GENERATE_METHODS.get(region_type, [])
                sig = MethodSignature(
                    name=name, lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    region_type=region_type, is_primary=(name in primaries)
                )
                generate_methods_by_type[region_type].append(sig)

        for region_type in sorted(self.PRIMARY_GENERATE_METHODS.keys()):
            methods = generate_methods_by_type.get(region_type, [])
            primaries = self.PRIMARY_GENERATE_METHODS.get(region_type, [])
            method_names = [m.name for m in methods]

            if len(methods) == 0:
                self.validation_results.append(ValidationResult(
                    region_type=region_type, methods=[],
                    status='WARNING',
                    message=f'缺少生成方法 (建议: {primaries[0] if primaries else "N/A"})'
                ))
                self.violations.append({
                    'type': 'missing_generate_method', 'category': 'generator',
                    'region_type': region_type, 'expected': primaries[0] if primaries else 'N/A',
                    'severity': 'WARNING'
                })
            elif len(methods) == 1:
                if methods[0].is_primary:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='OK',
                        message=f'生成: {methods[0].name}'
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='OK',
                        message=f'生成: {methods[0].name} (兼容模式)'
                    ))
            else:
                primary_methods = [m for m in methods if m.is_primary]
                if len(primary_methods) >= 1:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='OK',
                        message=f'生成: {", ".join([m.name for m in primary_methods])} (主方法)'
                    ))
                else:
                    self.validation_results.append(ValidationResult(
                        region_type=region_type, methods=methods,
                        status='WARNING',
                        message=f'生成: 发现 {len(methods)} 个方法'
                    ))
                    self.violations.append({
                        'type': 'no_primary_generate', 'category': 'generator',
                        'region_type': region_type, 'methods': method_names,
                        'expected': primaries, 'severity': 'WARNING'
                    })

    def _check_patterns(self):
        for name, node in self.analyzer_methods:
            for pattern, label in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, name):
                    self.violations.append({
                        'type': 'forbidden_pattern', 'category': 'analyzer',
                        'method': name, 'lineno': node.lineno,
                        'pattern': label, 'severity': 'ERROR'
                    })

            for pattern, label in self.WARN_PATTERNS:
                if re.search(pattern, name):
                    self.violations.append({
                        'type': 'warn_pattern', 'category': 'analyzer',
                        'method': name, 'lineno': node.lineno,
                        'pattern': label, 'severity': 'WARNING'
                    })

        for name, node in self.generator_methods:
            for pattern, label in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, name):
                    self.violations.append({
                        'type': 'forbidden_pattern', 'category': 'generator',
                        'method': name, 'lineno': node.lineno,
                        'pattern': label, 'severity': 'ERROR'
                    })

            for pattern, label in self.WARN_PATTERNS:
                if re.search(pattern, name):
                    self.violations.append({
                        'type': 'warn_pattern', 'category': 'generator',
                        'method': name, 'lineno': node.lineno,
                        'pattern': label, 'severity': 'WARNING'
                    })

    def generate_report(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("  方法签名验证报告 - 防补丁机制")
        lines.append("=" * 80)
        lines.append(f"  分析器: {self.analyzer_file}")
        lines.append(f"  生成器: {self.generator_file}")
        lines.append("")

        current_category = None
        for result in self.validation_results:
            cat = 'analyzer' if any(m.name.startswith('_identify_') for m in result.methods) else 'generator'
            if cat != current_category:
                current_category = cat
                lines.append(f"\n  [{'区域分析器 (识别方法)' if cat == 'analyzer' else '区域生成器 (生成方法)'}]")
                lines.append("-" * 80)

            status_icon = {'OK': '✓', 'WARNING': '⚠', 'ERROR': '✗', 'MISSING': '?'}.get(result.status, '?')
            lines.append(f"    {status_icon} {result.status:8s} | {result.region_type:15s} | {result.message}")

        lines.append("")
        lines.append("  [模式检查]")
        lines.append("-" * 80)

        errors = [v for v in self.violations if v['severity'] == 'ERROR']
        warnings = [v for v in self.violations if v['severity'] == 'WARNING']

        if not self.violations:
            lines.append("    ✓ 未发现违规模式")
        else:
            if errors:
                lines.append("  禁止模式 (ERROR):")
                for v in errors:
                    method = v.get('method', 'N/A')
                    lineno = v.get('lineno', 'N/A')
                    pattern = v.get('pattern', v.get('type', 'unknown'))
                    region_type = v.get('region_type', '')
                    extra = f" (区域: {region_type})" if region_type else ''
                    lines.append(f"    ✗ [{v['category']}] {method}:{lineno}{extra} - {pattern}")

            if warnings:
                lines.append("  警告模式 (WARNING):")
                for v in warnings:
                    method = v.get('method', 'N/A')
                    lineno = v.get('lineno', 'N/A')
                    pattern = v.get('pattern', v.get('type', 'unknown'))
                    region_type = v.get('region_type', '')
                    extra = f" (区域: {region_type})" if region_type else ''
                    lines.append(f"    ⚠ [{v['category']}] {method}:{lineno}{extra} - {pattern}")

        lines.append("")
        lines.append("=" * 80)
        lines.append(f"  统计: {len(errors)} 个错误, {len(warnings)} 个警告")
        lines.append(f"  结论: {'✓ 通过验证' if not errors else '✗ 验证失败 (存在禁止模式)'}")
        lines.append("=" * 80)

        return '\n'.join(lines)

    def get_summary(self) -> Dict:
        return {
            'analyzer_file': str(self.analyzer_file),
            'generator_file': str(self.generator_file),
            'analyzer_methods': len(self.analyzer_methods),
            'generator_methods': len(self.generator_methods),
            'total_violations': len(self.violations),
            'errors': sum(1 for v in self.violations if v['severity'] == 'ERROR'),
            'warnings': sum(1 for v in self.violations if v['severity'] == 'WARNING'),
            'status': 'PASS' if all(v['severity'] != 'ERROR' for v in self.violations) else 'FAIL'
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='验证区域方法签名规范')
    parser.add_argument('--analyzer', default='core/cfg/region_analyzer.py', help='区域分析器文件')
    parser.add_argument('--generator', default='core/cfg/region_ast_generator.py', help='区域生成器文件')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    parser.add_argument('--strict', action='store_true', help='严格模式：警告也视为错误')
    args = parser.parse_args()

    validator = SignatureValidator(args.analyzer, args.generator)

    if not validator.parse():
        sys.exit(1)

    is_valid = validator.validate()

    if args.json:
        import json
        print(json.dumps(validator.get_summary(), indent=2, ensure_ascii=False))
    else:
        print(validator.generate_report())

    if is_valid:
        if args.strict:
            print("\n⚠ 严格模式: 存在警告，请检查")
            sys.exit(0)
        else:
            print("\n✓ 验证通过: 方法签名符合防补丁规范")
            sys.exit(0)
    else:
        print("\n✗ 验证失败: 存在违反防补丁规范的禁止模式")
        sys.exit(1)


if __name__ == '__main__':
    main()
