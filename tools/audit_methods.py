"""
方法合规性审计脚本

检测 region_analyzer.py 和 region_ast_generator.py 中的补丁特征。
基于7项结构性违规检测，确保代码符合架构约束。

用法: python tools/audit_methods.py
"""

import ast
import re
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple


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
    'BREAK_LOOP', 'CONTINUE_LOOP', 'SETUP_LOOP',
    'POP_BLOCK', 'END_FINALLY', 'WITH_CLEANUP',
    'IMPORT_NAME', 'IMPORT_FROM', 'UNPACK_SEQUENCE',
    'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET', 'BUILD_MAP',
    'POP_TOP', 'COPY', 'SWAP', 'LOAD_CONST',
    'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',
    'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
    'NOP', 'CACHE', 'RESUME', 'PUSH_NULL',
}

CFG_TRAVERSAL_ATTRS = {
    'successors', 'predecessors',
}

DOMINATOR_ATTRS = {
    'dominator', 'dom_analyzer', 'dom_tree', 'immediate_dominator',
    'dominance', 'dom_frontier', 'post_dominator',
}

DOMINATOR_METHODS = {
    'immediate_dominator', 'dominates', 'post_dominator',
    'dominance_frontier', 'find_back_edges', 'find_natural_loops',
}

FORBIDDEN_NAME_PREFIXES = (
    '_fix_', '_merge_', '_patch_', '_fallback_', '_special_case_',
)

FORBIDDEN_NAME_PATTERN = re.compile(r'^_generate_\w+_from_block$')

REGION_TYPE_KEYWORDS = [
    'if', 'for', 'while', 'try', 'with', 'match', 'boolop', 'ternary',
    'assert', 'loop', 'basic',
]

GENERATE_PREFIXES = ['_generate_', '_try_generate_', '_build_']


@dataclass
class Violation:
    file_name: str
    method_name: str
    line: int
    violation_type: str
    description: str


