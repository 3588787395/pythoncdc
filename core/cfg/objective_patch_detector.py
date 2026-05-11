"""
客观补丁检测器 v2.0 - 基于6维客观特征的自动化补丁检测系统

6维判定规则：
  D1 算法依据性  — AST文档字符串扫描理论引用关键词
  D2 特殊分支数  — 统计if/elif分支数量（>3种为违规）
  D3 后处理修正  — 检测对已创建对象的修改操作
  D4 跨域访问    — 检测跨域导入和属性访问
  D5 多路径生成  — 检测同一区域的多个生成方法
  D6 硬编码引用  — 硬编码操作码字符串检测

判定标准：任何方法满足≥3项违规即判定为补丁方法

使用方式：
    from core.cfg.objective_patch_detector import ObjectivePatchDetector
    detector = ObjectivePatchDetector()
    verdicts = detector.analyze_file("path/to/file.py")
    report = detector.generate_report(verdicts)
"""

import ast
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any


@dataclass
class PatchVerdict:
    """单个方法的补丁判定结果"""
    method_name: str
    d1_score: float = 1.0
    d2_score: float = 1.0
    d3_score: float = 1.0
    d4_score: float = 1.0
    d5_score: float = 1.0
    d6_score: float = 1.0
    is_patch: bool = False
    violation_count: int = 0
    violation_details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'method_name': self.method_name,
            'd1_score': round(self.d1_score, 2),
            'd2_score': round(self.d2_score, 2),
            'd3_score': round(self.d3_score, 2),
            'd4_score': round(self.d4_score, 2),
            'd5_score': round(self.d5_score, 2),
            'd6_score': round(self.d6_score, 2),
            'is_patch': self.is_patch,
            'violation_count': self.violation_count,
            'violation_details': self.violation_details,
        }


