"""
方法合规性审计脚本 (Method Compliance Audit)

检测 region_analyzer.py 和 region_ast_generator.py 中的补丁驱动开发模式。
基于 AST 结构分析（非文本模式匹配），按方法维度组织审计结果。

六类检测规则：
  P1  后处理修正   — 在区域创建后修改其属性（如 region.try_blocks = ...）
  P2  特殊情况分支 — if/elif 条件中硬编码特定字节码指令名
  P3  多路径生成   — 同一区域类型存在多个 _generate_* 入口
  P4  跨职责逻辑   — 分析器中混入生成逻辑，或生成器中混入分析逻辑
  P5  硬编码偏移   — 依赖特定偏移数值（如 gap <= 8）
  P6  顺序依赖     — 方法间通过 self 属性形成隐式执行顺序依赖

使用方式:
    python -m core.cfg.patch_detector
    python core/cfg/patch_detector.py [文件路径...]
    python core/cfg/patch_detector.py -v
    python core/cfg/patch_detector.py --json
"""

import ast
import sys
import os
import json
import argparse
from typing import List, Dict, Set, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Violation:
    """单条违规记录"""
    rule_id: str
    rule_name: str
    line: int
    col: int
    snippet: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MethodAudit:
    """单个方法的审计结果"""
    method_name: str
    class_name: str
    start_line: int
    end_line: int
    violations: List[Violation] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return len(self.violations) == 0

    @property
    def violated_rules(self) -> Set[str]:
        return {v.rule_id for v in self.violations}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'method_name': self.method_name,
            'class_name': self.class_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'is_compliant': self.is_compliant,
            'violated_rules': sorted(self.violated_rules),
            'violations': [v.to_dict() for v in self.violations],
        }


@dataclass
class FileAudit:
    """单个文件的审计结果"""
    filepath: str
    method_audits: List[MethodAudit] = field(default_factory=list)

    @property
    def compliant_methods(self) -> List[MethodAudit]:
        return [m for m in self.method_audits if m.is_compliant]

    @property
    def violating_methods(self) -> List[MethodAudit]:
        return [m for m in self.method_audits if not m.is_compliant]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'filepath': self.filepath,
            'compliant_count': len(self.compliant_methods),
            'violating_count': len(self.violating_methods),
            'methods': [m.to_dict() for m in self.method_audits],
        }


# ============================================================
# 常量定义
# ============================================================

# 已知的区域可变属性（创建后不应被外部方法修改）
REGION_MUTABLE_ATTRS = frozenset({
    'try_blocks', 'blocks', 'entry', 'body_blocks', 'else_blocks',
    'condition_block', 'handler_entry_blocks',
    'finally_blocks', 'cleanup_blocks', 'has_else', 'has_finally',
    'finally_copy_blocks', 'except_handlers',
    'chained_compare_blocks', 'chained_compare_ops',
    'chained_left_instr', 'chained_comparator_instrs',
    'header_block', 'back_edge_block', 'is_while_true', 'is_async',
    'init_blocks', 'pre_condition_blocks',
    'then_blocks', 'merge_block',
    'elif_conditions', 'elif_bodies', 'elif_final_else',
    'with_blocks', 'exception_blocks', 'resource_expr', 'target', 'items',
    'subject_block', 'case_blocks', 'case_patterns', 'case_guards', 'case_bodies',
    'op_chain', 'value_target', 'prefix_block', 'prefix_op_type', 'body_block',
    'condition_expr', 'true_value_block', 'false_value_block',
    'condition_chain_blocks', 'container_type', 'func_call_info',
    'parent', 'children', 'region_type',
})

