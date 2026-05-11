#!/usr/bin/env python3
"""
CFG区域归约反编译 - 防补丁合规性审计脚本 v2.0

6大审计维度：
1. 方法命名审计（FAIL级别）- 禁止的补丁式方法名模式
2. 后处理修正审计（FAIL级别）- region创建后修改region.blocks
3. 跨职责审计（WARN级别）- 生成器中的分析API调用
4. 多路径审计（FAIL级别）- 同一AST节点类型的多个生成方法
5. 硬编码偏移审计（WARN级别）- magic number offset/block_id依赖
6. 操作码白名单审计（WARN级别）- 大型操作码集合推断语义角色

输出：PASS/WARN/FAIL三级报告 + JSON（CI使用）
"""

import ast
import os
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AuditLevel(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class AuditResult:
    level: AuditLevel
    category: str
    message: str
    file: str
    line: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class ComplianceAuditor:
    """CFG防补丁合规性审计器"""

    # 禁止的方法名模式（FAIL级别）
    FORBIDDEN_METHOD_PATTERNS = [
        r'_fix_',           # 后处理修正方法
        r'_merge_',         # 合并已识别区域方法
        r'_patch_',         # 补丁方法
        r'_fallback_',      # 回退逻辑方法
        r'_special_case_',  # 特殊情况处理方法
        r'_try_generate_',  # 多生成路径尝试方法
    ]

    # 需要审计的核心文件
    TARGET_FILES = {
        'core/cfg/region_analyzer.py': 'RegionAnalyzer - 区域识别与分析',
        'core/cfg/region_ast_generator.py': 'RegionAstGenerator - AST生成',
    }

    # 跨职责检测 - 生成器中禁止直接调用的分析API
    FORBIDDEN_ANALYSIS_APIS = [
        'dominator_tree',
        'back_edges',
        'find_nearest_common_post_dominator',
        'block_to_region',
    ]

    # RegionType到生成方法的映射
    REGION_TYPE_GENERATE_METHODS = {
        'IfRegion': ['_generate_if'],
        'LoopRegion': ['_generate_loop'],
        'TryExceptRegion': ['_generate_try'],
        'WithRegion': ['_generate_with', '_generate_with_impl'],  # _generate_with_impl是内部实现
        'MatchRegion': ['_generate_match', '_generate_match_as_if'],  # _generate_match_as_if是特殊处理
        'AssertRegion': ['_generate_assert'],
        'BoolOpRegion': ['_generate_boolop'],
        'TernaryRegion': ['_generate_ternary'],
        'BasicRegion': ['_generate_basic_region'],
    }

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results: List[AuditResult] = []
        self.verbose = False
        self.json_output = False
        self.file_stats: Dict[str, int] = {}

    def audit_all(self) -> Dict[str, Any]:
        """执行全部6大审计维度"""
        print("=" * 80)
        print("=== CFG Compliance Audit Report ===")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 80)

        # 统计文件信息
        print("\nFiles Scanned:")
        for rel_path, desc in self.TARGET_FILES.items():
            file_path = self.base_path / rel_path
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    method_count = len(re.findall(r'def \w+', content))
                    self.file_stats[rel_path] = method_count
                    print(f"  - {rel_path} ({method_count} methods)")
            else:
                print(f"  - {rel_path} (NOT FOUND)")

        print("\nResults:")

        # 维度1: 方法命名审计（FAIL级别）
        self._audit_method_naming()

        # 维度2: 后处理修正审计（FAIL级别）
        self._audit_post_processing_modification()

        # 维度3: 跨职责审计（WARN级别）
        self._audit_cross_responsibility()

        # 维度4: 多路径审计（FAIL级别）
        self._audit_multiple_generation_paths()

        # 维度5: 硬编码偏移审计（WARN级别）
        self._audit_hardcoded_offsets()

        # 维度6: 操作码白名单审计（WARN级别）
        self._audit_opcode_whitelists()

        # 生成报告
        return self._generate_report()

    def _audit_method_naming(self):
        """维度1: 方法命名审计（FAIL级别）"""
        print("\n" + "-" * 80)
        violations = []

        for rel_path in self.TARGET_FILES.keys():
            file_path = self.base_path / rel_path
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # 检测方法定义是否匹配禁止的模式
                for pattern in self.FORBIDDEN_METHOD_PATTERNS:
                    regex = rf'def {pattern}\w*\s*\('
                    match = re.search(regex, line)
                    if match:
                        result = AuditResult(
                            level=AuditLevel.FAIL,
                            category='METHOD_NAMING',
                            message=f"发现禁止的方法名模式 '{pattern}'",
                            file=str(file_path),
                            line=line_num,
                            details={'pattern': pattern, 'line_content': line.strip()}
                        )
                        self.results.append(result)
                        violations.append(result)
                        if self.verbose:
                            print(f"  [FAIL] {file_path}:{line_num}: {line.strip()}")

        if len(violations) == 0:
            print("✅ PASS: Method naming compliance (0 forbidden patterns found)")
        else:
            print(f"❌ FAIL: Method naming violation ({len(violations)} forbidden patterns found)")

    def _audit_post_processing_modification(self):
        """维度2: 后处理修正审计（FAIL级别）- 检测region创建后修改region.blocks"""
        print("\n" + "-" * 80)
        violations = []

        for rel_path in self.TARGET_FILES.keys():
            file_path = self.base_path / rel_path
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 检测对region.blocks的修改操作
            modification_patterns = [
                (r'region\.blocks\.add\(', 'region.blocks.add()'),
                (r'region\.blocks\.remove\(', 'region.blocks.remove()'),
                (r'region\.blocks\.discard\(', 'region.blocks.discard()'),
                (r'\w+region\.blocks\s*[^=]*=', 'direct assignment to region.blocks'),
            ]

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # 跳过注释和空行
                if not stripped or stripped.startswith('#'):
                    continue

                for pattern, desc in modification_patterns:
                    if re.search(pattern, line):
                        # 排除Region类定义本身中的方法
                        context_start = max(0, line_num - 30)
                        context = ''.join(lines[context_start:line_num])
                        if 'class Region' in context or 'def add_block' in context:
                            continue

                        result = AuditResult(
                            level=AuditLevel.FAIL,
                            category='POST_PROCESSING',
                            message=f"Post-processing detected: {desc}",
                            file=str(file_path),
                            line=line_num,
                            details={'pattern': desc, 'line_content': stripped[:120]}
                        )
                        self.results.append(result)
                        violations.append(result)
                        if self.verbose:
                            method_name = self._get_current_method(lines, line_num)
                            print(f"  [FAIL] {file_path}:{line_num} in {method_name}: {desc}")
                            print(f"         {stripped[:120]}")

        if len(violations) == 0:
            print("✅ PASS: No post-processing modifications detected")
        else:
            print(f"❌ FAIL: Post-processing detected ({len(violations)} violations)")
            if not self.verbose:
                for v in violations[:3]:  # 显示前3个违规
                    print(f"       - {v.file}:{v.line}: {v.message}")

    def _audit_cross_responsibility(self):
        """维度3: 跨职责审计（WARN级别）- 检测region_ast_generator.py中的分析API调用"""
        print("\n" + "-" * 80)
        violations = []

        generator_file = self.base_path / 'core/cfg/region_ast_generator.py'
        if not generator_file.exists():
            print("⚠️ WARN: region_ast_generator.py not found")
            return

        with open(generator_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # 跳过注释、空行、字符串、导入语句
            if (not stripped or
                stripped.startswith('#') or
                stripped.startswith('"""') or
                stripped.startswith("'''") or
                stripped.startswith('from ') or
                stripped.startswith('import ')):
                continue

            # 检测禁止的分析API调用
            for api in self.FORBIDDEN_ANALYSIS_APIS:
                # 匹配 API 调用（排除注释和字符串中的引用）
                if re.search(rf'\b{re.escape(api)}\s*\(', line) or \
                   re.search(rf'\b{re.escape(api)}\b', line):
                    # 允许某些合法的使用场景
                    if any(allowed in line for allowed in [
                        '#', '"""', "'''",
                        'block_role(',  # block_role是查询接口，允许
                        'get_region_for_block(',  # 查询接口，允许
                        'get_block_role(',  # 查询接口，允许
                    ]):
                        continue

                    result = AuditResult(
                        level=AuditLevel.WARN,
                        category='CROSS_RESPONSIBILITY',
                        message=f"Cross-responsibility: direct call to analysis API '{api}'",
                        file=str(generator_file),
                        line=line_num,
                        details={'api': api, 'line_content': stripped[:120]}
                    )
                    self.results.append(result)
                    violations.append(result)
                    if self.verbose:
                        method_name = self._get_current_method(lines, line_num)
                        print(f"  [WARN] {generator_file}:{line_num} in {method_name}: {api}")
                        print(f"         {stripped[:120]}")

        if len(violations) == 0:
            print("✅ PASS: No cross-responsibility violations detected")
        else:
            print(f"⚠️ WARN: Cross-responsibility in region_ast_generator.py ({len(violations)} analysis API calls)")

    def _audit_multiple_generation_paths(self):
        """维度4: 多路径审计（FAIL级别）- 检测同一AST节点类型的多个生成方法"""
        print("\n" + "-" * 80)
        violations = []

        generator_file = self.base_path / 'core/cfg/region_ast_generator.py'
        if not generator_file.exists():
            print("⚠️ WARN: region_ast_generator.py not found")
            return

        with open(generator_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有_generate_*方法
        generate_methods = re.findall(r'def (_generate_\w+)\s*\(', content)

        # 内部实现方法后缀（这些不是独立路径）
        INTERNAL_SUFFIXES = ('_impl', '_body', '_internal', '_statements')

        # 按类型分组并检查是否有多个公共生成方法
        for region_type, expected_methods in self.REGION_TYPE_GENERATE_METHODS.items():
            # 找到所有相关方法
            related_methods = [m for m in generate_methods
                             if any(exp in m for exp in expected_methods)]

            # 过滤掉内部实现方法
            public_methods = [m for m in related_methods
                            if not any(m.endswith(suffix) for suffix in INTERNAL_SUFFIXES)]

            # 如果有多个公共方法生成相同类型的节点
            if len(public_methods) > 1:
                result = AuditResult(
                    level=AuditLevel.FAIL,
                    category='MULTIPLE_PATHS',
                    message=f"{region_type} has multiple generation methods: {public_methods}",
                    file=str(generator_file),
                    details={'region_type': region_type, 'methods': public_methods}
                )
                self.results.append(result)
                violations.append(result)
                if self.verbose:
                    print(f"  [FAIL] {region_type}: {len(public_methods)} public methods: {public_methods}")

        if len(violations) == 0:
            print("✅ PASS: Single generation path per region type")
        else:
            print(f"❌ FAIL: Multiple generation paths detected ({len(violations)} region types affected)")

    def _audit_hardcoded_offsets(self):
        """维度5: 硬编码偏移审计（WARN级别）- magic number依赖"""
        print("\n" + "-" * 80)
        violations = []

        for rel_path in self.TARGET_FILES.keys():
            file_path = self.base_path / rel_path
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # 跳过注释、常量定义、文档字符串
                if (not stripped or
                    stripped.startswith('#') or
                    stripped.startswith('"""') or
                    stripped.startswith("'''") or
                    re.match(r'^[A-Z_]+\s*=\s*', stripped) or  # 常量定义
                    re.match(r'^\w+\s*=\s*\d+\s*#.*constant', stripped)):  # 带注释的常量
                    continue

                # 检测硬编码偏移或block_id
                patterns = [
                    (r'offset\s*==\s*\d+', 'Hard-coded offset comparison'),
                    (r'block_id\s*==\s*\d+', 'Hard-coded block_id comparison'),
                    (r'if\s+\w+.*==\s*\d+\s*:', 'Hard-coded numeric comparison (possible offset/block_id)'),
                ]

                for pattern, desc in patterns:
                    if re.search(pattern, line):
                        # 排除明显安全的情况
                        if any(safe in line for safe in [
                            '#', 'range(', 'len(', 'enumerate(',
                            'FOR_ITER_OPS', 'NOISE_OPS', 'CLEANUP_OPS',  # 操作码集合
                            'MIN_INSTRS_FOR',  # 配置常量
                        ]):
                            continue

                        result = AuditResult(
                            level=AuditLevel.WARN,
                            category='HARDCODED_OFFSET',
                            message=desc,
                            file=str(file_path),
                            line=line_num,
                            details={'line_content': stripped[:120]}
                        )
                        self.results.append(result)
                        violations.append(result)
                        if self.verbose:
                            method_name = self._get_current_method(lines, line_num)
                            print(f"  [WARN] {file_path}:{line_num} in {method_name}: {desc}")
                            print(f"         {stripped[:120]}")

        if len(violations) == 0:
            print("✅ PASS: No hard-coded offsets detected")
        else:
            print(f"⚠️ WARN: Hard-coded offsets ({len(violations)} occurrences)")

    def _audit_opcode_whitelists(self):
        """维度6: 操作码白名单审计（WARN级别）- 大型操作码集合推断语义角色"""
        print("\n" + "-" * 80)
        violations = []

        for rel_path in self.TARGET_FILES.keys():
            file_path = self.base_path / rel_path
            if not file_path.exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 已知的合法噪声过滤白名单
            LEGITIMATE_NOISE_WHITELISTS = [
                'NOISE_OPS',
                'CLEANUP_OPS',
                'PURE_JUMP_OPS',
                'PLACEHOLDER_OPS',
                'RERAISE_ONLY_OPS',
                'WITH_EXIT_INDICATOR_OPS',
            ]

            # 检测大型操作码集合的定义和使用
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # 跳过注释和空行
                if not stripped or stripped.startswith('#'):
                    continue

                # 检测frozenset/set定义（可能包含大量操作码）
                if re.match(r'\w+_OPS\s*=\s*frozenset\(\{', line):
                    # 收集整个集合定义
                    set_content = stripped
                    brace_count = line.count('{') - line.count('}')
                    current_line = line_num

                    while brace_count > 0 and current_line < len(lines) - 1:
                        current_line += 1
                        set_content += lines[current_line - 1]
                        brace_count += lines[current_line - 1].count('{') - lines[current_line - 1].count('}')

                    # 统计操作码数量
                    opcodes = re.findall(r"'[\w_]+'", set_content)
                    opcode_count = len(opcodes)

                    # 提取变量名
                    var_match = re.match(r'(\w+_OPS)\s*=', stripped)
                    var_name = var_match.group(1) if var_match else 'UNKNOWN'

                    # 如果超过10个操作码且不是已知的合法白名单
                    if opcode_count > 10 and var_name not in LEGITIMATE_NOISE_WHITELISTS:
                        # 检查是否用于语义判断（而非噪声过滤）
                        context_end = min(line_num + 20, len(lines))
                        context = ''.join(lines[line_num:context_end])

                        semantic_indicators = [
                            r'if.*all\(.*in\s*' + re.escape(var_name),
                            r'if.*any\(.*in\s*' + re.escape(var_name),
                            r'.*in\s*' + re.escape(var_name) + r'.*role',
                            r'.*in\s*' + re.escape(var_name) + r'.*type',
                            r'.*in\s*' + re.escape(var_name) + r'.*semantic',
                            r'.*in\s*' + re.escape(var_name) + r'.*identify',
                        ]

                        is_semantic = any(re.search(ind, context, re.IGNORECASE)
                                        for ind in semantic_indicators)

                        if is_semantic:
                            result = AuditResult(
                                level=AuditLevel.WARN,
                                category='OPCODE_WHITELIST',
                                message=f"Opcode whitelist used for semantic inference: {var_name} ({opcode_count} opcodes)",
                                file=str(file_path),
                                line=line_num,
                                details={
                                    'var_name': var_name,
                                    'opcode_count': opcode_count,
                                    'usage': 'semantic_inference'
                                }
                            )
                            self.results.append(result)
                            violations.append(result)
                            if self.verbose:
                                method_name = self._get_current_method(lines, line_num)
                                print(f"  [WARN] {file_path}:{line_num} in {method_name}")
                                print(f"         {var_name}: {opcode_count} opcodes used for semantic inference")

        if len(violations) == 0:
            print("✅ PASS: No problematic opcode whitelists detected")
        else:
            print(f"⚠️ WARN: Opcode whitelists ({len(violations)} semantic inference whitelists found)")

    def _get_current_method(self, lines: List[str], line_num: int) -> str:
        """获取指定行所在的方法名"""
        # 向上搜索最近的方法定义
        for i in range(line_num - 1, max(0, line_num - 100), -1):
            match = re.match(r'def (\w+)\s*\(', lines[i])
            if match:
                return match.group(1)
        return '<unknown>'

    def _generate_report(self) -> Dict[str, Any]:
        """生成审计报告"""
        print("\n" + "=" * 80)
        print("Summary:")
        print("=" * 80)

        # 统计各级别数量
        fail_results = [r for r in self.results if r.level == AuditLevel.FAIL]
        warn_results = [r for r in self.results if r.level == AuditLevel.WARN]

        fail_count = len(fail_results)
        warn_count = len(warn_results)

        # 计算通过的审计项数（6个维度 - 有问题的）
        total_dimensions = 6
        failed_categories = set(r.category for r in fail_results)
        warned_categories = set(r.category for r in warn_results)
        pass_count = total_dimensions - len(failed_categories) - len(warned_categories)

        print(f"\n  FAIL: {fail_count} (must fix before commit)")
        print(f"  WARN: {warn_count} (should fix in next sprint)")
        print(f"  PASS: {pass_count}")

        # 输出FAIL项详情
        if fail_count > 0:
            print(f"\n❌ FAIL Details:")
            for r in fail_results:
                print(f"  - [{r.category}] {Path(r.file).name}:{r.line}")
                print(f"    {r.message}")

        # 输出WARN项详情
        if warn_count > 0:
            print(f"\n⚠️  WARN Details:")
            for r in warn_results[:5]:  # 只显示前5个WARN
                print(f"  - [{r.category}] {Path(r.file).name}:{r.line}")
                print(f"    {r.message}")
            if warn_count > 5:
                print(f"  ... and {warn_count - 5} more warnings")

        # 判断总体状态
        if fail_count == 0:
            overall_status = "✅ COMPLIANT"
            print(f"\nOverall: {overall_status}")
        else:
            overall_status = f"❌ NOT COMPLIANT ({fail_count} FAIL found)"
            print(f"\nOverall: {overall_status}")

        # 构建JSON报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': len(self.results),
                'fail': fail_count,
                'warn': warn_count,
                'pass': pass_count,
                'status': 'COMPLIANT' if fail_count == 0 else 'NOT_COMPLIANT',
                'overall_status': overall_status,
            },
            'files_scanned': self.file_stats,
            'categories': {
                'METHOD_NAMING': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
                'POST_PROCESSING': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
                'CROSS_RESPONSIBILITY': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
                'MULTIPLE_PATHS': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
                'HARDCODED_OFFSET': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
                'OPCODE_WHITELIST': {'PASS': 0, 'WARN': 0, 'FAIL': 0},
            },
            'issues': [
                {
                    'level': r.level.value,
                    'category': r.category,
                    'message': r.message,
                    'file': r.file,
                    'line': r.line,
                    'details': r.details,
                }
                for r in self.results
            ]
        }

        # 更新分类统计
        for r in self.results:
            if r.category in report['categories']:
                report['categories'][r.category][r.level.value] += 1

        # 标记通过的类别
        for cat in report['categories']:
            if report['categories'][cat]['FAIL'] == 0 and report['categories'][cat]['WARN'] == 0:
                report['categories'][cat]['PASS'] = 1

        return report


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='CFG防补丁合规性审计工具 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python audit_compliance.py                          # 运行完整审计
  python audit_compliance.py -v                       # 显示详细信息
  python audit_compliance.py --json -o report.json     # 输出JSON报告
  python audit_compliance.py --base-path ../pythoncdc  # 指定项目根目录
        """
    )
    parser.add_argument('--base-path', '-b', default='.', help='项目根目录 (默认: 当前目录)')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--json', '-j', action='store_true', help='输出JSON格式')
    parser.add_argument('--output', '-o', help='输出文件路径 (仅配合--json使用)')

    args = parser.parse_args()

    auditor = ComplianceAuditor(args.base_path)
    auditor.verbose = args.verbose
    auditor.json_output = args.json

    report = auditor.audit_all()

    if args.json:
        output = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n📄 JSON报告已保存到: {args.output}")
        else:
            print('\n' + output)

    # 返回退出码（CI使用）
    sys.exit(0 if report['summary']['fail'] == 0 else 1)


if __name__ == '__main__':
    main()
