"""
方法合规性审计脚本

检查 region_analyzer.py 和 region_ast_generator.py 中的补丁模式。
基于7项结构性特征（非注释型）检测方法是否为补丁。

用法: python scripts/audit_methods.py
"""

import ast
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any


REGION_SUBCLASS_NAMES = {
    'IfRegion', 'LoopRegion', 'TryExceptRegion', 'WithRegion',
    'MatchRegion', 'AssertRegion', 'BoolOpRegion', 'TernaryRegion',
}

REGION_DATA_ATTRS = {
    'condition_block', 'then_blocks', 'else_blocks', 'merge_block',
    'elif_conditions', 'elif_bodies', 'elif_final_else',
    'chained_compare_blocks', 'chained_compare_ops',
    'chained_left_instr', 'chained_comparator_instrs',
    'header_block', 'body_blocks', 'init_blocks', 'is_async',
    'back_edge_block', 'is_while_true', 'has_break', 'else_is_follow',
    'pre_condition_blocks', 'try_blocks', 'except_handlers',
    'has_else', 'has_finally', 'try_offset_start', 'try_offset_end',
    'handler_entry_blocks', 'finally_copy_blocks', 'cleanup_blocks',
    'with_blocks', 'exception_blocks', 'resource_expr', 'target',
    'items', 'body_offset_start', 'body_offset_end',
    'subject_block', 'case_blocks', 'case_patterns', 'case_guards',
    'case_bodies', 'parent_region', 'message_block',
    'op_chain', 'value_target', 'prefix_block', 'prefix_op_type',
    'body_block', 'condition_expr',
    'true_value_block', 'false_value_block',
    'region_type', 'entry', 'blocks', 'exit', 'parent', 'children',
    'metadata', 'finally_blocks',
}

SPECIAL_OPCODE_NAMES = {
    'FOR_ITER', 'SETUP_FINALLY', 'SETUP_WITH', 'BEFORE_WITH',
    'POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE', 'GET_ITER',
    'GET_ANEXT', 'BEFORE_ASYNC_WITH', 'SETUP_ASYNC_WITH',
    'WITH_CLEANUP_START', 'WITH_CLEANUP_FINISH',
    'LOAD_ASSERTION_ERROR', 'COMPARE_OP',
    'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE',
    'MATCH_KEYS', 'COPY_DICT_WITHOUT_KEYS',
}

AST_NODE_TYPE_MAP = {
    'If': ['_generate_if', '_try_generate_ifexp'],
    'For': ['_loop_generate_for'],
    'While': ['_loop_generate_while'],
    'Try': ['_generate_try'],
    'With': ['_generate_with'],
    'Match': ['_generate_match'],
    'BoolOp': ['_generate_boolop'],
    'Ternary': ['_generate_ternary'],
}

CFG_TRAVERSAL_ATTRS = {
    'successors', 'predecessors',
}

DOMINATOR_ATTRS = {
    'dominator', 'dom_analyzer', 'dom_tree', 'immediate_dominator',
    'dominance', 'dom_frontier', 'post_dominator',
}


@dataclass
class Violation:
    criterion: str
    criterion_id: int
    line: int
    detail: str