# 已知的Python字节码操作码名称
BYTECODE_OPNAMES = frozenset({
    'BEFORE_WITH', 'BEFORE_ASYNC_WITH', 'WITH_EXCEPT_START',
    'END_ASYNC_FOR', 'FOR_ITER', 'GET_ITER', 'GET_AITER',
    'SEND', 'YIELD_VALUE', 'RETURN_VALUE', 'RETURN_CONST',
    'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
    'JUMP_BACKWARD_NO_INTERRUPT',
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
    'COMPARE_OP', 'CALL', 'LOAD_CONST', 'LOAD_FAST',
    'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
    'BUILD_LIST', 'BUILD_DICT', 'BUILD_SET', 'BUILD_TUPLE',
    'BUILD_STRING', 'UNPACK_SEQUENCE',
    'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
    'MATCH_KEYS', 'MATCH_MAPPING_KEYS', 'GET_LEN', 'GET_AWAITABLE',
    'RERAISE', 'RAISE_VARARGS', 'SETUP_FINALLY',
    'POP_BLOCK', 'POP_TOP', 'DUP_TOP', 'ROT_TWO', 'ROT_THREE',
    'SWAP', 'COPY', 'NOP', 'RESUME', 'CACHE',
    'PUSH_NULL', 'PRECALL', 'CALL_FUNCTION', 'CALL_METHOD',
    'LIST_APPEND', 'DICT_UPDATE', 'SET_ADD', 'TUPLE_APPEND',
    'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
    'LOAD_ATTR', 'STORE_ATTR', 'DELETE_ATTR',
    'LOAD_SUBSCR', 'STORE_SUBSCR', 'DELETE_SUBSCR',
    'BINARY_OP', 'BINARY_SUBSCR',
    'IS_OP', 'CONTAINS_OP', 'FORMAT_VALUE', 'BUILD_SLICE',
    'EXTENDED_ARG', 'END_FOR', 'END_SEND',
    'MAKE_FUNCTION', 'LOAD_CLOSURE', 'LOAD_DEREF',
    'STORE_DEREF', 'DELETE_DEREF',
    'PRINT_EXPR', 'LIST_TO_TUPLE',
    'PUSH_EXC_INFO', 'POP_EXCEPT',
    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
    'LOAD_GLOBAL', 'LOAD_NAME', 'DELETE_FAST', 'DELETE_NAME',
    'LOAD_ASSERTION_ERROR', 'LOAD_BUILD_CLASS',
    'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
    'GET_ITER_STACK', 'ASYNC_GEN_WRAP',
    'GEN_START', 'CACHE_START_ENTRY',
})

# 区域类型关键词（用于P3分组）
REGION_TYPE_KEYWORDS: Dict[str, List[str]] = {
    'with': ['with'],
    'if': ['if', 'branch', 'cond'],
    'loop': ['loop', 'for', 'while'],
    'try': ['try', 'except', 'finally', 'handler'],
    'match': ['match'],
    'boolop': ['boolop', 'bool_op'],
    'ternary': ['ternary'],
    'basic': ['basic'],
    'return': ['return'],
}

# AST节点类型名称集合（用于P4检测）
AST_NODE_TYPE_NAMES = frozenset({
    'If', 'For', 'While', 'With', 'Try', 'Match',
    'FunctionDef', 'ClassDef', 'Return', 'Assign',
    'AugAssign', 'AnnAssign', 'Expr', 'Pass',
    'Import', 'ImportFrom', 'Global', 'Nonlocal',
    'Assert', 'Delete', 'Raise', 'Break', 'Continue',
    'AsyncFunctionDef', 'AsyncFor', 'AsyncWith', 'Await',
    'BoolOp', 'BinOp', 'UnaryOp', 'Compare',
    'Call', 'Attribute', 'Subscript', 'Name',
    'Constant', 'List', 'Dict', 'Set', 'Tuple',
    'IfExp', 'Lambda', 'Yield', 'YieldFrom',
    'FormattedValue', 'JoinedStr', 'Starred',
    'TryStar', 'Slice', 'Subscript',
})

# 规则名称映射
RULE_NAMES = {
    'P1': '后处理修正',
    'P2': '特殊情况分支',
    'P3': '多路径生成',
    'P4': '跨职责逻辑',
    'P5': '硬编码偏移',
    'P6': '顺序依赖',
}


# ============================================================
# 辅助函数
# ============================================================

def get_source_segment(source_lines: List[str], lineno: int,
                       end_lineno: int = None) -> str:
    """获取源代码片段"""
    if end_lineno is None:
        end_lineno = lineno
    start = max(0, lineno - 1)
    end = min(len(source_lines), end_lineno)
    lines = source_lines[start:end]
    return ''.join(lines).strip()


def is_self_attr(node: ast.AST, attr_name: str = None) -> bool:
    """检查节点是否为 self.XXX 形式的属性访问"""
    if not isinstance(node, ast.Attribute):
        return False
    if not isinstance(node.value, ast.Name) or node.value.id != 'self':
        return False
    if attr_name is not None and node.attr != attr_name:
        return False
    return True


def is_self_attr_call(node: ast.AST, obj_attr: str, method_attr: str) -> bool:
    """检查节点是否为 self.XXX.yyy() 形式的方法调用"""
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != method_attr:
        return False
    return is_self_attr(node.func.value, obj_attr)


# ============================================================
# P1: 后处理修正检测器
# ============================================================

