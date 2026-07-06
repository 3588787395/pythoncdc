"""
补丁行为自动检测工具 (Patch Behavior Auto-Detector)

基于 AST 的静态分析工具，用于检测代码中违反区域归约算法原则的"补丁行为"模式。
使用 ast 模块解析 Python 源码（不依赖正则表达式），确保检测结果准确。

六项检测功能：
  28.1  后处理修正     检测 _fix_*/_merge_* 等后处理方法名及后处理识别方法
  28.2  特殊情况分支   检测特殊注释标记和过长的 if/elif 链
  28.3  多种生成路径   检测同一结构类型的多种生成方法和 _from_block 违规
  28.4  跨职责修改     检测生成器中对分析数据结构（支配树等）的直接访问
  28.5  硬编码偏移     检测 .offset 比较、硬编码数字索引
  28.6  顺序依赖       检测多步初始化过程和方法间隐式状态传递

使用方式：
    python tests/anti_patch/patch_detector.py
    python -m tests.anti_patch.patch_detector
"""

import ast
import os
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Violation:
    """单条违规记录"""
    category: str
    rule_id: str
    file_path: str
    line: int
    method_name: str
    snippet: str
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'rule_id': self.rule_id,
            'file_path': self.file_path,
            'line': self.line,
            'method_name': self.method_name,
            'snippet': self.snippet,
            'detail': self.detail,
        }


def _get_source_snippet(lines: List[str], lineno: int,
                        end_lineno: Optional[int] = None) -> str:
    """获取源代码片段"""
    start = max(0, lineno - 1)
    end = min(len(lines), end_lineno or lineno)
    return ''.join(lines[start:end]).strip()


# ============================================================
# 28.1 后处理修正检测器
# ============================================================

class PostProcessingDetector:
    FIX_PREFIXES = ('_fix_',)
    MERGE_SUFFIXES = ('condition', 'compare', 'chain')
    POST_IDENTIFY_NAMES = frozenset({
        '_identify_nop', '_identify_optimized',
        '_identify_redundant', '_identify_fallback',
    })

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            name = node.name
            matched = self._check_method_name(name)
            if matched:
                snippet = _get_source_snippet(source_lines, node.lineno,
                                              node.end_lineno)
                violations.append(Violation(
                    category='后处理修正', rule_id='28.1',
                    file_path=file_path, line=node.lineno,
                    method_name=name, snippet=snippet[:120],
                    detail=f"发现后处理修正方法: {matched}",
                ))
        return violations

    def _check_method_name(self, name: str) -> Optional[str]:
        for prefix in self.FIX_PREFIXES:
            if name.startswith(prefix):
                return f"方法名以 '{prefix}' 开头 ({name})"
        if name.startswith('_merge_'):
            suffix = name[len('_merge_'):]
            for ms in self.MERGE_SUFFIXES:
                if suffix == ms or suffix.startswith(ms + '_') or suffix.endswith('_' + ms):
                    return f"合并方法 '_merge_{suffix}' (可能为后处理合并)"
        if name in self.POST_IDENTIFY_NAMES:
            return f"后处理识别方法 '{name}'"
        return None


# ============================================================
# 28.2 特殊情况分支检测器
# ============================================================