@dataclass
class MethodReport:
    file_path: str
    class_name: str
    method_name: str
    start_line: int
    end_line: int
    violations: List[Violation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    @property
    def compliance_scores(self) -> Dict[str, bool]:
        scores = {}
        for i in range(1, 8):
            criterion_name = CRITERION_NAMES[i]
            has_violation = any(v.criterion_id == i for v in self.violations)
            scores[criterion_name] = not has_violation
        return scores


CRITERION_NAMES = {
    1: "后处理修改 (Post-processing modification)",
    2: "特殊情况分支 (Special case branches)",
    3: "多重生成路径 (Multiple generation paths)",
    4: "跨职责修改 (Cross-responsibility modification)",
    5: "硬编码偏移 (Hardcoded offsets)",
    6: "顺序依赖 (Order dependency)",
    7: "修改其他区域 (Modifying other regions)",
}


class MethodVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.methods: List[Tuple[str, str, ast.FunctionDef]] = []
        self.class_methods: Dict[str, List[Tuple[str, ast.FunctionDef]]] = {}
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self._current_class
        self._current_class = node.name
        self.class_methods[node.name] = []
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._current_class:
            self.class_methods[self._current_class].append(
                (self._current_class, node)
            )
            self.methods.append((self._current_class, self._current_class, node))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if self._current_class:
            self.class_methods[self._current_class].append(
                (self._current_class, node)
            )
            self.methods.append((self._current_class, self._current_class, node))
        self.generic_visit(node)


class PatchAuditor:
    def __init__(self, analyzer_path: str, generator_path: str):
        self.analyzer_path = analyzer_path
        self.generator_path = generator_path
        self.analyzer_tree = self._parse_file(analyzer_path)
        self.generator_tree = self._parse_file(generator_path)
        self.analyzer_source = self._read_source(analyzer_path)
        self.generator_source = self._read_source(generator_path)
        self.analyzer_methods = self._collect_methods(analyzer_path, self.analyzer_tree)
        self.generator_methods = self._collect_methods(generator_path, self.generator_tree)
        self.analyzer_init_methods = self._find_init_methods(self.analyzer_methods)
        self.generator_init_methods = self._find_init_methods(self.generator_methods)

    def _parse_file(self, path: str) -> ast.Module:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        return ast.parse(source, filename=path)

    def _read_source(self, path: str) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _collect_methods(self, file_path: str, tree: ast.Module) -> List[Tuple[str, str, ast.FunctionDef]]:
        visitor = MethodVisitor(file_path)
        visitor.visit(tree)
        return visitor.methods

    def _find_init_methods(self, methods: List[Tuple[str, str, ast.FunctionDef]]) -> Set[str]:
        init_names = set()
        for cls_name, _, node in methods:
            if node.name == '__init__':
                init_names.add(cls_name)
        return init_names

    def _get_region_creator_methods(self, methods: List[Tuple[str, str, ast.FunctionDef]]) -> Dict[str, str]:
        creator_map = {}
        for cls_name, _, node in methods:
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name) and func.id in REGION_SUBCLASS_NAMES:
                        creator_map[node.name] = func.id
                        break
                    if (isinstance(func, ast.Attribute) and
                            isinstance(func.value, ast.Name) and
                            func.attr in REGION_SUBCLASS_NAMES):
                        creator_map[node.name] = func.attr
                        break
        return creator_map

    def audit(self) -> List[MethodReport]:
        reports = []
        analyzer_creators = self._get_region_creator_methods(self.analyzer_methods)
        generator_creators = self._get_region_creator_methods(self.generator_methods)

        for cls_name, _, node in self.analyzer_methods:
            report = self._audit_method(
                self.analyzer_path, cls_name, node,
                self.analyzer_methods, self.generator_methods,
                analyzer_creators, generator_creators,
                is_generator=False
            )
            reports.append(report)

        for cls_name, _, node in self.generator_methods:
            report = self._audit_method(
                self.generator_path, cls_name, node,
                self.analyzer_methods, self.generator_methods,
                analyzer_creators, generator_creators,
                is_generator=True
            )
            reports.append(report)

        return reports

    def _audit_method(
        self,
        file_path: str,
        class_name: str,
        node: ast.FunctionDef,
        analyzer_methods: List[Tuple[str, str, ast.FunctionDef]],
        generator_methods: List[Tuple[str, str, ast.FunctionDef]],
        analyzer_creators: Dict[str, str],
        generator_creators: Dict[str, str],
        is_generator: bool,
    ) -> MethodReport:
        report = MethodReport(
            file_path=file_path,
            class_name=class_name,
            method_name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
        )

        self._check_post_processing_modification(node, report, analyzer_creators, generator_creators, is_generator)
        self._check_special_case_branches(node, report)
        self._check_multiple_generation_paths(node, report, generator_methods)
        self._check_cross_responsibility(node, report, is_generator)
        self._check_hardcoded_offsets(node, report)
        self._check_order_dependency(node, report, analyzer_methods)
        self._check_modifying_other_regions(node, report, analyzer_creators, generator_creators)

        return report

    def _check_post_processing_modification(
        self,
        node: ast.FunctionDef,
        report: MethodReport,
        analyzer_creators: Dict[str, str],
        generator_creators: Dict[str, str],
        is_generator: bool,
    ):
        if node.name == '__init__':
            return

        all_creators = {**analyzer_creators, **generator_creators}
        current_creates_region = node.name in all_creators

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.ctx, ast.Store):
                attr_name = child.attr
                if attr_name in REGION_DATA_ATTRS:
                    value = child.value
                    is_region_obj = False
                    if isinstance(value, ast.Name):
                        if value.id in REGION_SUBCLASS_NAMES or value.id in ('region', 'r', 'loop_region', 'if_region',
                                                                              'try_region', 'with_region', 'match_region',
                                                                              'boolop_region', 'ternary_region', 'assert_region'):
                            is_region_obj = True
                    elif isinstance(value, ast.Attribute):
                        if value.attr in REGION_SUBCLASS_NAMES or value.attr in ('region', 'r'):
                            is_region_obj = True

                    if is_region_obj and not current_creates_region:
                        report.violations.append(Violation(
                            criterion=CRITERION_NAMES[1],
                            criterion_id=1,
                            line=child.lineno,
                            detail=f"方法 '{node.name}' 修改了 region.{attr_name}，但不是该 region 的创建者"
                        ))

    def _check_special_case_branches(self, node: ast.FunctionDef, report: MethodReport):
        special_opcode_checks = []

        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                for comparator in child.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        if comparator.value in SPECIAL_OPCODE_NAMES:
                            left = child.left
                            if isinstance(left, ast.Attribute) and left.attr == 'opname':
                                special_opcode_checks.append((child.lineno, comparator.value))
                            elif isinstance(left, ast.Name) and left.id in ('opname', 'instr', 'last', 'last_instr'):
                                special_opcode_checks.append((child.lineno, comparator.value))

            if isinstance(child, ast.Attribute) and child.attr == 'opname':
                parent = getattr(child, '_parent', None)

            if isinstance(child, ast.BoolOp):
                for value in child.values:
                    if isinstance(value, ast.Compare):
                        for comp in value.comparators:
                            if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                                if comp.value in SPECIAL_OPCODE_NAMES:
                                    left = value.left
                                    is_opname_check = False
                                    if isinstance(left, ast.Attribute) and left.attr == 'opname':
                                        is_opname_check = True
                                    elif isinstance(left, ast.Name):
                                        is_opname_check = True

                                    if is_opname_check:
                                        if isinstance(child, ast.BoolOp) and isinstance(child.op, (ast.And, ast.Or)):
                                            special_opcode_checks.append((value.lineno, comp.value))

        for line, opcode in special_opcode_checks:
            report.violations.append(Violation(
                criterion=CRITERION_NAMES[2],
                criterion_id=2,
                line=line,
                detail=f"特殊字节码分支: opname == '{opcode}'"
            ))

    def _check_multiple_generation_paths(
        self,
        node: ast.FunctionDef,
        report: MethodReport,
        generator_methods: List[Tuple[str, str, ast.FunctionDef]],
    ):
        method_name = node.name
        generate_prefixes = ['_generate_', '_try_generate_', '_build_']
        ast_node_types = ['if', 'for', 'while', 'try', 'with', 'match', 'boolop', 'ternary',
                          'assert', 'loop', 'basic']

        for ast_type in ast_node_types:
            matching_methods = []
            for cls_name, _, m_node in generator_methods:
                m_name = m_node.name
                for prefix in generate_prefixes:
                    pattern = f"{prefix}{ast_type}"
                    if m_name == pattern or m_name.startswith(pattern + '_'):
                        matching_methods.append(m_name)
                        break

            if len(matching_methods) > 1 and method_name in matching_methods:
                report.violations.append(Violation(
                    criterion=CRITERION_NAMES[3],
                    criterion_id=3,
                    line=node.lineno,
                    detail=f"AST节点类型 '{ast_type}' 有多个生成方法: {matching_methods}"
                ))

    def _check_cross_responsibility(
        self,
        node: ast.FunctionDef,
        report: MethodReport,
        is_generator: bool,
    ):
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if child.attr in CFG_TRAVERSAL_ATTRS:
                    if is_generator:
                        report.violations.append(Violation(
                            criterion=CRITERION_NAMES[4],
                            criterion_id=4,
                            line=child.lineno,
                            detail=f"生成器方法 '{node.name}' 访问了CFG边遍历属性 '.{child.attr}'"
                        ))

                if child.attr in DOMINATOR_ATTRS:
                    if is_generator:
                        report.violations.append(Violation(
                            criterion=CRITERION_NAMES[4],
                            criterion_id=4,
                            line=child.lineno,
                            detail=f"生成器方法 '{node.name}' 访问了支配树属性 '.{child.attr}'"
                        ))

            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute):
                    if func.attr in ('immediate_dominator', 'dominates',
                                     'post_dominator', 'dominance_frontier',
                                     'find_back_edges', 'find_natural_loops'):
                        if is_generator:
                            report.violations.append(Violation(
                                criterion=CRITERION_NAMES[4],
                                criterion_id=4,
                                line=child.lineno,
                                detail=f"生成器方法 '{node.name}' 调用了分析逻辑 '{func.attr}'"
                            ))

                if isinstance(func, ast.Name):
                    if func.id in ('PatternParser',):
                        if not is_generator:
                            report.violations.append(Violation(
                                criterion=CRITERION_NAMES[4],
                                criterion_id=4,
                                line=child.lineno,
                                detail=f"分析方法 '{node.name}' 使用了生成逻辑 '{func.id}'"
                            ))

            if not is_generator:
                for child2 in ast.walk(node):
                    if isinstance(child2, ast.Dict) or isinstance(child2, ast.List):
                        if hasattr(child2, 'lineno'):
                            pass
                    if isinstance(child2, ast.Call):
                        func = child2.func
                        if isinstance(func, ast.Attribute):
                            if func.attr in ('_generate_region', '_generate_if', '_generate_loop',
                                             '_generate_try', '_generate_with', '_generate_match',
                                             '_generate_boolop', '_generate_ternary',
                                             '_build_statement', '_build_statements',
                                             '_build_boolop_expression', '_build_ternary_value_expr'):
                                report.violations.append(Violation(
                                    criterion=CRITERION_NAMES[4],
                                    criterion_id=4,
                                    line=child2.lineno,
                                    detail=f"分析方法 '{node.name}' 调用了生成逻辑 '{func.attr}'"
                                ))

    def _check_hardcoded_offsets(self, node: ast.FunctionDef, report: MethodReport):
        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                left = child.left
                for op, comparator in zip(child.ops, child.comparators):
                    if self._is_offset_comparison(left, comparator, child):
                        report.violations.append(Violation(
                            criterion=CRITERION_NAMES[5],
                            criterion_id=5,
                            line=child.lineno,
                            detail=f"硬编码偏移比较: {ast.unparse(child)}"
                        ))
                    if self._is_offset_comparison(comparator, left, child):
                        report.violations.append(Violation(
                            criterion=CRITERION_NAMES[5],
                            criterion_id=5,
                            line=child.lineno,
                            detail=f"硬编码偏移比较: {ast.unparse(child)}"
                        ))

            if isinstance(child, ast.Subscript):
                if isinstance(child.slice, ast.Constant) and isinstance(child.slice.value, int):
                    value = child.slice.value
                    if isinstance(child.value, ast.Attribute):
                        if child.value.attr in ('instructions', 'args'):
                            if value > 3:
                                report.violations.append(Violation(
                                    criterion=CRITERION_NAMES[5],
                                    criterion_id=5,
                                    line=child.lineno,
                                    detail=f"硬编码索引访问: ...{child.value.attr}[{value}]"
                                ))

    def _is_offset_comparison(self, offset_side: ast.expr, value_side: ast.expr, parent: ast.Compare) -> bool:
        is_offset_access = False
        if isinstance(offset_side, ast.Attribute):
            if offset_side.attr == 'offset':
                is_offset_access = True
            elif offset_side.attr == 'start_offset':
                is_offset_access = True
        elif isinstance(offset_side, ast.Subscript):
            if isinstance(offset_side.value, ast.Attribute):
                if offset_side.value.attr == 'instructions':
                    is_offset_access = True

        if not is_offset_access:
            return False

        is_hardcoded = False
        if isinstance(value_side, ast.Constant) and isinstance(value_side.value, int):
            is_hardcoded = True
        elif isinstance(value_side, ast.UnaryOp) and isinstance(value_side.op, ast.USub):
            if isinstance(value_side.operand, ast.Constant) and isinstance(value_side.operand.value, int):
                is_hardcoded = True

        return is_hardcoded

    def _check_order_dependency(
        self,
        node: ast.FunctionDef,
        report: MethodReport,
        analyzer_methods: List[Tuple[str, str, ast.FunctionDef]],
    ):
        identify_methods = set()
        for cls_name, _, m_node in analyzer_methods:
            if m_node.name.startswith('_identify_') or m_node.name.startswith('identify_'):
                identify_methods.add(m_node.name)

        called_identify_methods = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute) and func.attr in identify_methods:
                    called_identify_methods.append((child.lineno, func.attr))
                elif isinstance(func, ast.Name) and func.id in identify_methods:
                    called_identify_methods.append((child.lineno, func.id))

        if node.name in identify_methods and called_identify_methods:
            for line, called in called_identify_methods:
                report.violations.append(Violation(
                    criterion=CRITERION_NAMES[6],
                    criterion_id=6,
                    line=line,
                    detail=f"识别方法 '{node.name}' 依赖 '{called}' 的执行结果"
                ))

    def _check_modifying_other_regions(
        self,
        node: ast.FunctionDef,
        report: MethodReport,
        analyzer_creators: Dict[str, str],
        generator_creators: Dict[str, str],
    ):
        if node.name == '__init__':
            return

        all_creators = {**analyzer_creators, **generator_creators}
        current_creates = all_creators.get(node.name)

        region_var_assigns: Dict[str, List[Tuple[int, str]]] = {}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.ctx, ast.Store):
                        attr_name = target.attr
                        if attr_name in REGION_DATA_ATTRS:
                            value_node = target.value
                            var_name = None
                            if isinstance(value_node, ast.Name):
                                var_name = value_node.id
                            elif isinstance(value_node, ast.Attribute):
                                var_name = value_node.attr

                            if var_name:
                                if var_name not in region_var_assigns:
                                    region_var_assigns[var_name] = []
                                region_var_assigns[var_name].append((child.lineno, attr_name))

        region_var_origins: Dict[str, str] = {}
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if isinstance(child.value, ast.Call):
                            func = child.value.func
                            if isinstance(func, ast.Name) and func.id in REGION_SUBCLASS_NAMES:
                                region_var_origins[var_name] = 'self'
                            elif isinstance(func, ast.Attribute) and func.attr in REGION_SUBCLASS_NAMES:
                                region_var_origins[var_name] = 'self'
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id in region_var_origins:
                            if isinstance(child.value, ast.Name) and child.value.id != target.id:
                                region_var_origins[child.value.id] = region_var_origins[target.id]

        for child in ast.walk(node):
            if isinstance(child, ast.For):
                target = child.target
                if isinstance(target, ast.Name):
                    iter_node = child.iter
                    if isinstance(iter_node, ast.Call):
                        func = iter_node.func
                        if isinstance(func, ast.Attribute):
                            if func.attr in ('values', 'items'):
                                region_var_origins[target.id] = 'other_method'

        for var_name, assignments in region_var_assigns.items():
            origin = region_var_origins.get(var_name, 'unknown')
            if origin == 'other_method' or (origin == 'unknown' and var_name not in ('self',)):
                for line, attr_name in assignments:
                    report.violations.append(Violation(
                        criterion=CRITERION_NAMES[7],
                        criterion_id=7,
                        line=line,
                        detail=f"方法 '{node.name}' 修改了其他方法创建的 region 对象的 .{attr_name} 属性 (变量: {var_name})"
                    ))