class P1Detector:
    """
    P1: 后处理修正检测

    在主方法（analyze/generate）中检测对已创建区域属性的赋值修改。
    核心AST模式：ast.Assign(target=ast.Attribute(attr=区域属性), ...)
    其中被修改的对象不是当前方法创建的区域。
    """

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST) -> List[Violation]:
        violations = []
        method_name = method_node.name

        is_main = method_name in ('analyze', 'generate', 'run', 'main')
        is_identify = method_name.startswith('_identify_')
        is_generate = method_name.startswith('_generate_')

        if not (is_main or is_identify or is_generate):
            return violations

        for node in ast.walk(method_node):
            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:
                if not isinstance(target, ast.Attribute):
                    continue
                if not isinstance(target.ctx, ast.Store):
                    continue

                attr_name = target.attr
                if attr_name not in REGION_MUTABLE_ATTRS:
                    continue

                # 获取被赋值对象的变量名
                value_node = target.value
                var_name = self._get_var_name(value_node)

                if is_main:
                    # 主方法中对区域属性的赋值都是后处理修正
                    snippet = get_source_segment(
                        source_lines, node.lineno, node.end_lineno)
                    violations.append(Violation(
                        rule_id="P1", rule_name="后处理修正",
                        line=node.lineno, col=node.col_offset,
                        snippet=snippet[:150],
                        detail=f"在主方法 '{method_name}'() 中修改区域属性 "
                               f"'{var_name}.{attr_name}'，"
                               f"该区域已由识别方法创建",
                    ))
                elif is_identify:
                    # 识别方法中修改非本方法创建的区域属性
                    if var_name and not self._is_local_region_var(
                            var_name, method_node):
                        snippet = get_source_segment(
                            source_lines, node.lineno, node.end_lineno)
                        violations.append(Violation(
                            rule_id="P1", rule_name="后处理修正",
                            line=node.lineno, col=node.col_offset,
                            snippet=snippet[:150],
                            detail=f"在识别方法 '{method_name}'() 中修改外部区域 "
                                   f"'{var_name}.{attr_name}'",
                        ))

        return violations

    def _get_var_name(self, node: ast.AST) -> str:
        """从属性访问的value中提取变量名"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "?"

    def _is_local_region_var(self, var_name: str,
                             method_node: ast.FunctionDef) -> bool:
        """检查变量是否是当前方法内创建的区域对象"""
        for node in ast.walk(method_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        # 检查右侧是否是区域构造调用
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name):
                                if 'Region' in node.value.func.id:
                                    return True
                        return False
        return False


# ============================================================
# P2: 特殊情况分支检测器
# ============================================================

class P2Detector:
    """
    P2: 特殊情况分支检测

    检测 if/elif 条件中硬编码特定字节码指令名的分支。
    核心AST模式：
      - ast.Compare(left=ast.Attribute(attr='opname'), comparators=[字符串常量])
      - 与变量引用的类别集合（如 FORWARD_JUMP_OPS）区分开
    """

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST) -> List[Violation]:
        violations = []
        method_name = method_node.name

        is_relevant = (method_name.startswith('_identify_') or
                       method_name.startswith('_generate_') or
                       method_name in ('analyze', 'generate') or
                       method_name.startswith('_build_') or
                       method_name.startswith('_create_') or
                       method_name.startswith('_collect_'))

        if not is_relevant:
            return violations

        for node in ast.walk(method_node):
            if not isinstance(node, ast.If):
                continue

            opname_checks = self._find_opname_checks(node.test)
            if opname_checks:
                snippet = get_source_segment(
                    source_lines,
                    node.test.lineno,
                    node.test.end_lineno)
                opnames_str = ', '.join(sorted(opname_checks)[:6])
                if len(opname_checks) > 6:
                    opnames_str += '...'
                violations.append(Violation(
                    rule_id="P2", rule_name="特殊情况分支",
                    line=node.test.lineno, col=node.test.col_offset,
                    snippet=snippet[:150],
                    detail=f"条件分支硬编码字节码指令名: {opnames_str}",
                ))

        return violations

    def _find_opname_checks(self, test_node: ast.AST) -> Set[str]:
        """在条件表达式中查找对 .opname 的硬编码字符串比较"""
        found = set()

        for node in ast.walk(test_node):
            if not isinstance(node, ast.Compare):
                continue

            left = node.left
            if not (isinstance(left, ast.Attribute) and left.attr == 'opname'):
                continue

            for comparator in node.comparators:
                found.update(self._extract_opname_strings(comparator))

            # 也检查 any() 生成器表达式中的 opname 检查
            if isinstance(node, ast.Call):
                found.update(self._check_any_genexp(node))

        # 额外检查 any() 调用
        for node in ast.walk(test_node):
            if isinstance(node, ast.Call):
                found.update(self._check_any_genexp(node))

        return found

    def _extract_opname_strings(self, node: ast.AST) -> Set[str]:
        """从比较对象中提取字节码操作码字符串常量（非变量引用）"""
        opnames = set()

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in BYTECODE_OPNAMES:
                opnames.add(node.value)

        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    if elt.value in BYTECODE_OPNAMES:
                        opnames.add(elt.value)

        return opnames

    def _check_any_genexp(self, call_node: ast.Call) -> Set[str]:
        """检查 any() 生成器表达式中的 opname 检查"""
        found = set()

        if not (isinstance(call_node.func, ast.Name) and
                call_node.func.id == 'any'):
            return found

        for arg in call_node.args:
            if not isinstance(arg, ast.GeneratorExp):
                continue
            for node in ast.walk(arg):
                if isinstance(node, ast.Compare):
                    left = node.left
                    if isinstance(left, ast.Attribute) and left.attr == 'opname':
                        for comp in node.comparators:
                            found.update(self._extract_opname_strings(comp))

        return found


# ============================================================
# P3: 多路径生成检测器
# ============================================================

class P3Detector:
    """
    P3: 多路径生成检测

    检测同一区域类型是否有多个 _generate_* 入口方法。
    例如 _generate_with 和 _generate_with_impl 同时存在。
    """

    def __init__(self):
        self._reported_types: Set[str] = set()

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST,
               generate_groups: Dict[str, List[ast.FunctionDef]]
               ) -> List[Violation]:
        violations = []
        method_name = method_node.name

        if not method_name.startswith('_generate_'):
            return violations

        region_type = self._classify_region_type(method_name)
        if region_type is None:
            return violations

        same_type_methods = generate_groups.get(region_type, [])
        if len(same_type_methods) < 2:
            return violations

        # 每种区域类型只报告一次
        if region_type in self._reported_types:
            return violations
        self._reported_types.add(region_type)

        method_names = sorted(m.name for m in same_type_methods)
        lines = [m.lineno for m in same_type_methods]

        violations.append(Violation(
            rule_id="P3", rule_name="多路径生成",
            line=min(lines), col=0,
            snippet=', '.join(method_names),
            detail=f"区域类型 '{region_type}' 存在 {len(same_type_methods)} 个生成入口: "
                   f"{', '.join(method_names)}",
        ))

        return violations

    def _classify_region_type(self, method_name: str) -> Optional[str]:
        """根据方法名分类区域类型"""
        name_lower = method_name.lower()
        for region_type, keywords in REGION_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in name_lower:
                    return region_type
        return None

    def reset(self):
        """重置已报告类型集合（新文件扫描时调用）"""
        self._reported_types.clear()


# ============================================================
# P4: 跨职责逻辑检测器
# ============================================================

class P4Detector:
    """
    P4: 跨职责逻辑检测

    在分析器中检测生成逻辑（AST节点构建、pattern解析）。
    在生成器中检测分析逻辑（CFG遍历、支配树查询、区域分析器访问）。
    """

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST,
               filepath: str) -> List[Violation]:
        filename = os.path.basename(filepath).lower()

        if 'region_analyzer' in filename:
            return self._detect_in_analyzer(
                method_node, source_lines)
        elif 'region_ast_generator' in filename:
            return self._detect_in_generator(
                method_node, source_lines)
        return []

    def _detect_in_analyzer(self, method_node: ast.FunctionDef,
                            source_lines: List[str]) -> List[Violation]:
        """在分析器中检测生成逻辑"""
        violations = []
        method_name = method_node.name

        # 检测 dict 构建模拟 AST 节点: {'type': 'If', ...}
        for node in ast.walk(method_node):
            if not isinstance(node, ast.Dict):
                continue

            for key, value in zip(node.keys, node.values):
                if key is None:
                    continue
                if not (isinstance(key, ast.Constant) and
                        isinstance(key.value, str) and key.value == 'type'):
                    continue
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    if value.value in AST_NODE_TYPE_NAMES:
                        snippet = get_source_segment(
                            source_lines, node.lineno, node.end_lineno)
                        violations.append(Violation(
                            rule_id="P4", rule_name="跨职责逻辑",
                            line=node.lineno, col=node.col_offset,
                            snippet=snippet[:150],
                            detail=f"在分析器中发现 AST 节点构建代码: "
                                   f"type='{value.value}'",
                        ))

        # 检测 self.pattern_parser 的方法调用
        for node in ast.walk(method_node):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue

            func = node.func
            if is_self_attr(func.value, 'pattern_parser'):
                snippet = get_source_segment(
                    source_lines, node.lineno, node.end_lineno)
                violations.append(Violation(
                    rule_id="P4", rule_name="跨职责逻辑",
                    line=node.lineno, col=node.col_offset,
                    snippet=snippet[:150],
                    detail=f"在分析器中发现 pattern 解析调用: "
                           f"self.pattern_parser.{func.attr}()",
                ))

        return violations

    def _detect_in_generator(self, method_node: ast.FunctionDef,
                             source_lines: List[str]) -> List[Violation]:
        """在生成器中检测分析逻辑"""
        violations = []
        method_name = method_node.name

        # 按类型聚合，避免同一方法中重复报告同类违规
        cfg_block_accesses: List[int] = []
        cfg_offset_lookups: List[int] = []
        analyzer_accesses: List[Tuple[int, str]] = []

        for node in ast.walk(method_node):
            # 检测 self.cfg.blocks / self.cfg.entry_block / self.cfg.name
            if isinstance(node, ast.Attribute):
                if is_self_attr(node.value, 'cfg'):
                    if node.attr in ('blocks', 'entry_block'):
                        cfg_block_accesses.append(node.lineno)

            # 检测 self.cfg.get_block_by_offset() 调用
            if isinstance(node, ast.Call):
                if is_self_attr_call(node, 'cfg', 'get_block_by_offset'):
                    cfg_offset_lookups.append(node.lineno)

                # 检测 self.region_analyzer.XXX() 调用
                if isinstance(node.func, ast.Attribute):
                    if is_self_attr(node.func.value, 'region_analyzer'):
                        analyzer_accesses.append(
                            (node.lineno, node.func.attr))

        # 报告聚合结果
        if cfg_block_accesses:
            first_line = min(cfg_block_accesses)
            snippet = get_source_segment(source_lines, first_line)
            violations.append(Violation(
                rule_id="P4", rule_name="跨职责逻辑",
                line=first_line, col=0,
                snippet=snippet[:150],
                detail=f"在生成器中发现 CFG 直接访问 (self.cfg.blocks/entry_block)，"
                       f"共 {len(cfg_block_accesses)} 处",
            ))

        if cfg_offset_lookups:
            first_line = min(cfg_offset_lookups)
            snippet = get_source_segment(source_lines, first_line)
            violations.append(Violation(
                rule_id="P4", rule_name="跨职责逻辑",
                line=first_line, col=0,
                snippet=snippet[:150],
                detail=f"在生成器中发现 CFG 偏移查询 "
                       f"(self.cfg.get_block_by_offset)，"
                       f"共 {len(cfg_offset_lookups)} 处",
            ))

        if analyzer_accesses:
            first_line = min(a[0] for a in analyzer_accesses)
            attrs = sorted(set(a[1] for a in analyzer_accesses))
            snippet = get_source_segment(source_lines, first_line)
            violations.append(Violation(
                rule_id="P4", rule_name="跨职责逻辑",
                line=first_line, col=0,
                snippet=snippet[:150],
                detail=f"在生成器中发现分析器访问 "
                       f"(self.region_analyzer.{', .'.join(attrs)})，"
                       f"共 {len(analyzer_accesses)} 处",
            ))

        return violations


# ============================================================
# P5: 硬编码偏移检测器
# ============================================================

class P5Detector:
    """
    P5: 硬编码偏移检测

    检测依赖特定偏移数值的代码，如 gap <= 8, gap < 16 等。
    核心AST模式：ast.Compare 中同时出现偏移相关变量和数值常量。
    """

    OFFSET_VAR_NAMES = frozenset({
        'gap', 'offset', 'start_offset', 'end_offset',
        'try_start', 'try_end', 'handler_start',
        'body_offset_start', 'body_offset_end',
    })

    OFFSET_ATTR_NAMES = frozenset({
        'start_offset', 'end_offset', 'offset',
        'try_offset_start', 'try_offset_end',
    })

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST) -> List[Violation]:
        violations = []

        for node in ast.walk(method_node):
            if not isinstance(node, ast.Compare):
                continue

            has_offset_var = self._has_offset_variable(node)
            has_numeric = self._has_significant_numeric(node)

            if has_offset_var and has_numeric:
                snippet = get_source_segment(
                    source_lines, node.lineno, node.end_lineno)
                # 排除标准排序模式
                if 'sorted' in snippet and 'key=' in snippet:
                    continue
                # 排除偏移范围计算（如 try_end - try_start）
                if self._is_range_calculation(node):
                    continue

                violations.append(Violation(
                    rule_id="P5", rule_name="硬编码偏移",
                    line=node.lineno, col=node.col_offset,
                    snippet=snippet[:150],
                    detail="发现偏移值硬编码比较，"
                           "应使用支配关系或控制流分析替代",
                ))

        return violations

    def _has_offset_variable(self, node: ast.Compare) -> bool:
        """检查比较节点是否包含偏移相关变量"""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in self.OFFSET_VAR_NAMES:
                return True
            if (isinstance(child, ast.Attribute) and
                    child.attr in self.OFFSET_ATTR_NAMES):
                return True
        return False

    def _has_significant_numeric(self, node: ast.Compare) -> bool:
        """检查比较节点是否包含有意义的数值常量（排除0/1/-1）"""
        for child in ast.walk(node):
            if (isinstance(child, ast.Constant) and
                    isinstance(child.value, (int, float))):
                if abs(child.value) > 1:
                    return True
        return False

    def _is_range_calculation(self, node: ast.Compare) -> bool:
        """检查是否是偏移范围计算（如 try_end - try_start > 0）"""
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Sub):
                return True
        return False


# ============================================================
# P6: 顺序依赖检测器
# ============================================================

class P6Detector:
    """
    P6: 顺序依赖检测

    检测主方法中方法调用间的隐式状态依赖。
    如果后续方法读取了前面方法写入的 self 属性，
    且没有通过参数显式传递，则存在顺序依赖。
    """

    def detect(self, method_node: ast.FunctionDef, class_name: str,
               source_lines: List[str], tree: ast.AST) -> List[Violation]:
        method_name = method_node.name

        if method_name not in ('analyze', 'generate'):
            return []

        call_sequence = self._extract_call_sequence(method_node)
        if len(call_sequence) < 2:
            return []

        violations = []
        reported_pairs: Set[Tuple[str, str]] = set()

        for i, call in enumerate(call_sequence):
            if i == 0:
                continue

            called_method = self._find_method_node(call['name'], tree)
            if called_method is None:
                continue

            read_attrs = self._find_self_attr_reads(called_method)
            if not read_attrs:
                continue

            for prev_call in call_sequence[:i]:
                prev_method = self._find_method_node(
                    prev_call['name'], tree)
                if prev_method is None:
                    continue

                written_attrs = self._find_self_attr_writes(prev_method)
                common_attrs = read_attrs & written_attrs

                if common_attrs:
                    pair = (prev_call['name'], call['name'])
                    if pair in reported_pairs:
                        continue
                    reported_pairs.add(pair)

                    snippet = get_source_segment(
                        source_lines, call['line'])
                    violations.append(Violation(
                        rule_id="P6", rule_name="顺序依赖",
                        line=call['line'], col=0,
                        snippet=snippet[:150],
                        detail=f"'{call['name']}'() 读取 "
                               f"self.{', self.'.join(sorted(common_attrs))}，"
                               f"由 '{prev_call['name']}'() 写入，"
                               f"存在隐式顺序依赖",
                    ))

        return violations

    def _extract_call_sequence(self, method_node: ast.FunctionDef
                               ) -> List[Dict[str, Any]]:
        """提取方法体中按顺序出现的 self.XXX() 调用"""
        sequence = []

        def _walk_stmts(stmts):
            for stmt in stmts:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    if (isinstance(call.func, ast.Attribute) and
                            call.func.attr.startswith('_') and
                            is_self_attr(call.func.value)):
                        sequence.append({
                            'name': call.func.attr,
                            'line': stmt.lineno,
                        })
                elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    if (isinstance(call.func, ast.Attribute) and
                            call.func.attr.startswith('_') and
                            is_self_attr(call.func.value)):
                        sequence.append({
                            'name': call.func.attr,
                            'line': stmt.lineno,
                        })
                # 递归进入 if/for/while/with/try 等复合语句
                if hasattr(stmt, 'body'):
                    _walk_stmts(stmt.body)
                if hasattr(stmt, 'orelse'):
                    _walk_stmts(stmt.orelse)
                if hasattr(stmt, 'finalbody'):
                    _walk_stmts(stmt.finalbody)
                if hasattr(stmt, 'handlers'):
                    for handler in stmt.handlers:
                        _walk_stmts(handler.body)

        _walk_stmts(method_node.body)
        return sequence

    def _find_method_node(self, name: str,
                          tree: ast.AST) -> Optional[ast.FunctionDef]:
        """按名称查找方法定义节点"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None

    def _find_self_attr_reads(self, method_node: ast.FunctionDef
                              ) -> Set[str]:
        """查找方法中读取的 self 属性"""
        attrs = set()
        for node in ast.walk(method_node):
            if (isinstance(node, ast.Attribute) and
                    isinstance(node.value, ast.Name) and
                    node.value.id == 'self' and
                    isinstance(node.ctx, ast.Load)):
                attrs.add(node.attr)
        return attrs

    def _find_self_attr_writes(self, method_node: ast.FunctionDef
                               ) -> Set[str]:
        """查找方法中写入的 self 属性"""
        attrs = set()
        for node in ast.walk(method_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Attribute) and
                            isinstance(target.value, ast.Name) and
                            target.value.id == 'self' and
                            isinstance(target.ctx, ast.Store)):
                        attrs.add(target.attr)
        return attrs