class MethodCollector(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.methods: List[Tuple[str, str, ast.FunctionDef]] = []
        self._current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._current_class:
            self.methods.append((self._current_class, node.name, node))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if self._current_class:
            self.methods.append((self._current_class, node.name, node))
        self.generic_visit(node)


class MethodAuditor:
    def __init__(self, analyzer_path: str, generator_path: str):
        self.analyzer_path = analyzer_path
        self.generator_path = generator_path
        self.analyzer_tree = self._parse_file(analyzer_path)
        self.generator_tree = self._parse_file(generator_path)
        self.analyzer_methods = self._collect_methods(analyzer_path, self.analyzer_tree)
        self.generator_methods = self._collect_methods(generator_path, self.generator_tree)
        self.analyzer_creators = self._find_region_creators(self.analyzer_methods)
        self.generator_creators = self._find_region_creators(self.generator_methods)
        self.all_creators = {**self.analyzer_creators, **self.generator_creators}

    def _parse_file(self, path: str) -> ast.Module:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        return ast.parse(source, filename=path)

    def _collect_methods(self, file_path: str, tree: ast.Module) -> List[Tuple[str, str, ast.FunctionDef]]:
        collector = MethodCollector(file_path)
        collector.visit(tree)
        return collector.methods

    def _find_region_creators(self, methods: List[Tuple[str, str, ast.FunctionDef]]) -> Dict[str, str]:
        creator_map = {}
        for cls_name, method_name, node in methods:
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Name) and func.id in REGION_SUBCLASS_NAMES:
                        creator_map[method_name] = func.id
                        break
                    if (isinstance(func, ast.Attribute) and func.attr in REGION_SUBCLASS_NAMES):
                        creator_map[method_name] = func.attr
                        break
        return creator_map

    def audit(self) -> List[Violation]:
        violations: List[Violation] = []

        for cls_name, method_name, node in self.analyzer_methods:
            file_name = os.path.basename(self.analyzer_path)
            violations.extend(self._check_post_processing(file_name, cls_name, method_name, node))
            violations.extend(self._check_special_case_branches(file_name, cls_name, method_name, node))
            violations.extend(self._check_multiple_generation_paths(file_name, cls_name, method_name, node, self.generator_methods))
            violations.extend(self._check_cross_responsibility(file_name, cls_name, method_name, node, is_generator=False))
            violations.extend(self._check_hardcoded_offsets(file_name, cls_name, method_name, node))
            violations.extend(self._check_forbidden_method_names(file_name, cls_name, method_name, node))
            violations.extend(self._check_order_dependency(file_name, cls_name, method_name, node, self.analyzer_methods))

        for cls_name, method_name, node in self.generator_methods:
            file_name = os.path.basename(self.generator_path)
            violations.extend(self._check_post_processing(file_name, cls_name, method_name, node))
            violations.extend(self._check_special_case_branches(file_name, cls_name, method_name, node))
            violations.extend(self._check_multiple_generation_paths(file_name, cls_name, method_name, node, self.generator_methods))
            violations.extend(self._check_cross_responsibility(file_name, cls_name, method_name, node, is_generator=True))
            violations.extend(self._check_hardcoded_offsets(file_name, cls_name, method_name, node))
            violations.extend(self._check_forbidden_method_names(file_name, cls_name, method_name, node))
            violations.extend(self._check_order_dependency(file_name, cls_name, method_name, node, self.analyzer_methods))

        violations.sort(key=lambda v: (v.file_name, v.line))
        return violations

    def _check_post_processing(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef
    ) -> List[Violation]:
        violations = []
        if method_name == '__init__':
            return violations

        is_creator = method_name in self.all_creators

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and isinstance(child.ctx, ast.Store):
                attr_name = child.attr
                if attr_name not in REGION_DATA_ATTRS:
                    continue
                value = child.value
                is_region_obj = False
                if isinstance(value, ast.Name):
                    if value.id in REGION_SUBCLASS_NAMES or value.id in (
                        'region', 'r', 'loop_region', 'if_region',
                        'try_region', 'with_region', 'match_region',
                        'boolop_region', 'ternary_region', 'assert_region',
                    ):
                        is_region_obj = True
                elif isinstance(value, ast.Attribute):
                    if value.attr in REGION_SUBCLASS_NAMES or value.attr in ('region', 'r'):
                        is_region_obj = True

                if is_region_obj and not is_creator:
                    violations.append(Violation(
                        file_name=file_name,
                        method_name=f"{cls_name}.{method_name}",
                        line=child.lineno,
                        violation_type="后处理修正",
                        description=f"方法 '{method_name}' 对已创建的Region对象执行属性赋值 region.{attr_name}，但不是该Region的创建者(__init__阶段之外)",
                    ))

        return violations

    def _check_special_case_branches(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef
    ) -> List[Violation]:
        violations = []
        seen = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                left = child.left
                for comparator in child.comparators:
                    if not (isinstance(comparator, ast.Constant) and isinstance(comparator.value, str)):
                        continue
                    opcode_str = comparator.value
                    if opcode_str not in SPECIAL_OPCODE_NAMES:
                        continue

                    is_opname_check = False
                    if isinstance(left, ast.Attribute) and left.attr == 'opname':
                        is_opname_check = True
                    elif isinstance(left, ast.Name) and left.id in ('opname', 'instr', 'last', 'last_instr'):
                        is_opname_check = True

                    if is_opname_check:
                        key = (child.lineno, opcode_str)
                        if key not in seen:
                            seen.add(key)
                            violations.append(Violation(
                                file_name=file_name,
                                method_name=f"{cls_name}.{method_name}",
                                line=child.lineno,
                                violation_type="特殊情况分支",
                                description=f"分支条件包含具体指令名比较: instr.opname == '{opcode_str}'",
                            ))

            if isinstance(child, ast.BoolOp):
                for value in child.values:
                    if not isinstance(value, ast.Compare):
                        continue
                    for comp in value.comparators:
                        if not (isinstance(comp, ast.Constant) and isinstance(comp.value, str)):
                            continue
                        opcode_str = comp.value
                        if opcode_str not in SPECIAL_OPCODE_NAMES:
                            continue
                        left = value.left
                        is_opname_check = False
                        if isinstance(left, ast.Attribute) and left.attr == 'opname':
                            is_opname_check = True
                        elif isinstance(left, ast.Name):
                            is_opname_check = True
                        if is_opname_check:
                            key = (value.lineno, opcode_str)
                            if key not in seen:
                                seen.add(key)
                                violations.append(Violation(
                                    file_name=file_name,
                                    method_name=f"{cls_name}.{method_name}",
                                    line=value.lineno,
                                    violation_type="特殊情况分支",
                                    description=f"分支条件包含具体指令名比较: opname == '{opcode_str}'",
                                ))

        return violations

    def _check_multiple_generation_paths(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef,
        generator_methods: List[Tuple[str, str, ast.FunctionDef]],
    ) -> List[Violation]:
        violations = []

        for region_type_kw in REGION_TYPE_KEYWORDS:
            matching_methods = []
            for g_cls, g_name, g_node in generator_methods:
                for prefix in GENERATE_PREFIXES:
                    pattern = f"{prefix}{region_type_kw}"
                    if g_name == pattern or g_name.startswith(pattern + '_'):
                        matching_methods.append(g_name)
                        break

            if len(matching_methods) > 1 and method_name in matching_methods:
                violations.append(Violation(
                    file_name=file_name,
                    method_name=f"{cls_name}.{method_name}",
                    line=node.lineno,
                    violation_type="多种生成路径",
                    description=f"区域类型 '{region_type_kw}' 存在多个生成方法入口: {matching_methods}",
                ))

        return violations

    def _check_cross_responsibility(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef,
        is_generator: bool,
    ) -> List[Violation]:
        violations = []
        if not is_generator:
            return violations

        seen = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if child.attr in CFG_TRAVERSAL_ATTRS:
                    key = (child.lineno, f"cfg_edge.{child.attr}")
                    if key not in seen:
                        seen.add(key)
                        violations.append(Violation(
                            file_name=file_name,
                            method_name=f"{cls_name}.{method_name}",
                            line=child.lineno,
                            violation_type="跨职责修改",
                            description=f"生成器方法 '{method_name}' 访问了CFG边遍历属性 '.{child.attr}'",
                        ))

                if child.attr in DOMINATOR_ATTRS:
                    key = (child.lineno, f"dom.{child.attr}")
                    if key not in seen:
                        seen.add(key)
                        violations.append(Violation(
                            file_name=file_name,
                            method_name=f"{cls_name}.{method_name}",
                            line=child.lineno,
                            violation_type="跨职责修改",
                            description=f"生成器方法 '{method_name}' 访问了支配树属性 '.{child.attr}'",
                        ))

            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute):
                    if func.attr in DOMINATOR_METHODS:
                        key = (child.lineno, f"call.{func.attr}")
                        if key not in seen:
                            seen.add(key)
                            violations.append(Violation(
                                file_name=file_name,
                                method_name=f"{cls_name}.{method_name}",
                                line=child.lineno,
                                violation_type="跨职责修改",
                                description=f"生成器方法 '{method_name}' 调用了支配树/CFG分析方法 '{func.attr}()'",
                            ))

        return violations

    def _check_hardcoded_offsets(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef
    ) -> List[Violation]:
        violations = []
        seen = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Compare):
                left = child.left
                for op, comparator in zip(child.ops, child.comparators):
                    if self._is_offset_vs_constant(left, comparator):
                        key = child.lineno
                        if key not in seen:
                            seen.add(key)
                            violations.append(Violation(
                                file_name=file_name,
                                method_name=f"{cls_name}.{method_name}",
                                line=child.lineno,
                                violation_type="硬编码偏移",
                                description=f"代码中存在数字常量与块偏移的比较: {ast.unparse(child)}",
                            ))
                    if self._is_offset_vs_constant(comparator, left):
                        key = child.lineno
                        if key not in seen:
                            seen.add(key)
                            violations.append(Violation(
                                file_name=file_name,
                                method_name=f"{cls_name}.{method_name}",
                                line=child.lineno,
                                violation_type="硬编码偏移",
                                description=f"代码中存在数字常量与块偏移的比较: {ast.unparse(child)}",
                            ))

            if isinstance(child, ast.Subscript):
                if isinstance(child.slice, ast.Constant) and isinstance(child.slice.value, int):
                    idx_val = child.slice.value
                    if isinstance(child.value, ast.Attribute):
                        if child.value.attr in ('instructions', 'args') and idx_val > 3:
                            key = child.lineno
                            if key not in seen:
                                seen.add(key)
                                violations.append(Violation(
                                    file_name=file_name,
                                    method_name=f"{cls_name}.{method_name}",
                                    line=child.lineno,
                                    violation_type="硬编码偏移",
                                    description=f"硬编码索引访问: ...{child.value.attr}[{idx_val}]",
                                ))

        return violations

    def _is_offset_vs_constant(self, offset_side: ast.expr, value_side: ast.expr) -> bool:
        is_offset = False
        if isinstance(offset_side, ast.Attribute):
            if offset_side.attr in ('offset', 'start_offset', 'end_offset'):
                is_offset = True
        elif isinstance(offset_side, ast.Subscript):
            if isinstance(offset_side.value, ast.Attribute):
                if offset_side.value.attr == 'instructions':
                    is_offset = True

        if not is_offset:
            return False

        if isinstance(value_side, ast.Constant) and isinstance(value_side.value, int):
            return True
        if isinstance(value_side, ast.UnaryOp) and isinstance(value_side.op, ast.USub):
            if isinstance(value_side.operand, ast.Constant) and isinstance(value_side.operand.value, int):
                return True
        return False

    def _check_forbidden_method_names(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef
    ) -> List[Violation]:
        violations = []

        for prefix in FORBIDDEN_NAME_PREFIXES:
            if method_name.startswith(prefix):
                violations.append(Violation(
                    file_name=file_name,
                    method_name=f"{cls_name}.{method_name}",
                    line=node.lineno,
                    violation_type="禁止方法名",
                    description=f"方法名 '{method_name}' 使用了禁止的前缀 '{prefix}'，表明此方法为补丁式修正",
                ))

        if FORBIDDEN_NAME_PATTERN.match(method_name):
            violations.append(Violation(
                file_name=file_name,
                method_name=f"{cls_name}.{method_name}",
                line=node.lineno,
                violation_type="禁止方法名",
                description=f"方法名 '{method_name}' 匹配禁止模式 '_generate_*_from_block'，表明此方法绕过了区域抽象",
            ))

        return violations

    def _check_order_dependency(
        self, file_name: str, cls_name: str, method_name: str, node: ast.FunctionDef,
        analyzer_methods: List[Tuple[str, str, ast.FunctionDef]],
    ) -> List[Violation]:
        violations = []

        identify_methods = set()
        for a_cls, a_name, a_node in analyzer_methods:
            if a_name.startswith('_identify_') or a_name.startswith('identify_'):
                identify_methods.add(a_name)

        if method_name not in identify_methods:
            return violations

        called_identify = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                called_name = None
                if isinstance(func, ast.Attribute) and func.attr in identify_methods:
                    called_name = func.attr
                elif isinstance(func, ast.Name) and func.id in identify_methods:
                    called_name = func.id
                if called_name and called_name != method_name:
                    called_identify.append((child.lineno, called_name))

        for line, called in called_identify:
            violations.append(Violation(
                file_name=file_name,
                method_name=f"{cls_name}.{method_name}",
                line=line,
                violation_type="顺序依赖",
                description=f"识别方法 '{method_name}' 依赖 '{called}' 的执行结果，步骤执行顺序影响结果",
            ))

        return violations