class ObjectivePatchDetector:
    """客观补丁检测器 - 基于代码特征而非注释"""

    def __init__(self):
        self.approved_theory_keywords = [
            'dominator', 'post-dominator', 'natural loop',
            'dominance frontier', 'exception table', 'opcode feature',
            'Aho', 'Lam', 'Sethi', 'Ullman', 'Dragon Book',
            'Cytron', 'SSA', 'CPython', 'PEP-659',
            'structural analysis', 'interval analysis',
            'control flow graph', 'CFG'
        ]
        self.hardcoded_opcodes = {
            'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
            'FOR_ITER', 'GET_ITER', 'GET_ANEXT', 'GET_AITER',
            'LOAD_CONST', 'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL',
            'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL',
            'COMPARE_OP', 'BINARY_OP', 'BINARY_SUBSCR',
            'BEFORE_WITH', 'WITH_EXCEPT_START', 'WITH_EXCEPT_FINISH',
            'PUSH_EXC_INFO', 'RERAISE', 'CHECK_EXC_MATCH',
            'MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE',
            'LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_MERGE',
            'RETURN_VALUE', 'RAISE_VARARGS',
        }

    def analyze_file(self, filepath: str) -> List[PatchVerdict]:
        """分析整个文件的所有方法，返回每个方法的补丁判定结果"""
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
        tree = ast.parse(source_code)
        all_methods = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                all_methods.append(node.name)
        verdicts = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for item in ast.iter_child_nodes(node):
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        verdict = self.analyze_method(
                            item, source_code,
                            class_context=class_name,
                            all_methods=all_methods
                        )
                        verdicts.append(verdict)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                verdict = self.analyze_method(
                    node, source_code,
                    class_context=None,
                    all_methods=all_methods
                )
                verdicts.append(verdict)
        return verdicts

    def analyze_method(self, method_node, source_code: str,
                       class_context: str = None,
                       all_methods: List[str] = None) -> PatchVerdict:
        """对单个方法进行6维分析，返回综合判定结果"""
        docstring = ast.get_docstring(method_node) or ''
        name = method_node.name
        start_line = method_node.lineno
        end_line = getattr(method_node, 'end_line', None)
        if end_line is None:
            end_line = self._infer_end_line(source_code, start_line)

        d1_score, d1_detail = self._check_d1_algorithm_basis(method_node, docstring)
        d2_score, d2_detail = self._check_d2_special_branches(method_node)
        d3_score, d3_detail = self._check_d3_postprocessing(method_node, source_code)
        d4_score, d4_detail = self._check_d4_cross_domain_access(
            method_node, source_code, class_context or '')
        d5_score, d5_detail = self._check_d5_multi_path_generation(
            method_node, source_code, all_methods or [])
        d6_score, d6_detail = self._check_d6_hardcoded_references(
            source_code, start_line, end_line)

        scores = [d1_score, d2_score, d3_score, d4_score, d5_score, d6_score]
        details = [d1_detail, d2_detail, d3_detail, d4_detail, d5_detail, d6_detail]
        violation_count = sum(1 for s in scores if s < 0.5)
        violation_details = [d for s, d in zip(scores, details) if s < 0.5]

        return PatchVerdict(
            method_name=name,
            d1_score=d1_score, d2_score=d2_score, d3_score=d3_score,
            d4_score=d4_score, d5_score=d5_score, d6_score=d6_score,
            is_patch=violation_count >= 3,
            violation_count=violation_count,
            violation_details=violation_details,
        )

    def _infer_end_line(self, source_code: str, start_line: int) -> int:
        """从源代码推断方法的结束行（当AST节点没有end_line属性时）"""
        lines = source_code.split('\n')
        base_indent = None
        for i in range(start_line - 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue
            if base_indent is None:
                base_indent = len(line) - len(line.lstrip())
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent < base_indent and line.strip():
                return i
        return len(lines)

    def _check_d1_algorithm_basis(self, method_node, docstring: str) -> Tuple[float, str]:
        """D1: 算法依据性检测 — 扫描文档字符串中的理论引用关键词"""
        combined_text = (docstring or '').lower()
        found_keywords = []
        for kw in self.approved_theory_keywords:
            if kw.lower() in combined_text:
                found_keywords.append(kw)
        if len(found_keywords) >= 2:
            return (1.0,
                    f"D1合规: 发现{len(found_keywords)}个理论引用关键词({', '.join(found_keywords[:3])})")
        elif len(found_keywords) == 1:
            return (0.5, f"D1部分合规: 仅发现1个理论关键词({found_keywords[0]})")
        return (0.0, "D1违规: 文档字符串中无编译器理论引用")

    def _check_d2_special_branches(self, method_node) -> Tuple[float, str]:
        """D2: 特殊分支数检测 — 统计顶层if/elif分支数量"""
        branch_patterns = set()
        for child in ast.walk(method_node):
            if isinstance(child, ast.If):
                test_source = self._extract_test_pattern(child.test)
                if test_source:
                    branch_patterns.add(test_source)
        if len(branch_patterns) <= 2:
            return (1.0, f"D2合规: {len(branch_patterns)}种分支模式(≤2)")
        return (0.0, f"D2违规: {len(branch_patterns)}种不同分支模式(>2)")

    def _extract_test_pattern(self, test_node) -> Optional[str]:
        """提取if条件测试的模式签名"""
        if isinstance(test_node, ast.Compare):
            left = self._node_signature(test_node.left)
            ops = [type(op).__name__ for op in test_node.ops]
            return f"Compare:{left}:{'+'.join(ops)}"
        if isinstance(test_node, ast.BoolOp):
            return f"BoolOp:{type(test_node.op).__name__}"
        if isinstance(test_node, ast.Attribute):
            return f"Attr:{test_node.attr}"
        if isinstance(test_node, ast.Call):
            func = self._node_signature(test_node.func)
            args_sig = '+'.join(self._node_signature(a) for a in test_node.args)
            return f"Call:{func}({args_sig})"
        return type(test_node).__name__

    def _node_signature(self, node) -> str:
        """生成AST节点的类型签名"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._node_signature(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            return f"{self._node_signature(node.value)}[]"
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        return type(node).__name__

    def _check_d3_postprocessing(self, method_node, source_code: str) -> Tuple[float, str]:
        """D3: 后处理修正检测 — 检测对已创建区域对象的属性赋值"""
        lines = source_code.split('\n')
        start = method_node.lineno - 1
        end = getattr(method_node, 'end_line', None)
        if end is None:
            end = self._infer_end_line(source_code, method_node.lineno)
        method_lines = lines[start:end]
        postprocess_patterns = [
            r'(?:region|block|node)\.\w+\s*=\s*',
            r'\w+\.(?:try_blocks|except_handlers|patched|extra_data|fixed|adjusted)\s*=',
            r'(?:region|Region)\[\w+\]\s*=',
            r'\.append\(.*(?:region|Region)',
            r'\.insert\(.*(?:region|Region)',
            r'for\s+\w+\s+in\s+(?:region|block)\.',
        ]
        violations = []
        for i, line in enumerate(method_lines, start=start + 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            for pattern in postprocess_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    violations.append((i, stripped[:80]))
                    break
        if not violations:
            return (1.0, "D3合规: 未检测到后处理修正操作")
        return (0.0, f"D3违规: 发现{len(violations)}处后处理修正")

    def _check_d4_cross_domain_access(self, method_node, source_code: str,
                                       class_name: str) -> Tuple[float, str]:
        """D4: 跨域访问检测 — 检测直接访问字节码指令或BasicBlock内部字段"""
        lines = source_code.split('\n')
        start = method_node.lineno - 1
        end = getattr(method_node, 'end_line', None)
        if end is None:
            end = self._infer_end_line(source_code, method_node.lineno)
        method_lines = lines[start:end]
        illegal_accesses = []
        legal_attr_patterns = [
            r'\.metadata[\.\[]',
            r'\.parent\b',
            r'\.children\b',
            r'\.blocks\b',
            r'cfg\.',
            r'self\._\w+\(',
        ]
        for i, line in enumerate(method_lines, start=start + 1):
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                continue
            is_legal = any(re.search(p, stripped) for p in legal_attr_patterns)
            if is_legal:
                continue
            illegal_patterns = [
                (r'\.instructions\s*\[', '直接访问指令列表'),
                (r'\.instructions\b', '直接访问指令属性'),
                (r'for\s+\w+\s+in\s+\w+\.instructions', '遍历指令列表'),
                (r'\._\w+\s*=', '访问私有字段'),
                (r'BasicBlock\(', '直接构造BasicBlock'),
                (r'Instruction\(', '直接构造Instruction'),
                (r"\.opcode\s*==\s*['\"]", '硬编码操作码比较'),
                (r"\.opname\s*==\s*['\"]", '硬编码操作名比较'),
            ]
            for pattern, desc in illegal_patterns:
                if re.search(pattern, stripped):
                    illegal_accesses.append((i, desc))
                    break
        if not illegal_accesses:
            return (1.0, "D4合规: 未检测到跨域非法访问")
        desc_set = list(set(d for _, d in illegal_accesses))
        return (0.0, f"D4违规: 发现{len(illegal_accesses)}处跨域访问({', '.join(desc_set[:3])})")

    def _check_d5_multi_path_generation(self, method_node, source_code: str,
                                         all_methods: List[str]) -> Tuple[float, str]:
        """D5: 多路径生成检测 — 同一区域类型的多个公开生成入口"""
        region_types = {
            'if_then': ['_handle_if_then', '_generate_if_then'],
            'if_else': ['_handle_if_else', '_generate_if_else'],
            'for_loop': ['_handle_for_loop', '_generate_for_loop'],
            'while_loop': ['_handle_while_loop', '_generate_while_loop'],
            'try_except': ['_handle_try_except', '_generate_try_except'],
            'try_finally': ['_handle_try_finally', '_generate_try_finally'],
            'with_block': ['_handle_with', '_generate_with'],
            'comprehension': ['_handle_comprehension', '_generate_comprehension'],
            'function_def': ['_handle_function_def', '_generate_function_def'],
            'class_def': ['_handle_class_def', '_generate_class_def'],
            'sequence': ['_handle_sequence', '_generate_sequence'],
            'ternary': ['_handle_ternary', '_generate_ternary'],
            'lambda': ['_handle_lambda', '_generate_lambda'],
            'if_else_chain': ['_handle_if_else_chain', '_generate_if_else_chain'],
        }
        current_name = method_node.name.lower()
        matched_region = None
        matched_prefixes = []
        for region_type, prefixes in region_types.items():
            for prefix in prefixes:
                if current_name.startswith(prefix):
                    matched_region = region_type
                    matched_prefixes.append(prefix)
        if not matched_region:
            return (1.0, "D5合规: 非区域生成方法")
        same_region_methods = [m for m in all_methods
                               if any(m.lower().startswith(p)
                                      for p in region_types[matched_region])]
        if len(same_region_methods) <= 1:
            return (1.0, f"D5合规: 区域[{matched_region}]只有单一生成入口")
        return (0.0, f"D5违规: 区域[{matched_region}]有{len(same_region_methods)}个生成入口({same_region_methods})")

    def _check_d6_hardcoded_references(self, source_code: str,
                                        start_line: int,
                                        end_line: int) -> Tuple[float, str]:
        """D6: 硬编码引用检测 — 检测操作码名称字符串字面量"""
        lines = source_code.split('\n')
        method_lines = lines[start_line - 1:end_line]
        found_opcodes = set()
        for line in method_lines:
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                continue
            for opcode_name in self.hardcoded_opcodes:
                pattern = rf"['\"]{re.escape(opcode_name)}['\"]"
                if re.search(pattern, stripped):
                    found_opcodes.add(opcode_name)
        if not found_opcodes:
            return (1.0, "D6合规: 无硬编码操作码引用")
        return (0.0, f"D6违规: 发现{len(found_opcodes)}个硬编码操作码({', '.join(sorted(found_opcodes)[:5])})")

    def generate_report(self, verdicts: List[PatchVerdict]) -> str:
        """生成结构化报告"""
        total = len(verdicts)
        patches = [v for v in verdicts if v.is_patch]
        clean = [v for v in verdicts if not v.is_patch]
        avg_scores = {}
        dims = ['d1_score', 'd2_score', 'd3_score', 'd4_score', 'd5_score', 'd6_score']
        for dim in dims:
            vals = [getattr(v, dim) for v in verdicts]
            avg_scores[dim] = sum(vals) / max(len(vals), 1)

        lines = ["=" * 70, "客观补丁检测报告 (Objective Patch Detector v2.0)", "=" * 70, ""]
        lines.append(f"总方法数: {total}")
        lines.append(f"补丁方法: {len(patches)} ({len(patches)/max(total,1)*100:.1f}%)")
        lines.append(f"合规方法: {len(clean)} ({len(clean)/max(total,1)*100:.1f}%)")
        lines.append("")
        lines.append("-" * 70)
        lines.append("各维度平均合规得分:")
        labels = {'d1_score': 'D1算法依据', 'd2_score': 'D2分支数量',
                  'd3_score': 'D3后处理', 'd4_score': 'D4跨域访问',
                  'd5_score': 'D5多路径', 'd6_score': 'D6硬编码'}
        for dim in dims:
            bar_len = int(avg_scores[dim] * 30)
            bar = '#' * bar_len + '-' * (30 - bar_len)
            lines.append(f"  {labels[dim]:12s} [{bar}] {avg_scores[dim]:.2f}")
        lines.append("-" * 70)
        lines.append("")
        if patches:
            lines.append("!" * 70)
            lines.append(f"补丁方法详情 ({len(patches)}个):")
            lines.append("!" * 70)
            for v in sorted(patches, key=lambda x: -x.violation_count):
                lines.append(f"\n  [{v.method_name}] 违规项数: {v.violation_count}/6")
                for detail in v.violation_details:
                    lines.append(f"    - {detail}")
        else:
            lines.append("未检测到补丁方法。所有方法均符合规范。")
        lines.append("")
        lines.append("=" * 70)
        return '\n'.join(lines)