# ============================================================
# 审计引擎
# ============================================================

class MethodComplianceAuditor:
    """方法合规性审计引擎：协调所有检测器对文件进行方法级审计"""

    def __init__(self):
        self.p1 = P1Detector()
        self.p2 = P2Detector()
        self.p3 = P3Detector()
        self.p4 = P4Detector()
        self.p5 = P5Detector()
        self.p6 = P6Detector()

    def audit_file(self, filepath: str) -> FileAudit:
        """审计单个文件"""
        abs_path = os.path.abspath(filepath)

        if not os.path.exists(abs_path):
            print(f"[错误] 文件不存在: {abs_path}", file=sys.stderr)
            return FileAudit(filepath=abs_path)

        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except IOError as e:
            print(f"[错误] 无法读取文件 {abs_path}: {e}", file=sys.stderr)
            return FileAudit(filepath=abs_path)

        source_lines = source.splitlines(keepends=True)

        try:
            tree = ast.parse(source, filename=abs_path)
        except SyntaxError as e:
            print(f"[警告] 文件 {abs_path} 语法解析失败: {e}",
                  file=sys.stderr)
            return FileAudit(filepath=abs_path)

        # 收集所有类方法
        methods = self._collect_class_methods(tree)

        # P3需要：收集 _generate_ 方法并按区域类型分组
        generate_groups = self._group_generate_methods(methods)
        self.p3.reset()

        file_audit = FileAudit(filepath=abs_path)

        for method_info in methods:
            method_node = method_info['node']
            class_name = method_info['class_name']

            method_audit = MethodAudit(
                method_name=method_node.name,
                class_name=class_name,
                start_line=method_node.lineno,
                end_line=method_node.end_lineno or method_node.lineno,
            )

            # 依次运行6个检测器
            method_audit.violations.extend(
                self.p1.detect(method_node, class_name,
                               source_lines, tree))
            method_audit.violations.extend(
                self.p2.detect(method_node, class_name,
                               source_lines, tree))
            method_audit.violations.extend(
                self.p3.detect(method_node, class_name,
                               source_lines, tree, generate_groups))
            method_audit.violations.extend(
                self.p4.detect(method_node, class_name,
                               source_lines, tree, abs_path))
            method_audit.violations.extend(
                self.p5.detect(method_node, class_name,
                               source_lines, tree))
            method_audit.violations.extend(
                self.p6.detect(method_node, class_name,
                               source_lines, tree))

            file_audit.method_audits.append(method_audit)

        return file_audit

    def _collect_class_methods(self, tree: ast.AST
                               ) -> List[Dict[str, Any]]:
        """收集所有类方法（仅顶层类方法，不含嵌套函数）"""
        methods = []
        seen_ids = set()

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if id(item) not in seen_ids:
                            seen_ids.add(id(item))
                            methods.append({
                                'node': item,
                                'class_name': node.name,
                            })

        return methods

    def _group_generate_methods(self, methods: List[Dict]
                                ) -> Dict[str, List[ast.FunctionDef]]:
        """将 _generate_* 方法按区域类型分组"""
        groups: Dict[str, List[ast.FunctionDef]] = defaultdict(list)

        for method_info in methods:
            node = method_info['node']
            name = node.name
            if not name.startswith('_generate_'):
                continue
            region_type = self.p3._classify_region_type(name)
            if region_type:
                groups[region_type].append(node)

        return dict(groups)