class SpecialCaseDetector:
    COMMENT_MARKERS = ['[关键修复]', '[FIXME]', 'HACK', 'WORKAROUND']
    ELIF_THRESHOLD = 5

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        violations = []
        violations.extend(self._detect_comment_markers(source_lines, file_path))
        violations.extend(self._detect_long_if_elif_chains(tree, source_lines,
                                                          file_path))
        return violations

    def _detect_comment_markers(self, source_lines: List[str],
                                file_path: str) -> List[Violation]:
        violations = []
        for i, line in enumerate(source_lines, start=1):
            stripped = line.strip()
            comment_text = self._extract_inline_comment(stripped)
            if comment_text is None:
                continue
            for marker in self.COMMENT_MARKERS:
                if marker.upper() in comment_text.upper():
                    violations.append(Violation(
                        category='特殊情况分支', rule_id='28.2',
                        file_path=file_path, line=i,
                        method_name='(注释)', snippet=stripped[:120],
                        detail=f"注释中发现特殊修复标记: '{marker}'",
                    ))
                    break
        return violations

    def _extract_inline_comment(self, line: str) -> Optional[str]:
        in_string = False
        quote_char = None
        idx = 0
        while idx < len(line):
            ch = line[idx]
            if not in_string and ch in ("'", '"'):
                qc = ch
                triple = (idx + 2 < len(line) and
                          line[idx + 1] == ch and line[idx + 2] == ch)
                if triple:
                    idx += 3
                    continue
                in_string = True
                quote_char = qc
            elif in_string and ch == quote_char:
                next_same = (idx + 1 < len(line) and
                             line[idx + 1] == quote_char)
                if not next_same:
                    in_string = False
                    quote_char = None
            elif not in_string and ch == '#':
                return line[idx + 1:].strip()
            idx += 1
        return None

    def _detect_long_if_elif_chains(self, tree: ast.AST,
                                    source_lines: List[str],
                                    file_path: str) -> List[Violation]:
        violations = []

        def count_elif_chain(if_node: ast.If) -> int:
            depth = 0
            current = if_node
            while True:
                if not current.orelse or len(current.orelse) != 1:
                    break
                child = current.orelse[0]
                if not isinstance(child, ast.If):
                    break
                depth += 1
                current = child
            return depth

        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            elif_count = count_elif_chain(node)
            if elif_count > self.ELIF_THRESHOLD:
                snippet = _get_source_snippet(source_lines, node.lineno,
                                              node.end_lineno)
                enclosing = self._find_enclosing_method(tree, node.lineno)
                violations.append(Violation(
                    category='特殊情况分支', rule_id='28.2',
                    file_path=file_path, line=node.lineno,
                    method_name=enclosing or '(顶层)',
                    snippet=snippet[:120],
                    detail=(f"if/elif 链过长: {elif_count} 个 elif "
                            f"(阈值: {self.ELIF_THRESHOLD})"),
                ))
        return violations

    def _find_enclosing_method(self, tree: ast.AST,
                               target_line: int) -> Optional[str]:
        best_name = None
        best_start = -1
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                s = node.lineno
                e = node.end_lineno or s
                if s <= target_line <= e and s > best_start:
                    best_name = node.name
                    best_start = s
        return best_name


# ============================================================
# 28.3 多种生成路径检测器
# ============================================================

class MultiPathGeneratorDetector:
    REGION_KEYWORDS: Dict[str, List[str]] = {
        'if': ['if', 'branch', 'cond'],
        'loop': ['loop', 'for', 'while', 'iter'],
        'try': ['try', 'except', 'finally', 'handler'],
        'with': ['with'],
        'match': ['match', 'case'],
        'boolop': ['boolop', 'bool_op'],
        'ternary': ['ternary', 'if_exp'],
        'return': ['return'],
        'basic': ['basic', 'sequence', 'linear'],
        'assert': ['assert'],
    }

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        violations = []
        methods = self._collect_generate_methods(tree)
        if not methods:
            return violations
        violations.extend(
            self._detect_from_block_methods(methods, source_lines, file_path))
        violations.extend(
            self._detect_multi_path_generation(methods, source_lines, file_path))

        total_gen = len(methods)
        if total_gen > 15:
            first_method = methods[0]
            violations.append(Violation(
                category='多种生成路径', rule_id='28.3',
                file_path=file_path, line=first_method.lineno,
                method_name='(类级别)',
                snippet=f'_generate_* 方法总数: {total_gen}',
                detail=(f"_generate_* 方法过多 ({total_gen} 个)，"
                        f"暗示可能存在冗余的生成路径"),
            ))
        return violations

    def _collect_generate_methods(self, tree: ast.AST) -> List[ast.FunctionDef]:
        result = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and \
                    node.name.startswith('_generate_'):
                result.append(node)
        result.sort(key=lambda n: n.lineno)
        return result

    def _detect_from_block_methods(self, methods: List[ast.FunctionDef],
                                   source_lines: List[str],
                                   file_path: str) -> List[Violation]:
        violations = []
        for m in methods:
            if '_from_block' in m.name:
                snippet = _get_source_snippet(source_lines, m.lineno,
                                              m.end_lineno)
                violations.append(Violation(
                    category='多种生成路径', rule_id='28.3',
                    file_path=file_path, line=m.lineno,
                    method_name=m.name, snippet=snippet[:120],
                    detail=(f"发现 '_generate_*_from_block' 方法 ({m.name})，"
                            f"违反只从区域生成AST的原则"),
                ))
        return violations

    def _detect_multi_path_generation(self, methods: List[ast.FunctionDef],
                                      source_lines: List[str],
                                      file_path: str) -> List[Violation]:
        violations = []
        groups: Dict[str, List[ast.FunctionDef]] = defaultdict(list)
        for m in methods:
            rtype = self._classify(m.name)
            if rtype:
                groups[rtype].append(m)

        for rtype, method_list in groups.items():
            if len(method_list) >= 2:
                names = sorted(n.name for n in method_list)
                first_line = min(n.lineno for n in method_list)
                snippet = ', '.join(names)[:120]
                violations.append(Violation(
                    category='多种生成路径', rule_id='28.3',
                    file_path=file_path, line=first_line,
                    method_name='(类级别)', snippet=snippet,
                    detail=(f"区域类型 '{rtype}' 存在 "
                            f"{len(method_list)} 个生成入口: "
                            f"{', '.join(names)}"),
                ))
        return violations

    def _classify(self, method_name: str) -> Optional[str]:
        lower = method_name.lower()
        for rtype, keywords in self.REGION_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    return rtype
        return None