VIOLATION_TYPE_ORDER = [
    "后处理修正",
    "特殊情况分支",
    "多种生成路径",
    "跨职责修改",
    "硬编码偏移",
    "禁止方法名",
    "顺序依赖",
]


def format_violations(violations: List[Violation]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("方法合规性审计报告")
    lines.append("=" * 80)
    lines.append("")

    if not violations:
        lines.append("未检测到违规项。")
        lines.append("")
        lines.append("=" * 80)
        lines.append("合规性总结")
        lines.append("=" * 80)
        lines.append("总违规数: 0")
        lines.append("结果: 全部通过 [PASS]")
        return "\n".join(lines)

    lines.append("-" * 80)
    lines.append("违规详情:")
    lines.append("-" * 80)
    lines.append("")

    for i, v in enumerate(violations, 1):
        lines.append(f"  [{i}] 文件: {v.file_name}")
        lines.append(f"      方法: {v.method_name}")
        lines.append(f"      行号: {v.line}")
        lines.append(f"      违规类型: {v.violation_type}")
        lines.append(f"      违规描述: {v.description}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("合规性总结")
    lines.append("=" * 80)
    lines.append(f"总违规数: {len(violations)}")
    lines.append("")

    lines.append("按违规类型分类统计:")
    type_counts: Dict[str, int] = {t: 0 for t in VIOLATION_TYPE_ORDER}
    for v in violations:
        if v.violation_type in type_counts:
            type_counts[v.violation_type] += 1

    for vtype in VIOLATION_TYPE_ORDER:
        count = type_counts[vtype]
        status = "PASS" if count == 0 else f"FAIL ({count}处)"
        lines.append(f"  {vtype}: {status}")

    lines.append("")
    lines.append(f"结果: 存在违规 [FAIL]")
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

    auditor = MethodAuditor(analyzer_path, generator_path)
    violations = auditor.audit()

    report_text = format_violations(violations)

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(report_text)

    sys.exit(1 if violations else 0)


if __name__ == '__main__':
    main()