# ============================================================
# 报告生成
# ============================================================

def generate_text_report(file_audits: List[FileAudit],
                         verbose: bool = False) -> str:
    """生成文本格式审计报告"""
    lines = []
    sep = "=" * 80
    sub_sep = "-" * 70

    lines.append(sep)
    lines.append("  方法合规性审计报告 (Method Compliance Audit Report)")
    lines.append(sep)
    lines.append("")

    total_compliant = 0
    total_violating = 0
    total_violations_by_rule: Dict[str, int] = defaultdict(int)

    for file_audit in file_audits:
        lines.append(f"  [FILE] {file_audit.filepath}")
        lines.append(sub_sep)

        compliant = file_audit.compliant_methods
        violating = file_audit.violating_methods

        total_compliant += len(compliant)
        total_violating += len(violating)

        # 合规方法列表
        if compliant:
            lines.append(f"\n  [合规方法] ({len(compliant)} 个)")
            for m in compliant:
                loc = f"行 {m.start_line}-{m.end_line}"
                cls_prefix = f"{m.class_name}." if m.class_name else ""
                lines.append(f"    {cls_prefix}{m.method_name}()  ({loc})")
        else:
            lines.append("\n  [合规方法] (0 个)")

        # 违规方法详情
        if violating:
            lines.append(f"\n  [违规方法] ({len(violating)} 个)")
            for m in violating:
                rules = ', '.join(sorted(m.violated_rules))
                cls_prefix = f"{m.class_name}." if m.class_name else ""
                loc = f"行 {m.start_line}-{m.end_line}"
                lines.append(
                    f"\n    {cls_prefix}{m.method_name}()  ({loc})  "
                    f"违反: {rules}")

                for v in m.violations:
                    total_violations_by_rule[v.rule_id] += 1
                    lines.append(
                        f"      [{v.rule_id}] 行 {v.line}: "
                        f"{v.snippet[:100]}")
                    if verbose:
                        lines.append(f"             -> {v.detail}")
        else:
            lines.append("\n  [违规方法] (0 个)")

        lines.append("")
        lines.append("")

    # 统计摘要
    lines.append(sep)
    lines.append("  [统计摘要]")
    lines.append(sep)
    lines.append(
        f"  {'规则':<8s} {'名称':<16s} {'违规数':>8s}  {'状态':<6s}")
    lines.append(f"  {'-' * 42}")

    for rule_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']:
        count = total_violations_by_rule.get(rule_id, 0)
        name = RULE_NAMES.get(rule_id, '')
        status = "[!]" if count > 0 else "[OK]"
        lines.append(
            f"  {rule_id:<8s} {name:<16s} {count:>8d}  {status}")

    lines.append(f"  {'-' * 42}")
    total_v = sum(total_violations_by_rule.values())
    lines.append(
        f"  合规方法: {total_compliant}  |  "
        f"违规方法: {total_violating}  |  "
        f"总违规数: {total_v}")
    lines.append(sep)

    return '\n'.join(lines)