# ============================================================
# 28.4 跨职责修改检测器
# ============================================================

class CrossResponsibilityDetector:
    ANALYSIS_ATTRS = frozenset({
        'dominator_tree', 'post_dominator_tree',
        'dominance_frontier', 'back_edges', 'forward_edges',
        'predecessors', 'successors',
        'predecessor_map', 'successor_map',
        'dominators', 'post_dominators',
        'immediate_dominator', 'immediate_post_dominator',
        'loop_nesting_tree', 'loop_headers',
        'natural_loops', 'reducible_loops',
        'control_dependencies',
    })

    ANALYSIS_METHODS = frozenset({
        'compute_dominators', 'compute_post_dominators',
        'compute_dominance_frontier',
        'find_back_edges', 'find_loops',
        'build_predecessor_map', 'build_successor_map',
        'analyze_natural_loops', 'analyze_reducibility',
        'get_dominator', 'get_post_dominator',
        'dominates', 'post_dominates',
    })

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        basename = os.path.basename(file_path).lower()
        if 'region_ast_generator' not in basename:
            return []

        violations = []
        attr_accesses: Dict[Tuple[str, int], Set[str]] = defaultdict(set)
        method_calls: Dict[Tuple[str, int], Set[str]] = defaultdict(set)

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            method_name = node.name
            method_key = (method_name, node.lineno)

            for child in ast.walk(node):
                if isinstance(child, ast.Attribute):
                    if child.attr in self.ANALYSIS_ATTRS:
                        attr_accesses[method_key].add(child.attr)
                if (isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Attribute)):
                    if child.func.attr in self.ANALYSIS_METHODS:
                        method_calls[method_key].add(child.func.attr)

        for (method_name, line), attrs in sorted(attr_accesses.items()):
            snippet = _get_source_snippet(source_lines, line)
            violations.append(Violation(
                category='跨职责修改', rule_id='28.4',
                file_path=file_path, line=line,
                method_name=method_name, snippet=snippet[:120],
                detail=(f"生成器中直接访问分析数据结构属性: "
                        f"{', '.join(sorted(attrs))}，"
                        f"违反职责分离原则"),
            ))

        for (method_name, line), calls in sorted(method_calls.items()):
            snippet = _get_source_snippet(source_lines, line)
            violations.append(Violation(
                category='跨职责修改', rule_id='28.4',
                file_path=file_path, line=line,
                method_name=method_name, snippet=snippet[:120],
                detail=(f"生成器中调用分析方法: "
                        f"{', '.join(sorted(calls))}，"
                        f"违反职责分离原则"),
            ))

        return violations


# ============================================================
# 28.5 硬编码偏移检测器
# ============================================================