def format_report(reports: List[MethodReport]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("方法合规性审计报告")
    lines.append("=" * 80)
    lines.append("")

    total_methods = 0
    passing_methods = 0
    failing_methods = 0
    all_violations_by_criterion: Dict[int, int] = {i: 0 for i in range(1, 8)}

    for report in reports:
        if report.method_name.startswith('_') and report.method_name.startswith('__'):
            continue

        total_methods += 1
        if report.passed:
            passing_methods += 1
        else:
            failing_methods += 1

        for v in report.violations:
            all_violations_by_criterion[v.criterion_id] += 1

    lines.append(f"审计方法总数: {total_methods}")
    lines.append(f"通过方法数: {passing_methods}")
    lines.append(f"违规方法数: {failing_methods}")
    lines.append("")

    lines.append("-" * 80)
    lines.append("各准则违规统计:")
    lines.append("-" * 80)
    for i in range(1, 8):
        count = all_violations_by_criterion[i]
        status = "PASS" if count == 0 else f"FAIL ({count}处)"
        lines.append(f"  [{i}] {CRITERION_NAMES[i]}: {status}")
    lines.append("")

    current_file = None
    for report in reports:
        if report.method_name.startswith('__') and report.method_name.endswith('__'):
            if report.method_name != '__init__':
                continue

        if report.file_path != current_file:
            current_file = report.file_path
            lines.append("=" * 80)
            lines.append(f"文件: {os.path.basename(current_file)}")
            lines.append("=" * 80)
            lines.append("")

        status_icon = "[PASS]" if report.passed else "[FAIL]"
        lines.append(f"  {status_icon} {report.class_name}.{report.method_name} "
                      f"(行 {report.start_line}-{report.end_line})")

        scores = report.compliance_scores
        for criterion_name, passed in scores.items():
            icon = "[PASS]" if passed else "[FAIL]"
            lines.append(f"      {icon} {criterion_name}")

        if report.violations:
            lines.append(f"      --- 违规详情 ---")
            for v in report.violations:
                lines.append(f"        行 {v.line}: [{v.criterion_id}] {v.detail}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("合规性总结")
    lines.append("=" * 80)

    all_pass = failing_methods == 0
    if all_pass:
        lines.append("结果: 全部通过 [PASS]")
    else:
        lines.append(f"结果: 存在违规 [FAIL] ({failing_methods}/{total_methods} 方法违规)")

    lines.append("")
    return "\n".join(lines)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    analyzer_path = os.path.join(project_root, "core", "cfg", "region_analyzer.py")
    generator_path = os.path.join(project_root, "core", "cfg", "region_ast_generator.py")

    if not os.path.exists(analyzer_path):
        print(f"错误: 找不到分析器文件: {analyzer_path}", file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(generator_path):
        print(f"错误: 找不到生成器文件: {generator_path}", file=sys.stderr)
        sys.exit(2)

    print(f"审计文件:")
    print(f"  分析器: {analyzer_path}")
    print(f"  生成器: {generator_path}")
    print()

    auditor = PatchAuditor(analyzer_path, generator_path)
    reports = auditor.audit()

    report_text = format_report(reports)

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(report_text)

    has_violations = any(not r.passed for r in reports
                         if not (r.method_name.startswith('__') and r.method_name.endswith('__')
                                 and r.method_name != '__init__'))

    sys.exit(1 if has_violations else 0)


if __name__ == '__main__':
    main()