def generate_json_report(file_audits: List[FileAudit]) -> str:
    """生成JSON格式审计报告"""
    total_compliant = sum(len(fa.compliant_methods) for fa in file_audits)
    total_violating = sum(len(fa.violating_methods) for fa in file_audits)
    total_violations_by_rule: Dict[str, int] = defaultdict(int)
    for fa in file_audits:
        for m in fa.method_audits:
            for v in m.violations:
                total_violations_by_rule[v.rule_id] += 1

    output = {
        "summary": {
            "total_compliant_methods": total_compliant,
            "total_violating_methods": total_violating,
            "total_violations": sum(total_violations_by_rule.values()),
            "violations_by_rule": dict(total_violations_by_rule),
        },
        "files": [fa.to_dict() for fa in file_audits],
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ============================================================
# CLI 入口
# ============================================================

def get_default_files() -> List[str]:
    """获取默认扫描文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(script_dir, 'region_analyzer.py'),
        os.path.join(script_dir, 'region_ast_generator.py'),
    ]


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='方法合规性审计工具 — 检测Python反编译器中的补丁驱动开发模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              (扫描默认文件)
  %(prog)s -v                           (详细模式)
  %(prog)s --json                       (JSON输出)
  %(prog)s core/cfg/region_analyzer.py  (指定文件)

检测规则说明:
  P1  后处理修正   — 在区域创建后修改其属性
  P2  特殊情况分支 — if/elif条件中硬编码字节码指令名
  P3  多路径生成   — 同一区域类型存在多个生成入口
  P4  跨职责逻辑   — 分析器中混入生成逻辑或反之
  P5  硬编码偏移   — 依赖特定偏移数值的比较
  P6  顺序依赖     — 方法间隐式状态依赖
        """
    )
    parser.add_argument(
        'files', metavar='FILE', nargs='*',
        help='要扫描的Python源文件路径（默认扫描region_analyzer.py和region_ast_generator.py）'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='输出详细模式（包含每条违规的详细描述）'
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='以JSON格式输出结果'
    )
    return parser.parse_args()


def main():
    """CLI入口"""
    args = parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    files = args.files if args.files else get_default_files()

    # 验证文件存在
    valid_files = []
    for f in files:
        if os.path.exists(f):
            valid_files.append(f)
        else:
            print(f"[警告] 文件不存在，已跳过: {f}", file=sys.stderr)

    if not valid_files:
        print("[错误] 没有可扫描的文件", file=sys.stderr)
        sys.exit(1)

    auditor = MethodComplianceAuditor()
    file_audits = []

    for filepath in valid_files:
        audit = auditor.audit_file(filepath)
        file_audits.append(audit)

    if args.json_output:
        output = generate_json_report(file_audits)
    else:
        output = generate_text_report(file_audits, verbose=args.verbose)

    print(output)

    total_violations = sum(
        len(m.violations)
        for fa in file_audits
        for m in fa.method_audits
    )
    sys.exit(min(total_violations, 1))


if __name__ == '__main__':
    main()