class HardcodedOffsetDetector:
    OFFSET_ATTRS = frozenset({'offset', 'start_offset', 'end_offset'})
    BLOCK_CONTAINER_NAMES = frozenset({
        'blocks', 'instructions', 'instrs', 'block_list',
        'basic_blocks', 'all_blocks',
    })

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        violations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            method_name = node.name
            for child in ast.walk(node):
                violations.extend(
                    self._check_offset_comparison(
                        child, source_lines, file_path, method_name))
                violations.extend(
                    self._check_hardcoded_index(
                        child, source_lines, file_path, method_name))
        return violations

    def _check_offset_comparison(self, node: ast.AST, source_lines: List[str],
                                 file_path: str,
                                 method_name: str) -> List[Violation]:
        violations = []
        if not isinstance(node, ast.Compare):
            return violations

        has_offset_attr = False
        has_numeric_literal = False
        numeric_value = None

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute) and \
                    child.attr in self.OFFSET_ATTRS:
                has_offset_attr = True
            if (isinstance(child, ast.Constant) and
                    isinstance(child.value, (int, float))):
                has_numeric_literal = True
                numeric_value = child.value

        if has_offset_attr and has_numeric_literal and numeric_value is not None:
            snippet = _get_source_snippet(source_lines, node.lineno,
                                          node.end_lineno)
            violations.append(Violation(
                category='硬编码偏移', rule_id='28.5',
                file_path=file_path, line=node.lineno,
                method_name=method_name, snippet=snippet[:120],
                detail=f"硬编码偏移值比较 (.offset 与常量 {numeric_value})",
            ))
        return violations

    def _check_hardcoded_index(self, node: ast.AST, source_lines: List[str],
                               file_path: str,
                               method_name: str) -> List[Violation]:
        violations = []
        if not isinstance(node, ast.Subscript):
            return violations

        value = node.value
        slice_node = node.slice

        container_name = None
        if isinstance(value, ast.Name) and value.id in self.BLOCK_CONTAINER_NAMES:
            container_name = value.id
        elif (isinstance(value, ast.Attribute) and
              value.attr in self.BLOCK_CONTAINER_NAMES):
            container_name = value.attr

        if container_name is None:
            return violations

        index_val = self._extract_index_value(slice_node)
        if index_val is not None and isinstance(index_val, int):
            snippet = _get_source_snippet(source_lines, node.lineno,
                                          node.end_lineno)
            violations.append(Violation(
                category='硬编码偏移', rule_id='28.5',
                file_path=file_path, line=node.lineno,
                method_name=method_name, snippet=snippet[:120],
                detail=f"硬编码数字索引访问: {container_name}[{index_val}]",
            ))
        return violations

    def _extract_index_value(self, slice_node: ast.AST) -> Optional[Any]:
        if isinstance(slice_node, ast.Constant):
            return slice_node.value
        if isinstance(slice_node, ast.UnaryOp) and \
                isinstance(slice_node.operand, ast.Constant):
            operand = slice_node.operand.value
            if isinstance(slice_node.op, ast.USub) and isinstance(operand, int):
                return -operand
            if isinstance(slice_node.op, ast.UAdd) and isinstance(operand, int):
                return operand
        return None


# ============================================================
# 28.6 顺序依赖检测器
# ============================================================

