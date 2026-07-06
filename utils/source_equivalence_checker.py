#!/usr/bin/env python3
"""
源代码等效性检查器

用于比较两个Python源代码文件/字符串，检查它们是否语义等价
"""

import ast
import sys
import re
import difflib
import hashlib
from typing import List, Dict, Tuple, Set, Any, Optional, Union
from pathlib import Path
from collections import defaultdict, Counter


class SourceEquivalenceChecker:
    """源代码等效性检查器"""
    
    def __init__(self):
        self.differences = []
        self.original_ast = None
        self.decompiled_ast = None
        self.ignored_node_types = {'Comment', 'Docstring'}
        self.analysis_results = {
            'ast_compatible': False,
            'text_similarity': 0.0,
            'function_equivalence': {},
            'class_equivalence': {},
            'variable_equivalence': {},
            'control_flow_equivalence': {},
            'variable_usage_pattern': {},
            'complexity_metrics': {},
            'semantic_hash': {}
        }
        self.semantic_analysis_enabled = True
        self.strict_mode = False
        self.normalize_names = True
        self.detailed_report = ""
        
    def enable_semantic_analysis(self, enable: bool = True):
        """启用或禁用语义分析"""
        self.semantic_analysis_enabled = enable
        
    def enable_strict_mode(self, enable: bool = True):
        """启用或禁用严格模式"""
        self.strict_mode = enable
        
    def normalize_variable_names(self, enable: bool = True):
        """启用或禁用变量名规范化"""
        self.normalize_names = enable
        
    def analyze_variable_usage(self) -> Dict[str, Any]:
        """分析变量使用模式"""
        if not self.original_ast or not self.decompiled_ast:
            return {}
            
        variable_usage = {}
        
        # 分析原始代码的变量使用
        orig_variables = self._extract_variable_usage(self.original_ast)
        dec_variables = self._extract_variable_usage(self.decompiled_ast)
        
        # 比较变量使用模式
        for var_name in set(list(orig_variables.keys()) + list(dec_variables.keys())):
            orig_usage = orig_variables.get(var_name, {})
            dec_usage = dec_variables.get(var_name, {})
            
            # 如果启用了变量名规范化，使用通用变量名
            if self.normalize_names:
                var_usage_pattern = self._get_variable_usage_pattern(orig_usage)
                dec_var_usage_pattern = self._get_variable_usage_pattern(dec_usage)
            else:
                var_usage_pattern = orig_usage
                dec_var_usage_pattern = dec_usage
            
            # 比较变量使用模式
            is_equivalent = var_usage_pattern == dec_var_usage_pattern
            
            variable_usage[var_name] = {
                'original_usage': orig_usage,
                'decompiled_usage': dec_usage,
                'equivalent': is_equivalent
            }
        
        self.analysis_results['variable_usage_pattern'] = variable_usage
        return variable_usage
        
    def _extract_variable_usage(self, ast_root: ast.AST) -> Dict[str, Dict[str, int]]:
        """从AST中提取变量使用信息"""
        variables = defaultdict(lambda: {'load': 0, 'store': 0, 'delete': 0})
        
        # 递归遍历AST
        self._traverse_ast(ast_root, variables)
        
        return dict(variables)
        
    def _traverse_ast(self, node: ast.AST, variables: Dict[str, Dict[str, int]]):
        """递归遍历AST以提取变量使用信息"""
        for child in ast.iter_child_nodes(node):
            self._traverse_ast(child, variables)
            
            # 检查当前节点是否引用变量
            if isinstance(child, ast.Name):
                # 检查是否为加载操作
                if isinstance(node, ast.Load):
                    variables[child.id]['load'] += 1
                # 检查是否为存储操作
                elif isinstance(node, ast.Store):
                    variables[child.id]['store'] += 1
                # 检查是否为删除操作
                elif isinstance(node, ast.Del):
                    variables[child.id]['delete'] += 1
            elif isinstance(child, ast.Attribute):
                # 处理属性访问
                if isinstance(child.value, ast.Name):
                    # 加载属性
                    if isinstance(node, ast.Load):
                        variables[child.value.id]['load'] += 1
        
    def _get_variable_usage_pattern(self, usage: Dict[str, int]) -> str:
        """获取变量使用模式字符串"""
        # 将使用模式转换为字符串表示
        loads = usage.get('load', 0)
        stores = usage.get('store', 0)
        deletes = usage.get('delete', 0)
        
        # 生成模式字符串
        pattern = f"L{loads}S{stores}D{deletes}"
        return pattern
        
    def analyze_control_flow(self) -> Dict[str, Any]:
        """分析控制流结构"""
        if not self.original_ast or not self.decompiled_ast:
            return {}
            
        control_flow = {
            'original': self._extract_control_flow(self.original_ast),
            'decompiled': self._extract_control_flow(self.decompiled_ast)
        }
        
        # 比较控制流结构
        orig_flow = control_flow['original']
        dec_flow = control_flow['decompiled']
        
        # 比较循环结构
        loops_match = orig_flow['loops'] == dec_flow['loops']
        
        # 比较条件分支结构
        conditionals_match = orig_flow['conditionals'] == dec_flow['conditionals']
        
        # 比较异常处理结构
        exceptions_match = orig_flow['exceptions'] == dec_flow['exceptions']
        
        self.analysis_results['control_flow_equivalence'] = {
            'loops_match': loops_match,
            'conditionals_match': conditionals_match,
            'exceptions_match': exceptions_match,
            'overall_match': loops_match and conditionals_match and exceptions_match
        }
        
        return control_flow
        
    def _extract_control_flow(self, ast_root: ast.AST) -> Dict[str, List[Dict[str, Any]]]:
        """从AST中提取控制流结构"""
        control_flow = {
            'loops': [],
            'conditionals': [],
            'exceptions': []
        }
        
        # 递归遍历AST
        self._traverse_control_flow(ast_root, control_flow)
        
        return control_flow
        
    def _traverse_control_flow(self, node: ast.AST, control_flow: Dict[str, List[Dict[str, Any]]]):
        """递归遍历AST以提取控制流信息"""
        for child in ast.iter_child_nodes(node):
            self._traverse_control_flow(child, control_flow)
            
            # 检测循环结构
            if isinstance(node, ast.For):
                loop_info = {
                    'type': 'for',
                    'target': self._extract_name(child) if isinstance(child, ast.Name) else str(child),
                    'iter': self._extract_name(node.iter) if isinstance(node.iter, ast.Name) else str(node.iter)
                }
                control_flow['loops'].append(loop_info)
            elif isinstance(node, ast.While):
                loop_info = {
                    'type': 'while',
                    'test': self._extract_expression(node.test)
                }
                control_flow['loops'].append(loop_info)
            
            # 检测条件分支结构
            elif isinstance(node, ast.If):
                if_info = {
                    'test': self._extract_expression(node.test),
                    'orelse': len(node.orelse) > 0
                }
                control_flow['conditionals'].append(if_info)
            
            # 检测异常处理结构
            elif isinstance(node, ast.Try):
                try_info = {
                    'handlers': [self._extract_expression(h.type) if h.type else None for h in node.handlers],
                    'orelse': len(node.orelse) > 0,
                    'finalbody': len(node.finalbody) > 0
                }
                control_flow['exceptions'].append(try_info)
                
    def _extract_name(self, node: ast.AST) -> str:
        """提取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_name(node.value)}.{node.attr}"
        else:
            return str(node)
            
    def _extract_expression(self, node: ast.AST) -> str:
        """提取表达式字符串"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._extract_expression(node.left)
            op = self._extract_operator(node.op)
            right = self._extract_expression(node.right)
            return f"({left} {op} {right})"
        elif isinstance(node, ast.UnaryOp):
            op = self._extract_operator(node.op)
            operand = self._extract_expression(node.operand)
            return f"({op}{operand})"
        elif isinstance(node, ast.Call):
            func = self._extract_expression(node.func)
            args = [self._extract_expression(arg) for arg in node.args]
            return f"{func}({', '.join(args)})"
        elif isinstance(node, ast.Attribute):
            value = self._extract_expression(node.value)
            return f"{value}.{node.attr}"
        else:
            return str(node)
            
    def _extract_operator(self, op: ast.AST) -> str:
        """提取操作符字符串"""
        if isinstance(op, ast.Add):
            return "+"
        elif isinstance(op, ast.Sub):
            return "-"
        elif isinstance(op, ast.Mult):
            return "*"
        elif isinstance(op, ast.Div):
            return "/"
        elif isinstance(op, ast.Mod):
            return "%"
        elif isinstance(op, ast.Pow):
            return "**"
        elif isinstance(op, ast.USub):
            return "-"
        elif isinstance(op, ast.UAdd):
            return "+"
        elif isinstance(op, ast.Not):
            return "not "
        else:
            return str(op)
            
    def calculate_complexity_metrics(self) -> Dict[str, Any]:
        """计算代码复杂度指标"""
        if not self.original_ast or not self.decompiled_ast:
            return {}
            
        orig_metrics = self._calculate_ast_complexity(self.original_ast)
        dec_metrics = self._calculate_ast_complexity(self.decompiled_ast)
        
        # 比较复杂度指标
        complexity_match = abs(orig_metrics['cyclomatic'] - dec_metrics['cyclomatic']) < 1 and \
                          abs(orig_metrics['depth'] - dec_metrics['depth']) < 1
        
        self.analysis_results['complexity_metrics'] = {
            'original': orig_metrics,
            'decompiled': dec_metrics,
            'match': complexity_match
        }
        
        return self.analysis_results['complexity_metrics']
        
    def _calculate_ast_complexity(self, ast_root: ast.AST) -> Dict[str, int]:
        """计算AST复杂度指标"""
        metrics = {
            'nodes': 0,
            'edges': 0,
            'cyclomatic': 1,  # 基础复杂度为1
            'depth': 0,
            'functions': 0,
            'classes': 0
        }
        
        # 递归计算AST复杂度
        self._calculate_ast_complexity_recursive(ast_root, metrics, 0)
        
        return metrics
        
    def _calculate_ast_complexity_recursive(self, node: ast.AST, metrics: Dict[str, int], depth: int):
        """递归计算AST复杂度"""
        metrics['nodes'] += 1
        metrics['depth'] = max(metrics['depth'], depth)
        
        # 计算边数（连接数）
        child_count = len(list(ast.iter_child_nodes(node)))
        metrics['edges'] += child_count
        
        # 计算分支因子
        if isinstance(node, ast.If):
            metrics['cyclomatic'] += 1  # if语句增加一个分支
        elif isinstance(node, ast.For):
            metrics['cyclomatic'] += 1  # for循环增加一个分支
        elif isinstance(node, ast.While):
            metrics['cyclomatic'] += 1  # while循环增加一个分支
        elif isinstance(node, ast.Try):
            metrics['cyclomatic'] += len(node.handlers)  # 每个except增加一个分支
        elif isinstance(node, (ast.And, ast.Or)):
            metrics['cyclomatic'] += 1  # 逻辑运算符增加一个分支
            
        # 计算函数和类数量
        if isinstance(node, ast.FunctionDef):
            metrics['functions'] += 1
        elif isinstance(node, ast.ClassDef):
            metrics['classes'] += 1
        
        # 递归处理子节点
        for child in ast.iter_child_nodes(node):
            self._calculate_ast_complexity_recursive(child, metrics, depth + 1)
            
    def compute_semantic_hash(self) -> Dict[str, str]:
        """计算源代码的语义哈希"""
        if not self.original_ast or not self.decompiled_ast:
            return {}
            
        orig_hash = self._compute_ast_hash(self.original_ast)
        dec_hash = self._compute_ast_hash(self.decompiled_ast)
        
        self.analysis_results['semantic_hash'] = {
            'original': orig_hash,
            'decompiled': dec_hash,
            'match': orig_hash == dec_hash
        }
        
        return self.analysis_results['semantic_hash']
        
    def _compute_ast_hash(self, ast_root: ast.AST) -> str:
        """计算AST的语义哈希"""
        # 提取AST的结构化表示
        ast_structure = self._extract_ast_structure(ast_root)
        
        # 计算哈希值
        return hashlib.md5(ast_structure.encode('utf-8')).hexdigest()
        
    def _extract_ast_structure(self, node: ast.AST) -> str:
        """提取AST的结构化表示"""
        # 获取节点类型
        node_type = type(node).__name__
        
        # 提取节点属性
        attrs = []
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                # 处理列表属性
                if value:
                    list_str = "[" + ",".join(self._extract_ast_structure(item) if isinstance(item, ast.AST) else str(item) for item in value) + "]"
                    attrs.append(f"{field}:{list_str}")
            elif isinstance(value, ast.AST):
                # 处理AST子节点
                attrs.append(f"{field}:{self._extract_ast_structure(value)}")
            else:
                # 处理基本值
                if self._should_include_attribute(field, value):
                    attrs.append(f"{field}:{str(value)}")
        
        # 生成结构化表示
        structure = f"{node_type}({','.join(attrs)})"
        return structure
        
    def _should_include_attribute(self, field: str, value: Any) -> bool:
        """判断是否应该包含某个属性"""
        # 在严格模式下，包含所有属性
        if self.strict_mode:
            return True
            
        # 排除不影响语义的属性
        excluded_fields = {
            'col_offset', 'end_col_offset', 'lineno', 'end_lineno'
        }
        
        if field in excluded_fields:
            return False
            
        # 在语义分析模式下，排除一些可能因重构而改变的属性
        if self.semantic_analysis_enabled:
            if field in {'name'}:
                # 在语义分析模式下，函数名和变量名可能不重要
                return False
                
        return True
        
    def generate_detailed_report(self) -> str:
        """生成详细的比较报告"""
        if not self.differences:
            return "源代码完全匹配！"
            
        report = []
        
        # 添加报告标题
        report.append("=" * 80)
        report.append("源代码等效性详细分析报告")
        report.append("=" * 80)
        report.append("")
        
        # 添加总体评估
        is_equivalent = self.analysis_results['ast_compatible'] and self.analysis_results['text_similarity'] >= 0.8
        report.append(f"总体等效性: {'是' if is_equivalent else '否'}")
        report.append(f"AST兼容性: {'是' if self.analysis_results['ast_compatible'] else '否'}")
        report.append(f"文本相似度: {self.analysis_results['text_similarity']:.2%}")
        report.append("")
        
        # 添加语义分析结果
        if self.semantic_analysis_enabled:
            # 变量使用模式分析
            if 'variable_usage_pattern' in self.analysis_results and self.analysis_results['variable_usage_pattern']:
                report.append("变量使用模式分析:")
                var_patterns = self.analysis_results['variable_usage_pattern']
                for var_name, var_info in var_patterns.items():
                    match_status = "匹配" if var_info['equivalent'] else "不匹配"
                    report.append(f"  变量 '{var_name}': {match_status}")
                report.append("")
                
            # 控制流分析
            if 'control_flow_equivalence' in self.analysis_results:
                control_flow = self.analysis_results['control_flow_equivalence']
                report.append("控制流等效性分析:")
                report.append(f"  循环结构: {'匹配' if control_flow['loops_match'] else '不匹配'}")
                report.append(f"  条件分支: {'匹配' if control_flow['conditionals_match'] else '不匹配'}")
                report.append(f"  异常处理: {'匹配' if control_flow['exceptions_match'] else '不匹配'}")
                report.append("")
                
            # 复杂度分析
            if 'complexity_metrics' in self.analysis_results:
                metrics = self.analysis_results['complexity_metrics']
                report.append("代码复杂度分析:")
                report.append(f"  原始代码复杂度: {metrics['original']['cyclomatic']}")
                report.append(f"  反编译代码复杂度: {metrics['decompiled']['cyclomatic']}")
                report.append(f"  复杂度匹配: {'是' if metrics['match'] else '否'}")
                report.append("")
                
            # 语义哈希分析
            if 'semantic_hash' in self.analysis_results:
                hash_info = self.analysis_results['semantic_hash']
                report.append("语义哈希分析:")
                report.append(f"  原始代码哈希: {hash_info['original']}")
                report.append(f"  反编译代码哈希: {hash_info['decompiled']}")
                report.append(f"  哈希匹配: {'是' if hash_info['match'] else '否'}")
                report.append("")
        
        # 添加AST差异详情
        if self.differences:
            report.append("AST差异详情:")
            for i, diff in enumerate(self.differences, 1):
                report.append(f"  {i}. {diff['type']}")
                if 'expected' in diff and 'actual' in diff:
                    report.append(f"     期望: {diff['expected']}")
                    report.append(f"     实际: {diff['actual']}")
                if 'details' in diff and diff['details']:
                    report.append(f"     详情: {diff['details']}")
            report.append("")
        
        # 添加文本差异详情
        if self.analysis_results['text_similarity'] < 0.9:
            report.append("文本差异详情:")
            # 使用difflib生成差异报告
            if self.original_ast and self.decompiled_ast:
                orig_source = ast.unparse(self.original_ast)
                dec_source = ast.unparse(self.decompiled_ast)
                
                diff = list(difflib.unified_diff(
                    orig_source.splitlines(keepends=True),
                    dec_source.splitlines(keepends=True),
                    fromfile='原始代码',
                    tofile='反编译代码',
                    n=3
                ))
                
                for line in diff:
                    report.append(f"  {line.rstrip()}")
        
        self.detailed_report = "\n".join(report)
        return self.detailed_report
        
    def compare_source_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """
        比较两个源代码文件是否等效
        
        Args:
            file1: 第一个文件路径
            file2: 第二个文件路径
            
        Returns:
            包含比较结果的字典
        """
        with open(file1, 'r', encoding='utf-8') as f:
            source1 = f.read()
            
        with open(file2, 'r', encoding='utf-8') as f:
            source2 = f.read()
            
        return self.compare_source_strings(source1, source2)
    
    def compare_source_strings(self, source1: str, source2: str) -> Dict[str, Any]:
        """
        比较两个源代码字符串是否等效
        
        Args:
            source1: 第一个源代码字符串
            source2: 第二个源代码字符串
            
        Returns:
            包含比较结果的字典
        """
        # 解析AST
        self.original_ast = self._safe_parse_ast(source1)
        self.decompiled_ast = self._safe_parse_ast(source2)
        
        # 如果任一解析失败，进行基本的文本比较
        if not self.original_ast or not self.decompiled_ast:
            return self._basic_text_comparison(source1, source2)
        
        # 进行AST级别的比较
        ast_compatible = self._compare_asts(self.original_ast, self.decompiled_ast)
        
        # 进行文本级别的比较
        text_similarity = self._calculate_text_similarity(source1, source2)
        
        # 如果启用了语义分析，进行额外分析
        if self.semantic_analysis_enabled:
            # 分析变量使用模式
            self.analyze_variable_usage()
            
            # 分析控制流结构
            self.analyze_control_flow()
            
            # 计算复杂度指标
            self.calculate_complexity_metrics()
            
            # 计算语义哈希
            self.compute_semantic_hash()
        
        # 综合判断
        is_equivalent = ast_compatible['equivalent'] and text_similarity >= 0.8
        
        # 更新分析结果
        self.analysis_results['ast_compatible'] = ast_compatible['equivalent']
        self.analysis_results['text_similarity'] = text_similarity
        
        return {
            'equivalent': is_equivalent,
            'ast_compatible': ast_compatible,
            'text_similarity': text_similarity,
            'differences': self.differences,
            'analysis_results': self.analysis_results,
            'detailed_report': self.generate_detailed_report()
        }
    
    def _safe_parse_ast(self, source: str) -> Optional[ast.AST]:
        """
        安全地解析源代码为AST
        
        Args:
            source: 源代码字符串
            
        Returns:
            AST对象或None（如果解析失败）
        """
        try:
            return ast.parse(source)
        except SyntaxError as e:
            print(f"AST解析失败: {e}")
            return None
    
    def _basic_text_comparison(self, source1: str, source2: str) -> Dict[str, Any]:
        """
        进行基本的文本比较
        
        Args:
            source1: 第一个源代码字符串
            source2: 第二个源代码字符串
            
        Returns:
            包含比较结果的字典
        """
        similarity = self._calculate_text_similarity(source1, source2)
        
        # 计算基本的相似度
        lines1 = [line.strip() for line in source1.splitlines() if line.strip()]
        lines2 = [line.strip() for line in source2.splitlines() if line.strip()]
        
        return {
            'equivalent': similarity >= 0.9,
            'ast_compatible': {'equivalent': False, 'error': 'AST解析失败'},
            'text_similarity': similarity,
            'differences': [{'type': 'syntax_error', 'description': '无法解析为AST'}]
        }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            相似度值（0-1之间）
        """
        # 规范化文本 - 去除多余空格和换行
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # 使用SequenceMatcher计算相似度
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """
        规范化文本，去除多余空格和注释
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        # 移除注释（# 开头到行末的内容）
        lines = []
        for line in text.splitlines():
            # 查找注释标记
            comment_index = line.find('#')
            if comment_index >= 0:
                # 保留注释前的部分
                line = line[:comment_index]
            lines.append(line)
        
        # 规范化空白字符
        text = '\n'.join(lines)
        text = re.sub(r'\s+', ' ', text)  # 将多个空白字符替换为单个空格
        text = text.strip()
        
        return text
    
    def _compare_asts(self, ast1: ast.AST, ast2: ast.AST) -> Dict[str, Any]:
        """
        比较两个AST是否等价
        
        Args:
            ast1: 第一个AST
            ast2: 第二个AST
            
        Returns:
            包含比较结果的字典
        """
        self.differences = []
        
        # 根级别比较
        if type(ast1) != type(ast2):
            self.differences.append({
                'type': 'root_type_mismatch',
                'expected': type(ast1).__name__,
                'actual': type(ast2).__name__
            })
            return {'equivalent': False, 'differences': self.differences}
        
        # 详细比较根节点
        if isinstance(ast1, ast.Module) and isinstance(ast2, ast.Module):
            return self._compare_module_nodes(ast1, ast2)
        else:
            return self._compare_nodes(ast1, ast2)
    
    def _compare_module_nodes(self, module1: ast.Module, module2: ast.Module) -> Dict[str, Any]:
        """
        比较两个模块节点
        
        Args:
            module1: 第一个模块节点
            module2: 第二个模块节点
            
        Returns:
            包含比较结果的字典
        """
        if len(module1.body) != len(module2.body):
            self.differences.append({
                'type': 'body_length_mismatch',
                'expected': len(module1.body),
                'actual': len(module2.body)
            })
        
        # 比较各个body节点
        for i, (node1, node2) in enumerate(zip(module1.body, module2.body)):
            result = self._compare_nodes(node1, node2)
            if not result['equivalent']:
                self.differences.append({
                    'type': 'body_item_mismatch',
                    'index': i,
                    'expected': type(node1).__name__,
                    'actual': type(node2).__name__,
                    'details': result['differences'] if 'differences' in result else []
                })
        
        return {'equivalent': len(self.differences) == 0, 'differences': self.differences}
    
    def _compare_nodes(self, node1: ast.AST, node2: ast.AST) -> Dict[str, Any]:
        """
        比较两个AST节点
        
        Args:
            node1: 第一个AST节点
            node2: 第二个AST节点
            
        Returns:
            包含比较结果的字典
        """
        if type(node1) != type(node2):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'type_mismatch',
                    'expected': type(node1).__name__,
                    'actual': type(node2).__name__
                }]
            }
        
        # 基于节点类型进行特定比较
        if isinstance(node1, ast.Assign):
            return self._compare_assign_nodes(node1, node2)
        elif isinstance(node1, ast.FunctionDef):
            return self._compare_function_nodes(node1, node2)
        elif isinstance(node1, ast.ClassDef):
            return self._compare_class_nodes(node1, node2)
        elif isinstance(node1, ast.If):
            return self._compare_if_nodes(node1, node2)
        elif isinstance(node1, ast.For):
            return self._compare_for_nodes(node1, node2)
        elif isinstance(node1, ast.While):
            return self._compare_while_nodes(node1, node2)
        elif isinstance(node1, ast.Try):
            return self._compare_try_nodes(node1, node2)
        elif isinstance(node1, ast.Import):
            return self._compare_import_nodes(node1, node2)
        elif isinstance(node1, ast.ImportFrom):
            return self._compare_importfrom_nodes(node1, node2)
        elif isinstance(node1, ast.Expr):
            return self._compare_expr_nodes(node1, node2)
        elif isinstance(node1, ast.Return):
            return self._compare_return_nodes(node1, node2)
        elif isinstance(node1, ast.Break):
            return self._compare_break_nodes(node1, node2)
        elif isinstance(node1, ast.Continue):
            return self._compare_continue_nodes(node1, node2)
        elif isinstance(node1, ast.With):
            return self._compare_with_nodes(node1, node2)
        elif isinstance(node1, ast.Pass):
            return {'equivalent': True}
        elif isinstance(node1, (ast.Constant, ast.Name, ast.Attribute, ast.Call, 
                             ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, 
                             ast.Subscript, ast.List, ast.Tuple, ast.Dict, ast.Set)):
            # 这些是表达式节点，使用通用比较
            return self._compare_expression_nodes(node1, node2)
        else:
            # 对于未知节点类型，进行通用比较
            return self._compare_generic_nodes(node1, node2)
    
    def _compare_generic_nodes(self, node1: ast.AST, node2: ast.AST) -> Dict[str, Any]:
        """
        通用AST节点比较
        
        Args:
            node1: 第一个AST节点
            node2: 第二个AST节点
            
        Returns:
            包含比较结果的字典
        """
        # 获取节点的所有属性
        attrs1 = [attr for attr in dir(node1) if not attr.startswith('_')]
        attrs2 = [attr for attr in dir(node2) if not attr.startswith('_')]
        
        # 比较属性列表
        if set(attrs1) != set(attrs2):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'attribute_mismatch',
                    'expected': set(attrs1),
                    'actual': set(attrs2)
                }]
            }
        
        # 比较属性值
        differences = []
        for attr in attrs1:
            val1 = getattr(node1, attr, None)
            val2 = getattr(node2, attr, None)
            
            if type(val1) != type(val2):
                differences.append({
                    'type': 'attribute_value_mismatch',
                    'attribute': attr,
                    'expected_type': type(val1).__name__,
                    'actual_type': type(val2).__name__
                })
                continue
            
            # 递归比较复杂类型的属性值
            if isinstance(val1, list):
                if len(val1) != len(val2):
                    differences.append({
                        'type': 'attribute_list_length_mismatch',
                        'attribute': attr,
                        'expected_length': len(val1),
                        'actual_length': len(val2)
                    })
                else:
                    for i, (item1, item2) in enumerate(zip(val1, val2)):
                        if isinstance(item1, ast.AST) and isinstance(item2, ast.AST):
                            result = self._compare_nodes(item1, item2)
                            if not result['equivalent']:
                                differences.append({
                                    'type': 'attribute_list_item_mismatch',
                                    'attribute': attr,
                                    'index': i,
                                    'details': result['differences'] if 'differences' in result else []
                                })
            elif isinstance(val1, dict):
                if set(val1.keys()) != set(val2.keys()):
                    differences.append({
                        'type': 'attribute_dict_keys_mismatch',
                        'attribute': attr,
                        'expected_keys': set(val1.keys()),
                        'actual_keys': set(val2.keys())
                    })
                else:
                    for key in val1.keys():
                        val1_item = val1[key]
                        val2_item = val2[key]
                        if isinstance(val1_item, ast.AST) and isinstance(val2_item, ast.AST):
                            result = self._compare_nodes(val1_item, val2_item)
                            if not result['equivalent']:
                                differences.append({
                                    'type': 'attribute_dict_item_mismatch',
                                    'attribute': attr,
                                    'key': key,
                                    'details': result['differences'] if 'differences' in result else []
                                })
            elif isinstance(val1, ast.AST) and isinstance(val2, ast.AST):
                result = self._compare_nodes(val1, val2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'attribute_node_mismatch',
                        'attribute': attr,
                        'details': result['differences'] if 'differences' in result else []
                    })
            elif val1 != val2:
                differences.append({
                    'type': 'attribute_value_mismatch',
                    'attribute': attr,
                    'expected': str(val1),
                    'actual': str(val2)
                })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_assign_nodes(self, node1: ast.Assign, node2: ast.Assign) -> Dict[str, Any]:
        """
        比较两个赋值节点
        
        Args:
            node1: 第一个赋值节点
            node2: 第二个赋值节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较targets
        if len(node1.targets) != len(node2.targets):
            differences.append({
                'type': 'targets_length_mismatch',
                'expected': len(node1.targets),
                'actual': len(node2.targets)
            })
        else:
            for i, (t1, t2) in enumerate(zip(node1.targets, node2.targets)):
                result = self._compare_nodes(t1, t2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'target_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较value
        result = self._compare_nodes(node1.value, node2.value)
        if not result['equivalent']:
            differences.append({
                'type': 'value_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_function_nodes(self, node1: ast.FunctionDef, node2: ast.FunctionDef) -> Dict[str, Any]:
        """
        比较两个函数定义节点
        
        Args:
            node1: 第一个函数定义节点
            node2: 第二个函数定义节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较函数名
        if node1.name != node2.name:
            differences.append({
                'type': 'function_name_mismatch',
                'expected': node1.name,
                'actual': node2.name
            })
        
        # 比较参数
        if len(node1.args.args) != len(node2.args.args):
            differences.append({
                'type': 'args_length_mismatch',
                'expected': len(node1.args.args),
                'actual': len(node2.args.args)
            })
        else:
            for i, (arg1, arg2) in enumerate(zip(node1.args.args, node2.args.args)):
                if arg1.arg != arg2.arg:
                    differences.append({
                        'type': 'arg_mismatch',
                        'index': i,
                        'expected': arg1.arg,
                        'actual': arg2.arg
                    })
        
        # 比较返回值
        if node1.returns != node2.returns:
            if node1.returns is None or node2.returns is None:
                differences.append({
                    'type': 'returns_mismatch',
                    'expected': str(node1.returns),
                    'actual': str(node2.returns)
                })
            else:
                result = self._compare_nodes(node1.returns, node2.returns)
                if not result['equivalent']:
                    differences.append({
                        'type': 'returns_mismatch',
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较函数体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_class_nodes(self, node1: ast.ClassDef, node2: ast.ClassDef) -> Dict[str, Any]:
        """
        比较两个类定义节点
        
        Args:
            node1: 第一个类定义节点
            node2: 第二个类定义节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较类名
        if node1.name != node2.name:
            differences.append({
                'type': 'class_name_mismatch',
                'expected': node1.name,
                'actual': node2.name
            })
        
        # 比较基类
        if len(node1.bases) != len(node2.bases):
            differences.append({
                'type': 'bases_length_mismatch',
                'expected': len(node1.bases),
                'actual': len(node2.bases)
            })
        else:
            for i, (base1, base2) in enumerate(zip(node1.bases, node2.bases)):
                result = self._compare_nodes(base1, base2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'base_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较类体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_if_nodes(self, node1: ast.If, node2: ast.If) -> Dict[str, Any]:
        """
        比较两个If节点
        
        Args:
            node1: 第一个If节点
            node2: 第二个If节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较条件
        result = self._compare_nodes(node1.test, node2.test)
        if not result['equivalent']:
            differences.append({
                'type': 'test_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较主体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较orelse
        if len(node1.orelse) != len(node2.orelse):
            differences.append({
                'type': 'orelse_length_mismatch',
                'expected': len(node1.orelse),
                'actual': len(node2.orelse)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.orelse, node2.orelse)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'orelse_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_for_nodes(self, node1: ast.For, node2: ast.For) -> Dict[str, Any]:
        """
        比较两个For节点
        
        Args:
            node1: 第一个For节点
            node2: 第二个For节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较target
        result = self._compare_nodes(node1.target, node2.target)
        if not result['equivalent']:
            differences.append({
                'type': 'target_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较iter
        result = self._compare_nodes(node1.iter, node2.iter)
        if not result['equivalent']:
            differences.append({
                'type': 'iter_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较主体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较orelse
        if len(node1.orelse) != len(node2.orelse):
            differences.append({
                'type': 'orelse_length_mismatch',
                'expected': len(node1.orelse),
                'actual': len(node2.orelse)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.orelse, node2.orelse)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'orelse_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_while_nodes(self, node1: ast.While, node2: ast.While) -> Dict[str, Any]:
        """
        比较两个While节点
        
        Args:
            node1: 第一个While节点
            node2: 第二个While节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较test
        result = self._compare_nodes(node1.test, node2.test)
        if not result['equivalent']:
            differences.append({
                'type': 'test_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较主体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较orelse
        if len(node1.orelse) != len(node2.orelse):
            differences.append({
                'type': 'orelse_length_mismatch',
                'expected': len(node1.orelse),
                'actual': len(node2.orelse)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.orelse, node2.orelse)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'orelse_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_try_nodes(self, node1: ast.Try, node2: ast.Try) -> Dict[str, Any]:
        """
        比较两个Try节点
        
        Args:
            node1: 第一个Try节点
            node2: 第二个Try节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较主体
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较handlers
        if len(node1.handlers) != len(node2.handlers):
            differences.append({
                'type': 'handlers_length_mismatch',
                'expected': len(node1.handlers),
                'actual': len(node2.handlers)
            })
        else:
            for i, (h1, h2) in enumerate(zip(node1.handlers, node2.handlers)):
                # 比较异常类型
                if h1.type is None and h2.type is None:
                    # 两者都是捕获所有异常
                    pass
                elif h1.type is None or h2.type is None:
                    differences.append({
                        'type': 'handler_type_mismatch',
                        'index': i,
                        'expected': str(h1.type),
                        'actual': str(h2.type)
                    })
                else:
                    result = self._compare_nodes(h1.type, h2.type)
                    if not result['equivalent']:
                        differences.append({
                            'type': 'handler_type_mismatch',
                            'index': i,
                            'details': result['differences'] if 'differences' in result else []
                        })
                
                # 比较异常变量名
                if (h1.name is None) != (h2.name is None):
                    differences.append({
                        'type': 'handler_name_mismatch',
                        'index': i,
                        'expected': str(h1.name),
                        'actual': str(h2.name)
                    })
                elif h1.name is not None and h2.name is not None:
                    if h1.name != h2.name:
                        differences.append({
                            'type': 'handler_name_mismatch',
                            'index': i,
                            'expected': h1.name,
                            'actual': h2.name
                        })
                
                # 比较处理程序体
                if len(h1.body) != len(h2.body):
                    differences.append({
                        'type': 'handler_body_length_mismatch',
                        'index': i,
                        'expected': len(h1.body),
                        'actual': len(h2.body)
                    })
                else:
                    for j, (stmt1, stmt2) in enumerate(zip(h1.body, h2.body)):
                        result = self._compare_nodes(stmt1, stmt2)
                        if not result['equivalent']:
                            differences.append({
                                'type': 'handler_body_stmt_mismatch',
                                'index': i,
                                'stmt_index': j,
                                'expected': type(stmt1).__name__,
                                'actual': type(stmt2).__name__,
                                'details': result['differences'] if 'differences' in result else []
                            })
        
        # 比较orelse
        if len(node1.orelse) != len(node2.orelse):
            differences.append({
                'type': 'orelse_length_mismatch',
                'expected': len(node1.orelse),
                'actual': len(node2.orelse)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.orelse, node2.orelse)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'orelse_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较finalbody
        if len(node1.finalbody) != len(node2.finalbody):
            differences.append({
                'type': 'finalbody_length_mismatch',
                'expected': len(node1.finalbody),
                'actual': len(node2.finalbody)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.finalbody, node2.finalbody)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'finalbody_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_import_nodes(self, node1: ast.Import, node2: ast.Import) -> Dict[str, Any]:
        """
        比较两个Import节点
        
        Args:
            node1: 第一个Import节点
            node2: 第二个Import节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较names
        if len(node1.names) != len(node2.names):
            differences.append({
                'type': 'names_length_mismatch',
                'expected': len(node1.names),
                'actual': len(node2.names)
            })
        else:
            for i, (alias1, alias2) in enumerate(zip(node1.names, node2.names)):
                if alias1.name != alias2.name:
                    differences.append({
                        'type': 'import_name_mismatch',
                        'index': i,
                        'expected': alias1.name,
                        'actual': alias2.name
                    })
                
                if (alias1.asname is None) != (alias2.asname is None):
                    differences.append({
                        'type': 'import_asname_mismatch',
                        'index': i,
                        'expected': str(alias1.asname),
                        'actual': str(alias2.asname)
                    })
                elif alias1.asname is not None and alias2.asname is not None:
                    if alias1.asname != alias2.asname:
                        differences.append({
                            'type': 'import_asname_mismatch',
                            'index': i,
                            'expected': alias1.asname,
                            'actual': alias2.asname
                        })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_importfrom_nodes(self, node1: ast.ImportFrom, node2: ast.ImportFrom) -> Dict[str, Any]:
        """
        比较两个ImportFrom节点
        
        Args:
            node1: 第一个ImportFrom节点
            node2: 第二个ImportFrom节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较module
        if (node1.module is None) != (node2.module is None):
            differences.append({
                'type': 'module_mismatch',
                'expected': str(node1.module),
                'actual': str(node2.module)
            })
        elif node1.module is not None and node2.module is not None:
            if node1.module != node2.module:
                differences.append({
                    'type': 'module_mismatch',
                    'expected': node1.module,
                    'actual': node2.module
                })
        
        # 比较level
        if node1.level != node2.level:
            differences.append({
                'type': 'level_mismatch',
                'expected': node1.level,
                'actual': node2.level
            })
        
        # 比较names
        if len(node1.names) != len(node2.names):
            differences.append({
                'type': 'names_length_mismatch',
                'expected': len(node1.names),
                'actual': len(node2.names)
            })
        else:
            for i, (alias1, alias2) in enumerate(zip(node1.names, node2.names)):
                if alias1.name != alias2.name:
                    differences.append({
                        'type': 'import_name_mismatch',
                        'index': i,
                        'expected': alias1.name,
                        'actual': alias2.name
                    })
                
                if (alias1.asname is None) != (alias2.asname is None):
                    differences.append({
                        'type': 'import_asname_mismatch',
                        'index': i,
                        'expected': str(alias1.asname),
                        'actual': str(alias2.asname)
                    })
                elif alias1.asname is not None and alias2.asname is not None:
                    if alias1.asname != alias2.asname:
                        differences.append({
                            'type': 'import_asname_mismatch',
                            'index': i,
                            'expected': alias1.asname,
                            'actual': alias2.asname
                        })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_expr_nodes(self, node1: ast.Expr, node2: ast.Expr) -> Dict[str, Any]:
        """
        比较两个Expr节点
        
        Args:
            node1: 第一个Expr节点
            node2: 第二个Expr节点
            
        Returns:
            包含比较结果的字典
        """
        return self._compare_nodes(node1.value, node2.value)
    
    def _compare_return_nodes(self, node1: ast.Return, node2: ast.Return) -> Dict[str, Any]:
        """
        比较两个Return节点
        
        Args:
            node1: 第一个Return节点
            node2: 第二个Return节点
            
        Returns:
            包含比较结果的字典
        """
        if (node1.value is None) != (node2.value is None):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'return_value_mismatch',
                    'expected': str(node1.value),
                    'actual': str(node2.value)
                }]
            }
        
        if node1.value is None and node2.value is None:
            return {'equivalent': True}
        
        return self._compare_nodes(node1.value, node2.value)
    
    def _compare_break_nodes(self, node1: ast.Break, node2: ast.Break) -> Dict[str, Any]:
        """
        比较两个Break节点
        
        Args:
            node1: 第一个Break节点
            node2: 第二个Break节点
            
        Returns:
            包含比较结果的字典
        """
        return {'equivalent': True}
    
    def _compare_continue_nodes(self, node1: ast.Continue, node2: ast.Continue) -> Dict[str, Any]:
        """
        比较两个Continue节点
        
        Args:
            node1: 第一个Continue节点
            node2: 第二个Continue节点
            
        Returns:
            包含比较结果的字典
        """
        return {'equivalent': True}
    
    def _compare_with_nodes(self, node1: ast.With, node2: ast.With) -> Dict[str, Any]:
        """
        比较两个With节点
        
        Args:
            node1: 第一个With节点
            node2: 第二个With节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较items
        if len(node1.items) != len(node2.items):
            differences.append({
                'type': 'items_length_mismatch',
                'expected': len(node1.items),
                'actual': len(node2.items)
            })
        else:
            for i, (item1, item2) in enumerate(zip(node1.items, node2.items)):
                # 比较context_expr
                result = self._compare_nodes(item1.context_expr, item2.context_expr)
                if not result['equivalent']:
                    differences.append({
                        'type': 'context_expr_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
                
                # 比较optional_vars
                if (item1.optional_vars is None) != (item2.optional_vars is None):
                    differences.append({
                        'type': 'optional_vars_mismatch',
                        'index': i,
                        'expected': str(item1.optional_vars),
                        'actual': str(item2.optional_vars)
                    })
                elif item1.optional_vars is not None and item2.optional_vars is not None:
                    result = self._compare_nodes(item1.optional_vars, item2.optional_vars)
                    if not result['equivalent']:
                        differences.append({
                            'type': 'optional_vars_mismatch',
                            'index': i,
                            'details': result['differences'] if 'differences' in result else []
                        })
        
        # 比较body
        if len(node1.body) != len(node2.body):
            differences.append({
                'type': 'body_length_mismatch',
                'expected': len(node1.body),
                'actual': len(node2.body)
            })
        else:
            for i, (stmt1, stmt2) in enumerate(zip(node1.body, node2.body)):
                result = self._compare_nodes(stmt1, stmt2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'body_stmt_mismatch',
                        'index': i,
                        'expected': type(stmt1).__name__,
                        'actual': type(stmt2).__name__,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_expression_nodes(self, node1: ast.AST, node2: ast.AST) -> Dict[str, Any]:
        """
        比较两个表达式节点
        
        Args:
            node1: 第一个表达式节点
            node2: 第二个表达式节点
            
        Returns:
            包含比较结果的字典
        """
        if type(node1) != type(node2):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'expression_type_mismatch',
                    'expected': type(node1).__name__,
                    'actual': type(node2).__name__
                }]
            }
        
        # 基于表达式类型进行特定比较
        if isinstance(node1, ast.Constant):
            return self._compare_constant_nodes(node1, node2)
        elif isinstance(node1, ast.Name):
            return self._compare_name_nodes(node1, node2)
        elif isinstance(node1, ast.Attribute):
            return self._compare_attribute_nodes(node1, node2)
        elif isinstance(node1, ast.Call):
            return self._compare_call_nodes(node1, node2)
        elif isinstance(node1, ast.BinOp):
            return self._compare_binop_nodes(node1, node2)
        elif isinstance(node1, ast.UnaryOp):
            return self._compare_unaryop_nodes(node1, node2)
        elif isinstance(node1, ast.BoolOp):
            return self._compare_boolop_nodes(node1, node2)
        elif isinstance(node1, ast.Compare):
            return self._compare_compare_nodes(node1, node2)
        elif isinstance(node1, ast.Subscript):
            return self._compare_subscript_nodes(node1, node2)
        elif isinstance(node1, ast.List):
            return self._compare_list_nodes(node1, node2)
        elif isinstance(node1, ast.Tuple):
            return self._compare_tuple_nodes(node1, node2)
        elif isinstance(node1, ast.Dict):
            return self._compare_dict_nodes(node1, node2)
        elif isinstance(node1, ast.Set):
            return self._compare_set_nodes(node1, node2)
        else:
            # 对于未处理的表达式类型，使用通用比较
            return self._compare_generic_nodes(node1, node2)
    
    def _compare_constant_nodes(self, node1: ast.Constant, node2: ast.Constant) -> Dict[str, Any]:
        """
        比较两个常量节点
        
        Args:
            node1: 第一个常量节点
            node2: 第二个常量节点
            
        Returns:
            包含比较结果的字典
        """
        if node1.value != node2.value:
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'constant_value_mismatch',
                    'expected': str(node1.value),
                    'actual': str(node2.value)
                }]
            }
        
        return {'equivalent': True}
    
    def _compare_name_nodes(self, node1: ast.Name, node2: ast.Name) -> Dict[str, Any]:
        """
        比较两个Name节点
        
        Args:
            node1: 第一个Name节点
            node2: 第二个Name节点
            
        Returns:
            包含比较结果的字典
        """
        if node1.id != node2.id:
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'name_id_mismatch',
                    'expected': node1.id,
                    'actual': node2.id
                }]
            }
        
        return {'equivalent': True}
    
    def _compare_attribute_nodes(self, node1: ast.Attribute, node2: ast.Attribute) -> Dict[str, Any]:
        """
        比较两个Attribute节点
        
        Args:
            node1: 第一个Attribute节点
            node2: 第二个Attribute节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较attr
        if node1.attr != node2.attr:
            differences.append({
                'type': 'attribute_attr_mismatch',
                'expected': node1.attr,
                'actual': node2.attr
            })
        
        # 比较value
        result = self._compare_nodes(node1.value, node2.value)
        if not result['equivalent']:
            differences.append({
                'type': 'attribute_value_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_call_nodes(self, node1: ast.Call, node2: ast.Call) -> Dict[str, Any]:
        """
        比较两个Call节点
        
        Args:
            node1: 第一个Call节点
            node2: 第二个Call节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较func
        result = self._compare_nodes(node1.func, node2.func)
        if not result['equivalent']:
            differences.append({
                'type': 'call_func_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较args
        if len(node1.args) != len(node2.args):
            differences.append({
                'type': 'args_length_mismatch',
                'expected': len(node1.args),
                'actual': len(node2.args)
            })
        else:
            for i, (arg1, arg2) in enumerate(zip(node1.args, node2.args)):
                result = self._compare_nodes(arg1, arg2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'arg_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        # 比较keywords
        if len(node1.keywords) != len(node2.keywords):
            differences.append({
                'type': 'keywords_length_mismatch',
                'expected': len(node1.keywords),
                'actual': len(node2.keywords)
            })
        else:
            for i, (kw1, kw2) in enumerate(zip(node1.keywords, node2.keywords)):
                if kw1.arg != kw2.arg:
                    differences.append({
                        'type': 'keyword_arg_mismatch',
                        'index': i,
                        'expected': kw1.arg,
                        'actual': kw2.arg
                    })
                
                result = self._compare_nodes(kw1.value, kw2.value)
                if not result['equivalent']:
                    differences.append({
                        'type': 'keyword_value_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_binop_nodes(self, node1: ast.BinOp, node2: ast.BinOp) -> Dict[str, Any]:
        """
        比较两个BinOp节点
        
        Args:
            node1: 第一个BinOp节点
            node2: 第二个BinOp节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较op
        if type(node1.op) != type(node2.op):
            differences.append({
                'type': 'binop_op_mismatch',
                'expected': type(node1.op).__name__,
                'actual': type(node2.op).__name__
            })
        
        # 比较left
        result = self._compare_nodes(node1.left, node2.left)
        if not result['equivalent']:
            differences.append({
                'type': 'binop_left_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较right
        result = self._compare_nodes(node1.right, node2.right)
        if not result['equivalent']:
            differences.append({
                'type': 'binop_right_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_unaryop_nodes(self, node1: ast.UnaryOp, node2: ast.UnaryOp) -> Dict[str, Any]:
        """
        比较两个UnaryOp节点
        
        Args:
            node1: 第一个UnaryOp节点
            node2: 第二个UnaryOp节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较op
        if type(node1.op) != type(node2.op):
            differences.append({
                'type': 'unaryop_op_mismatch',
                'expected': type(node1.op).__name__,
                'actual': type(node2.op).__name__
            })
        
        # 比较operand
        result = self._compare_nodes(node1.operand, node2.operand)
        if not result['equivalent']:
            differences.append({
                'type': 'unaryop_operand_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_boolop_nodes(self, node1: ast.BoolOp, node2: ast.BoolOp) -> Dict[str, Any]:
        """
        比较两个BoolOp节点
        
        Args:
            node1: 第一个BoolOp节点
            node2: 第二个BoolOp节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较op
        if type(node1.op) != type(node2.op):
            differences.append({
                'type': 'boolop_op_mismatch',
                'expected': type(node1.op).__name__,
                'actual': type(node2.op).__name__
            })
        
        # 比较values
        if len(node1.values) != len(node2.values):
            differences.append({
                'type': 'values_length_mismatch',
                'expected': len(node1.values),
                'actual': len(node2.values)
            })
        else:
            for i, (val1, val2) in enumerate(zip(node1.values, node2.values)):
                result = self._compare_nodes(val1, val2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'value_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_compare_nodes(self, node1: ast.Compare, node2: ast.Compare) -> Dict[str, Any]:
        """
        比较两个Compare节点
        
        Args:
            node1: 第一个Compare节点
            node2: 第二个Compare节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较left
        result = self._compare_nodes(node1.left, node2.left)
        if not result['equivalent']:
            differences.append({
                'type': 'compare_left_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较ops
        if len(node1.ops) != len(node2.ops):
            differences.append({
                'type': 'ops_length_mismatch',
                'expected': len(node1.ops),
                'actual': len(node2.ops)
            })
        else:
            for i, (op1, op2) in enumerate(zip(node1.ops, node2.ops)):
                if type(op1) != type(op2):
                    differences.append({
                        'type': 'op_mismatch',
                        'index': i,
                        'expected': type(op1).__name__,
                        'actual': type(op2).__name__
                    })
        
        # 比较comparators
        if len(node1.comparators) != len(node2.comparators):
            differences.append({
                'type': 'comparators_length_mismatch',
                'expected': len(node1.comparators),
                'actual': len(node2.comparators)
            })
        else:
            for i, (comp1, comp2) in enumerate(zip(node1.comparators, node2.comparators)):
                result = self._compare_nodes(comp1, comp2)
                if not result['equivalent']:
                    differences.append({
                        'type': 'comparator_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_subscript_nodes(self, node1: ast.Subscript, node2: ast.Subscript) -> Dict[str, Any]:
        """
        比较两个Subscript节点
        
        Args:
            node1: 第一个Subscript节点
            node2: 第二个Subscript节点
            
        Returns:
            包含比较结果的字典
        """
        differences = []
        
        # 比较value
        result = self._compare_nodes(node1.value, node2.value)
        if not result['equivalent']:
            differences.append({
                'type': 'subscript_value_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        # 比较slice
        result = self._compare_nodes(node1.slice, node2.slice)
        if not result['equivalent']:
            differences.append({
                'type': 'subscript_slice_mismatch',
                'details': result['differences'] if 'differences' in result else []
            })
        
        return {'equivalent': len(differences) == 0, 'differences': differences}
    
    def _compare_list_nodes(self, node1: ast.List, node2: ast.List) -> Dict[str, Any]:
        """
        比较两个List节点
        
        Args:
            node1: 第一个List节点
            node2: 第二个List节点
            
        Returns:
            包含比较结果的字典
        """
        if len(node1.elts) != len(node2.elts):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'list_length_mismatch',
                    'expected': len(node1.elts),
                    'actual': len(node2.elts)
                }]
            }
        
        for i, (elt1, elt2) in enumerate(zip(node1.elts, node2.elts)):
            result = self._compare_nodes(elt1, elt2)
            if not result['equivalent']:
                return {
                    'equivalent': False,
                    'differences': [{
                        'type': 'list_element_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    }]
                }
        
        return {'equivalent': True}
    
    def _compare_tuple_nodes(self, node1: ast.Tuple, node2: ast.Tuple) -> Dict[str, Any]:
        """
        比较两个Tuple节点
        
        Args:
            node1: 第一个Tuple节点
            node2: 第二个Tuple节点
            
        Returns:
            包含比较结果的字典
        """
        if len(node1.elts) != len(node2.elts):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'tuple_length_mismatch',
                    'expected': len(node1.elts),
                    'actual': len(node2.elts)
                }]
            }
        
        for i, (elt1, elt2) in enumerate(zip(node1.elts, node2.elts)):
            result = self._compare_nodes(elt1, elt2)
            if not result['equivalent']:
                return {
                    'equivalent': False,
                    'differences': [{
                        'type': 'tuple_element_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    }]
                }
        
        return {'equivalent': True}
    
    def _compare_dict_nodes(self, node1: ast.Dict, node2: ast.Dict) -> Dict[str, Any]:
        """
        比较两个Dict节点
        
        Args:
            node1: 第一个Dict节点
            node2: 第二个Dict节点
            
        Returns:
            包含比较结果的字典
        """
        if len(node1.keys) != len(node2.keys):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'dict_length_mismatch',
                    'expected': len(node1.keys),
                    'actual': len(node2.keys)
                }]
            }
        
        for i, (key1, key2, val1, val2) in enumerate(zip(node1.keys, node2.keys, node1.values, node2.values)):
            # 比较key
            key_result = self._compare_nodes(key1, key2)
            if not key_result['equivalent']:
                return {
                    'equivalent': False,
                    'differences': [{
                        'type': 'dict_key_mismatch',
                        'index': i,
                        'details': key_result['differences'] if 'differences' in key_result else []
                    }]
                }
            
            # 比较value
            val_result = self._compare_nodes(val1, val2)
            if not val_result['equivalent']:
                return {
                    'equivalent': False,
                    'differences': [{
                        'type': 'dict_value_mismatch',
                        'index': i,
                        'details': val_result['differences'] if 'differences' in val_result else []
                    }]
                }
        
        return {'equivalent': True}
    
    def _compare_set_nodes(self, node1: ast.Set, node2: ast.Set) -> Dict[str, Any]:
        """
        比较两个Set节点
        
        Args:
            node1: 第一个Set节点
            node2: 第二个Set节点
            
        Returns:
            包含比较结果的字典
        """
        if len(node1.elts) != len(node2.elts):
            return {
                'equivalent': False,
                'differences': [{
                    'type': 'set_length_mismatch',
                    'expected': len(node1.elts),
                    'actual': len(node2.elts)
                }]
            }
        
        for i, (elt1, elt2) in enumerate(zip(node1.elts, node2.elts)):
            result = self._compare_nodes(elt1, elt2)
            if not result['equivalent']:
                return {
                    'equivalent': False,
                    'differences': [{
                        'type': 'set_element_mismatch',
                        'index': i,
                        'details': result['differences'] if 'differences' in result else []
                    }]
                }
        
        return {'equivalent': True}


def compare_source_code(original: str, generated: str) -> bool:
    """
    简化的源代码比较函数
    
    Args:
        original: 原始源代码字符串
        generated: 生成的源代码字符串
        
    Returns:
        源代码是否等效
    """
    checker = SourceEquivalenceChecker()
    result = checker.compare_source_strings(original, generated)
    return result['equivalent']


def main():
    """主函数，用于测试"""
    # 测试用例
    test_cases = [
        {
            'name': 'simple_assignment',
            'original': 'x = 10\ny = 20\nprint(x + y)',
            'generated': 'x = 10\ny = 20\nprint(x + y)'
        },
        {
            'name': 'function_definition',
            'original': 'def add(a, b):\n    return a + b\n\nresult = add(5, 3)',
            'generated': 'def add(a, b):\n    return a + b\n\nresult = add(5, 3)'
        },
        {
            'name': 'class_definition',
            'original': 'class Calculator:\n    def add(self, a, b):\n        return a + b\n\ncalc = Calculator()',
            'generated': 'class Calculator:\n    def add(self, a, b):\n        return a + b\n\ncalc = Calculator()'
        }
    ]
    
    # 运行测试
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"原始代码: {test_case['original']}")
        print(f"生成代码: {test_case['generated']}")
        
        result = compare_source_code(test_case['original'], test_case['generated'])
        print(f"等效性: {'等效' if result else '不等效'}")
        print("-" * 60)


if __name__ == '__main__':
    main()