class OrderDependencyDetector:
    INIT_PATTERNS = frozenset({
        'init', 'setup', 'prepare', 'initialize', 'reset', 'build'})

    def detect(self, tree: ast.AST, source_lines: List[str],
               file_path: str) -> List[Violation]:
        violations = []
        main_methods = self._find_main_methods(tree)
        for main_node in main_methods:
            violations.extend(
                self._detect_init_sequence(main_node, tree,
                                           source_lines, file_path))
            violations.extend(
                self._detect_state_dependency(main_node, tree,
                                             source_lines, file_path))
        return violations

    def _find_main_methods(self, tree: ast.AST) -> List[ast.FunctionDef]:
        result = []
        main_names = {'analyze', 'generate', 'run', 'main', '__init__'}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and \
                            item.name in main_names:
                        result.append(item)
        return result

    def _detect_init_sequence(self, main_node: ast.FunctionDef, tree: ast.AST,
                              source_lines: List[str],
                              file_path: str) -> List[Violation]:
        violations = []
        call_sequence = self._extract_ordered_self_calls(main_node)

        init_calls = [
            c for c in call_sequence
            if any(p in c['name'] for p in self.INIT_PATTERNS)
        ]

        if len(init_calls) >= 3:
            names = [c['name'] for c in init_calls]
            lines = [c['line'] for c in init_calls]
            snippet = _get_source_snippet(source_lines, min(lines))
            violations.append(Violation(
                category='顺序依赖', rule_id='28.6',
                file_path=file_path, line=min(lines),
                method_name=main_node.name, snippet=snippet[:120],
                detail=(f"多步初始化序列 ({len(init_calls)} 步): "
                        f"{', '.join(names)}，调用顺序影响结果正确性"),
            ))
        return violations

    def _detect_state_dependency(self, main_node: ast.FunctionDef, tree: ast.AST,
                                 source_lines: List[str],
                                 file_path: str) -> List[Violation]:
        violations = []
        call_sequence = self._extract_ordered_self_calls(main_node)
        if len(call_sequence) < 2:
            return violations

        reported_pairs: Set[Tuple[str, str]] = set()

        for i in range(1, len(call_sequence)):
            curr = call_sequence[i]
            curr_name = curr['name']
            curr_def = self._find_function_def(tree, curr_name)
            if curr_def is None:
                continue

            read_attrs = self._collect_self_load_attrs(curr_def)
            if not read_attrs:
                continue

            for prev in call_sequence[:i]:
                prev_name = prev['name']
                pair = (prev_name, curr_name)
                if pair in reported_pairs:
                    continue

                prev_def = self._find_function_def(tree, prev_name)
                if prev_def is None:
                    continue

                written_attrs = self._collect_self_store_attrs(prev_def)
                common = read_attrs & written_attrs

                if common:
                    reported_pairs.add(pair)
                    snippet = _get_source_snippet(source_lines, curr['line'])
                    violations.append(Violation(
                        category='顺序依赖', rule_id='28.6',
                        file_path=file_path, line=curr['line'],
                        method_name=main_node.name, snippet=snippet[:120],
                        detail=(f"'{curr_name}'() 读取 self."
                                f"{', self.'.join(sorted(common))}，"
                                f"由 '{prev_name}'() 写入，"
                                f"存在隐式顺序依赖"),
                    ))
        return violations

    def _extract_ordered_self_calls(self,
                                    method_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        sequence = []

        def walk_stmts(stmts):
            for stmt in stmts:
                call_info = self._try_extract_self_call(stmt)
                if call_info:
                    sequence.append(call_info)
                for body_attr in ('body', 'orelse', 'finalbody'):
                    if hasattr(stmt, body_attr):
                        sub = getattr(stmt, body_attr)
                        if isinstance(sub, list):
                            walk_stmts(sub)
                if hasattr(stmt, 'handlers'):
                    for handler in stmt.handlers:
                        if hasattr(handler, 'body'):
                            walk_stmts(handler.body)

        walk_stmts(method_node.body)
        return sequence

    def _try_extract_self_call(self, stmt: ast.stmt) -> Optional[Dict[str, Any]]:
        call_node = None
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call_node = stmt.value
        elif isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
            call_node = stmt.value
        if call_node is None:
            return None

        func = call_node.func
        if not isinstance(func, ast.Attribute):
            return None
        value = func.value
        if not isinstance(value, ast.Name) or value.id != 'self':
            return None
        return {'name': func.attr, 'line': stmt.lineno}

    def _find_function_def(self, tree: ast.AST,
                           name: str) -> Optional[ast.FunctionDef]:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None

    def _collect_self_load_attrs(self,
                                 func_def: ast.FunctionDef) -> Set[str]:
        attrs = set()
        for node in ast.walk(func_def):
            if (isinstance(node, ast.Attribute) and
                    isinstance(node.ctx, ast.Load) and
                    isinstance(node.value, ast.Name) and
                    node.value.id == 'self'):
                attrs.add(node.attr)
        return attrs

    def _collect_self_store_attrs(self,
                                  func_def: ast.FunctionDef) -> Set[str]:
        attrs = set()
        for node in ast.walk(func_def):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Attribute) and
                            isinstance(target.ctx, ast.Store) and
                            isinstance(target.value, ast.Name) and
                            target.value.id == 'self'):
                        attrs.add(target.attr)
            if isinstance(node, ast.AugAssign):
                if (isinstance(node.target, ast.Attribute) and
                        isinstance(node.target.value, ast.Name) and
                        node.target.value.id == 'self'):
                    attrs.add(node.target.attr)
        return attrs


# ============================================================
# PatchDetector 主类
# ============================================================

class PatchDetector:
    CATEGORY_LABELS = {
        '后处理修正': '28.1 后处理修正  检测 _fix_*/_merge_* 等后处理修正方法',
        '特殊情况分支': '28.2 特殊情况分支  检测特殊注释标记与过长的 if/elif 链',
        '多种生成路径': '28.3 多种生成路径  检测同一结构类型的多种生成方式',
        '跨职责修改': '28.4 跨职责修改  检测生成器中的分析数据结构访问',
        '硬编码偏移': '28.5 硬编码偏移  检测 .offset 比较与硬编码索引',
        '顺序依赖': '28.6 顺序依赖  检测多步初始化与方法间状态传递',
    }

    def __init__(self, source_files: List[str]):
        """初始化：指定要检测的源文件列表"""
        self.source_files = source_files
        self._detectors = [
            PostProcessingDetector(),
            SpecialCaseDetector(),
            MultiPathGeneratorDetector(),
            CrossResponsibilityDetector(),
            HardcodedOffsetDetector(),
            OrderDependencyDetector(),
        ]
        self._results: Dict[str, List[Dict]] = {}

    def detect_all(self) -> Dict[str, List[Dict]]:
        """运行所有检测，返回 {类别: [违规详情]}"""
        self._results = {}
        for filepath in self.source_files:
            abs_path = os.path.abspath(filepath)
            if not os.path.exists(abs_path):
                continue
            try:
                with open(abs_path, 'r', encoding='utf-8',
                          errors='replace') as f:
                    source = f.read()
                source_lines = source.splitlines(keepends=True)
                tree = ast.parse(source, filename=abs_path)
            except (IOError, SyntaxError):
                continue

            for detector in self._detectors:
                try:
                    vlist = detector.detect(tree, source_lines, abs_path)
                    for v in vlist:
                        cat = v.category
                        if cat not in self._results:
                            self._results[cat] = []
                        self._results[cat].append(v.to_dict())
                except Exception:
                    pass

        for cat in self.CATEGORY_LABELS:
            if cat not in self._results:
                self._results[cat] = []

        return self._results

    def generate_report(self) -> str:
        """生成人类可读的报告"""
        if not self._results:
            self.detect_all()

        lines = []
        sep = '=' * 76
        sub_sep = '-' * 68

        lines.append(sep)
        lines.append('  补丁行为自动检测报告 '
                     '(Patch Behavior Auto-Detection Report)')
        lines.append(sep)
        lines.append('')

        total_by_cat: Dict[str, int] = defaultdict(int)
        files_scanned = set()

        for cat, cat_label in self.CATEGORY_LABELS.items():
            vlist = self._results.get(cat, [])
            total_by_cat[cat] = len(vlist)
            for v in vlist:
                files_scanned.add(v.get('file_path', ''))

            lines.append(f'  [{cat}] {cat_label.split(" - ", 1)[-1]}')
            lines.append(sub_sep)

            if vlist:
                for idx, v in enumerate(vlist, 1):
                    fname = os.path.basename(v.get('file_path', ''))
                    lines.append(
                        f'    #{idx:<3d} [{v["rule_id"]}] '
                        f'{fname}:{v["line"]:>4d}  '
                        f'{v["method_name"]}()')
                    lines.append(f'         {v["snippet"][:90]}')
                    lines.append(f'         -> {v["detail"]}')
            else:
                lines.append('    OK 未检测到违规')

            lines.append('')
            lines.append('')

        lines.append(sep)
        lines.append('  [统计摘要]')
        lines.append(sep)
        lines.append(f'  {"规则":<14s} {"描述":<22s} {"违规数":>6s}   '
                     f'{"状态":<8s}')
        lines.append(f'  {"-" * 56}')

        grand_total = 0
        for cat, cat_label in self.CATEGORY_LABELS.items():
            count = total_by_cat.get(cat, 0)
            status = '[!]' if count > 0 else '[OK]'
            desc_short = cat_label.split(' - ')[-1][:20]
            lines.append(f'  {cat:<14s} {desc_short:<22s} {count:>6d}   '
                         f'{status}')
            grand_total += count

        lines.append(f'  {"-" * 56}')
        lines.append(
            f'  扫描文件: {len(files_scanned)} 个  |  '
            f'总违规数: {grand_total}')
        lines.append(sep)

        return '\n'.join(lines)

    def count_violations(self) -> int:
        """返回违规总数"""
        if not self._results:
            self.detect_all()
        return sum(len(vlist) for vlist in self._results.values())


if __name__ == '__main__':
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    default_files = [
        os.path.join(base_dir, 'core', 'cfg', 'region_analyzer.py'),
        os.path.join(base_dir, 'core', 'cfg', 'region_ast_generator.py'),
    ]

    detector = PatchDetector(default_files)
    report = detector.generate_report()
    print(report)
    print(f'\nTotal violations: {detector.count_violations()}')