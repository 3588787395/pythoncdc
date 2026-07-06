"""
增强版自动化补丁检测器

用于检测Python代码中的补丁式编程模式，防止回归到补丁老路。
支持5类违规检测、自动评分、质量门禁和多格式报告输出。

使用方式：
    python patch_detector_enhanced.py file1.py file2.py ...
"""

import ast
import re
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum


class ViolationSeverity(Enum):
    """违规严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationCategory(Enum):
    """违规类别"""
    METHOD_NAME = "method_name"
    COMPLEXITY = "complexity"
    RESPONSIBILITY = "responsibility"
    HARDCODED = "hardcoded"
    POST_PROCESSING = "post_processing"
    LONG_METHOD = "long_method"
    TOO_MANY_METHODS = "too_many_methods"


@dataclass
class Violation:
    """违规记录"""
    category: ViolationCategory
    severity: ViolationSeverity
    file_path: str
    line_number: int
    method_name: str
    description: str
    pattern_matched: str
    score_penalty: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'method_name': self.method_name,
            'description': self.description,
            'pattern_matched': self.pattern_matched,
            'score_penalty': self.score_penalty
        }


@dataclass
class MethodStats:
    """方法统计信息"""
    name: str
    line_start: int
    line_end: int
    line_count: int
    has_if_elif_chain: bool = False
    if_elif_depth: int = 0
    max_if_elif_block_lines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'line_count': self.line_count,
            'has_if_elif_chain': self.has_if_elif_chain,
            'if_elif_depth': self.if_elif_depth,
            'max_if_elif_block_lines': self.max_if_elif_block_lines
        }


@dataclass
class PatchDetectionReport:
    """检测结果报告"""
    file_path: str
    score: int
    violations: List[Violation] = field(default_factory=list)
    method_stats: List[MethodStats] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    quality_gate: str = ""
    detection_time: float = 0.0
    total_methods: int = 0
    total_lines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'score': self.score,
            'violations': [v.to_dict() for v in self.violations],
            'method_stats': [m.to_dict() for m in self.method_stats],
            'recommendations': self.recommendations,
            'quality_gate': self.quality_gate,
            'detection_time': self.detection_time,
            'total_methods': self.total_methods,
            'total_lines': self.total_lines
        }


class EnhancedPatchDetector:
    """
    增强版补丁检测器
    
    检测5类补丁违规模式：
    A. 方法名违规 - 检测补丁式方法命名
    B. 复杂度违规 - 检测过度复杂的方法
    C. 职责违规 - 检测职责混乱
    D. 硬编码违规 - 检测硬编码偏移和块编号
    E. 后处理违规 - 检测后处理修正方法
    """

    PATCH_METHOD_PATTERNS = [
        (r'_fix_', '后处理修正方法 (_fix_)', -5, ViolationSeverity.MEDIUM),
        (r'_merge_', '合并补丁方法 (_merge_)', -5, ViolationSeverity.MEDIUM),
        (r'_patch_', '补丁方法 (_patch_)', -5, ViolationSeverity.HIGH),
        (r'_special_case_', '特殊情况处理 (_special_case_)', -5, ViolationSeverity.MEDIUM),
        (r'_fallback_', '回退逻辑 (_fallback_)', -5, ViolationSeverity.LOW),
        (r'_generate_.*_from_block', '从块生成方法（禁止）(_generate_*_from_block)', -5, ViolationSeverity.HIGH),
        (r'_correct', '修正方法 (_correct)', -5, ViolationSeverity.HIGH),
        (r'_adjust', '调整方法 (_adjust)', -5, ViolationSeverity.MEDIUM),
    ]

    POST_PROCESSING_PATTERNS = [
        (r'(?i)fix', '包含"fix"词汇', -15, ViolationSeverity.HIGH),
        (r'(?i)patch', '包含"patch"词汇', -15, ViolationSeverity.HIGH),
        (r'(?i)correct', '包含"correct"词汇', -15, ViolationSeverity.HIGH),
        (r'(?i)adjust', '包含"adjust"词汇', -15, ViolationSeverity.MEDIUM),
        (r'(?i)workaround', '包含"workaround"词汇', -15, ViolationSeverity.HIGH),
        (r'(?i)hack', '包含"hack"词汇', -15, ViolationSeverity.CRITICAL),
    ]

    HARDCODED_PATTERNS = [
        (r'offset\s*==\s*\d+', '硬编码偏移比较', -20, ViolationSeverity.HIGH),
        (r'block\s*\d+|blocks?\s*\[\d+\]', '硬编码块编号引用', -20, ViolationSeverity.HIGH),
        (r'instruction\s*\[\d+\]|instrs?\s*\[\d+\]', '硬编码指令索引', -20, ViolationSeverity.HIGH),
        (r'\[\d+\]\s*=\s*', '通过数字索引赋值（可能硬编码）', -20, ViolationSeverity.MEDIUM),
    ]

    QUALITY_THRESHOLDS = {
        'excellent': 95,
        'good': 90,
        'acceptable': 80,
    }

    def __init__(self):
        self.violations: List[Violation] = []
        self.method_stats: List[MethodStats] = []
        self.recommendations: List[str] = []

    def detect(self, file_path: str) -> PatchDetectionReport:
        """
        对指定文件执行补丁检测
        
        Args:
            file_path: 要检测的Python文件路径
            
        Returns:
            PatchDetectionReport: 详细检测结果报告
        """
        start_time = time.time()
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"语法错误: {e}")
        
        lines = source_code.split('\n')
        total_lines = len(lines)
        
        self.violations = []
        self.method_stats = []
        self.recommendations = []
        
        self._analyze_file(tree, file_path, lines)
        
        score = self._calculate_score()
        quality_gate = self._determine_quality_gate(score)
        recommendations = self._generate_recommendations()
        
        detection_time = time.time() - start_time
        
        report = PatchDetectionReport(
            file_path=file_path,
            score=score,
            violations=self.violations,
            method_stats=self.method_stats,
            recommendations=recommendations,
            quality_gate=quality_gate,
            detection_time=detection_time,
            total_methods=len(self.method_stats),
            total_lines=total_lines
        )
        
        return report

    def _analyze_file(self, tree: ast.AST, file_path: str, lines: List[str]) -> None:
        """分析文件中的所有类和方法"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                self._analyze_class(node, file_path, lines, class_name)

    def _analyze_class(self, class_node: ast.ClassDef, file_path: str, 
                       lines: List[str], class_name: str) -> None:
        """分析类中的所有方法"""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                self._analyze_method(item, file_path, lines, class_name)

    def _analyze_method(self, method_node: ast.FunctionDef, file_path: str,
                        lines: List[str], class_name: str) -> None:
        """
        分析单个方法的所有违规模式
        
        检测顺序：
        1. 方法名违规 (A)
        2. 复杂度违规 (B)
        3. 职责违规 (C)
        4. 硬编码违规 (D)
        5. 后处理违规 (E)
        """
        method_name = method_node.name
        line_start = method_node.lineno
        line_end = method_node.end_lineno or line_start
        line_count = line_end - line_start + 1
        
        method_stat = MethodStats(
            name=method_name,
            line_start=line_start,
            line_end=line_end,
            line_count=line_count
        )
        
        method_source = '\n'.join(lines[line_start-1:line_end])
        
        self._check_method_name_violations(method_name, file_path, line_start, class_name)
        self._check_complexity_violations(method_node, method_source, file_path, 
                                         line_start, method_name, method_stat)
        self._check_responsibility_violations(method_name, file_path, line_start,
                                             class_name, method_name)
        self._check_hardcoded_violations(method_source, file_path, line_start, 
                                        method_name, class_name)
        self._check_post_processing_violations(method_name, method_source, 
                                              file_path, line_start, class_name)
        
        self.method_stats.append(method_stat)

    def _check_method_name_violations(self, method_name: str, file_path: str,
                                      line_num: int, class_name: str) -> None:
        """A. 检测方法名违规模式"""
        for pattern, desc, penalty, severity in self.PATCH_METHOD_PATTERNS:
            if re.search(pattern, method_name):
                violation = Violation(
                    category=ViolationCategory.METHOD_NAME,
                    severity=severity,
                    file_path=file_path,
                    line_number=line_num,
                    method_name=method_name,
                    description=f"[{class_name}.{method_name}] {desc}",
                    pattern_matched=pattern,
                    score_penalty=penalty
                )
                self.violations.append(violation)

    def _check_complexity_violations(self, method_node: ast.FunctionDef,
                                     method_source: str, file_path: str,
                                     line_num: int, method_name: str,
                                     method_stat: MethodStats) -> None:
        """B. 检测复杂度违规"""
        if_elif_info = self._analyze_if_elif_chains(method_node)
        method_stat.has_if_elif_chain = if_elif_info['has_chain']
        method_stat.if_elif_depth = if_elif_info['depth']
        method_stat.max_if_elif_block_lines = if_elif_info['max_block_lines']
        
        if if_elif_info['has_chain']:
            if if_elif_info['depth'] > 3 and if_elif_info['max_block_lines'] > 20:
                violation = Violation(
                    category=ViolationCategory.COMPLEXITY,
                    severity=ViolationSeverity.HIGH,
                    file_path=file_path,
                    line_number=line_num,
                    method_name=method_name,
                    description=f"if/elif链过深({if_elif_info['depth']}层)且每层过长({if_elif_info['max_block_lines']}行)",
                    pattern_matched=f"if/elif depth={if_elif_info['depth']}",
                    score_penalty=-10
                )
                self.violations.append(violation)
        
        if method_stat.line_count > 300:
            violation = Violation(
                category=ViolationCategory.COMPLEXITY,
                severity=ViolationSeverity.CRITICAL,
                file_path=file_path,
                line_number=line_num,
                method_name=method_name,
                description=f"方法过长: {method_stat.line_count}行 (超过300行限制)",
                pattern_matched=f"lines={method_stat.line_count}",
                score_penalty=-10
            )
            self.violations.append(violation)
        elif method_stat.line_count > 200:
            violation = Violation(
                category=ViolationCategory.LONG_METHOD,
                severity=ViolationSeverity.MEDIUM,
                file_path=file_path,
                line_number=line_num,
                method_name=method_name,
                description=f"方法较长: {method_stat.line_count}行 (超过200行警告线)",
                pattern_matched=f"lines={method_stat.line_count}",
                score_penalty=-3
            )
            self.violations.append(violation)

    def _analyze_if_elif_chains(self, method_node: ast.FunctionDef) -> Dict[str, Any]:
        """分析方法中的if/elif链复杂度"""
        result = {
            'has_chain': False,
            'depth': 0,
            'max_block_lines': 0
        }
        
        for node in ast.walk(method_node):
            if isinstance(node, ast.If):
                depth = 1
                current = node
                while hasattr(current, 'orelse') and current.orelse:
                    if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                        depth += 1
                        current = current.orelse[0]
                    else:
                        break
                
                if depth > result['depth']:
                    result['depth'] = depth
                    result['has_chain'] = depth > 3
                    
                    block_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                    if block_lines > result['max_block_lines']:
                        result['max_block_lines'] = block_lines
        
        return result

    def _check_responsibility_violations(self, method_name: str, file_path: str,
                                        line_num: int, class_name: str,
                                        full_method_name: str) -> None:
        """C. 检测职责违规"""
        is_analyzer = 'analyzer' in class_name.lower()
        is_generator = 'generator' in class_name.lower()
        
        if is_analyzer and re.search(r'^_generate', method_name):
            violation = Violation(
                category=ViolationCategory.RESPONSIBILITY,
                severity=ViolationSeverity.HIGH,
                file_path=file_path,
                line_number=line_num,
                method_name=method_name,
                description=f"[{class_name}] 分析器中包含生成方法: {method_name}，违反单一职责原则",
                pattern_matched='_generate* in analyzer',
                score_penalty=-15
            )
            self.violations.append(violation)
        
        if is_generator and re.search(r'^_identify', method_name):
            violation = Violation(
                category=ViolationCategory.RESPONSIBILITY,
                severity=ViolationSeverity.HIGH,
                file_path=file_path,
                line_number=line_num,
                method_name=method_name,
                description=f"[{class_name}] 生成器中包含识别方法: {method_name}，违反单一职责原则",
                pattern_matched='_identify* in generator',
                score_penalty=-15
            )
            self.violations.append(violation)

    def _check_hardcoded_violations(self, method_source: str, file_path: str,
                                   line_num: int, method_name: str,
                                   class_name: str) -> None:
        """D. 检测硬编码违规"""
        for pattern, desc, penalty, severity in self.HARDCODED_PATTERNS:
            matches = re.finditer(pattern, method_source)
            for match in matches:
                line_in_method = method_source[:match.start()].count('\n') + 1
                actual_line = line_num + line_in_method - 1
                
                violation = Violation(
                    category=ViolationCategory.HARDCODED,
                    severity=severity,
                    file_path=file_path,
                    line_number=actual_line,
                    method_name=method_name,
                    description=f"[{class_name}.{method_name}:{actual_line}] {desc}: {match.group()[:50]}",
                    pattern_matched=pattern,
                    score_penalty=penalty
                )
                self.violations.append(violation)

    def _check_post_processing_violations(self, method_name: str, method_source: str,
                                         file_path: str, line_num: int,
                                         class_name: str) -> None:
        """E. 检测后处理违规"""
        for pattern, desc, penalty, severity in self.POST_PROCESSING_PATTERNS:
            if re.search(pattern, method_name):
                violation = Violation(
                    category=ViolationCategory.POST_PROCESSING,
                    severity=severity,
                    file_path=file_path,
                    line_number=line_num,
                    method_name=method_name,
                    description=f"[{class_name}.{method_name}] 后处理方法: {desc}",
                    pattern_matched=pattern,
                    score_penalty=penalty
                )
                self.violations.append(violation)

    def _calculate_score(self) -> int:
        """计算质量评分 (0-100)"""
        base_score = 100
        
        for violation in self.violations:
            base_score += violation.score_penalty
        
        if len(self.method_stats) > 30:
            base_score -= 10
        
        return max(0, min(100, base_score))

    def _determine_quality_gate(self, score: int) -> str:
        """确定质量门禁等级"""
        if score >= self.QUALITY_THRESHOLDS['excellent']:
            return "✅ 优秀（通过）"
        elif score >= self.QUALITY_THRESHOLDS['good']:
            return "⚠️ 良好（警告）"
        elif score >= self.QUALITY_THRESHOLDS['acceptable']:
            return "❌ 不合格（需改进）"
        else:
            return "🔴 严重（阻止提交）"

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        category_counts = {}
        for v in self.violations:
            cat = v.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if category_counts.get('method_name', 0) > 0:
            recommendations.append("• 重命名包含补丁语义的方法，使用描述性名称")
        
        if category_counts.get('complexity', 0) > 0:
            recommendations.append("• 拆分过长或过于复杂的方法，遵循单一职责原则")
        
        if category_counts.get('responsibility', 0) > 0:
            recommendations.append("• 将识别逻辑和生成逻辑分离到正确的类中")
        
        if category_counts.get('hardcoded', 0) > 0:
            recommendations.append("• 将硬编码的偏移和块编号提取为常量或配置")
        
        if category_counts.get('post_processing', 0) > 0:
            recommendations.append("• 消除后处理修正方法，在识别阶段就正确处理")
        
        if category_counts.get('long_method', 0) > 0:
            recommendations.append("• 考虑将长方法拆分为更小的子方法")
        
        if len(self.method_stats) > 30:
            recommendations.append("• 类的方法数量过多(>30)，考虑拆分为多个类")
        
        if not recommendations:
            recommendations.append("✨ 代码质量优秀，未发现明显的补丁式模式")
        
        return recommendations

    def generate_report(self, reports: List[PatchDetectionReport], 
                       output_format: str = 'text') -> str:
        """
        生成格式化检测报告
        
        Args:
            reports: 检测报告列表
            output_format: 输出格式 ('text'|'json'|'html')
            
        Returns:
            格式化的报告字符串
        """
        if output_format == 'json':
            return self._generate_json_report(reports)
        elif output_format == 'html':
            return self._generate_html_report(reports)
        else:
            return self._generate_text_report(reports)

    def _generate_text_report(self, reports: List[PatchDetectionReport]) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("🔍 增强版补丁检测报告")
        lines.append("=" * 80)
        lines.append("")
        
        total_score = 0
        total_violations = 0
        total_methods = 0
        total_lines = 0
        
        for report in reports:
            lines.append(f"📄 文件: {report.file_path}")
            lines.append("-" * 80)
            lines.append(f"   评分: {report.score}/100")
            lines.append(f"   质量门禁: {report.quality_gate}")
            lines.append(f"   方法数: {report.total_methods}")
            lines.append(f"   总行数: {report.total_lines}")
            lines.append(f"   检测时间: {report.detection_time:.3f}s")
            lines.append("")
            
            if report.violations:
                lines.append(f"   🚨 违规项 ({len(report.violations)}):")
                lines.append("")
                
                for i, v in enumerate(report.violations, 1):
                    severity_icon = {
                        'LOW': '💚',
                        'MEDIUM': '💛',
                        'HIGH': '🧡',
                        'CRITICAL': '💔'
                    }.get(v.severity.value, '⚪')
                    
                    lines.append(f"   {i}. {severity_icon} [{v.severity.value.upper()}] ({v.category.value})")
                    lines.append(f"      方法: {v.method_name}:{v.line_number}")
                    lines.append(f"      说明: {v.description}")
                    lines.append(f"      扣分: {v.score_penalty}")
                    lines.append("")
            else:
                lines.append("   ✅ 未检测到违规")
                lines.append("")
            
            if report.recommendations:
                lines.append("   💡 改进建议:")
                for rec in report.recommendations:
                    lines.append(f"      {rec}")
                lines.append("")
            
            lines.append("")
            
            total_score += report.score
            total_violations += len(report.violations)
            total_methods += report.total_methods
            total_lines += report.total_lines
        
        if len(reports) > 1:
            avg_score = total_score / len(reports)
            lines.append("=" * 80)
            lines.append("📊 汇总统计")
            lines.append("=" * 80)
            lines.append(f"   文件数: {len(reports)}")
            lines.append(f"   平均评分: {avg_score:.1f}/100")
            lines.append(f"   总违规数: {total_violations}")
            lines.append(f"   总方法数: {total_methods}")
            lines.append(f"   总代码行数: {total_lines}")
            lines.append("")
            
            overall_gate = self._determine_quality_gate(int(avg_score))
            lines.append(f"   整体评价: {overall_gate}")
        
        lines.append("=" * 80)
        return '\n'.join(lines)

    def _generate_json_report(self, reports: List[PatchDetectionReport]) -> str:
        """生成JSON格式报告"""
        data = {
            'report_type': 'enhanced_patch_detection',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'files_analyzed': len(reports),
            'reports': [r.to_dict() for r in reports]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _generate_html_report(self, reports: List[PatchDetectionReport]) -> str:
        """生成HTML格式报告"""
        html_parts = []
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>增强版补丁检测报告</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .file-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .score { font-size: 24px; font-weight: bold; }
        .excellent { color: #28a745; }
        .good { color: #ffc107; }
        .acceptable { color: #dc3545; }
        .critical { color: #721c24; }
        .violation { margin: 10px 0; padding: 10px; border-left: 4px solid #dc3545; background: #fff5f5; }
        .violation.low { border-left-color: #28a745; background: #f0fff0; }
        .violation.medium { border-left-color: #ffc107; background: #fffef0; }
        .violation.high { border-left-color: #fd7e14; background: #fff5eb; }
        .violation.critical { border-left-color: #dc3545; background: #fff5f5; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #007acc; color: white; }
        tr:hover { background: #f5f5f5; }
        .recommendation { color: #666; font-style: italic; margin: 5px 0; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-box { flex: 1; padding: 15px; background: #f8f9fa; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; color: #007acc; }
        .stat-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 增强版补丁检测报告</h1>
""")
        
        for report in reports:
            score_class = 'excellent' if report.score >= 95 else 'good' if report.score >= 90 else 'acceptable' if report.score >= 80 else 'critical'
            
            html_parts.append(f"""
        <div class="file-section">
            <h2>📄 {Path(report.file_path).name}</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value {score_class}">{report.score}</div>
                    <div class="stat-label">评分 /100</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{report.total_methods}</div>
                    <div class="stat-label">方法数</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(report.violations)}</div>
                    <div class="stat-label">违规数</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{report.detection_time:.2f}s</div>
                    <div class="stat-label">检测时间</div>
                </div>
            </div>
            <p><strong>质量门禁:</strong> {report.quality_gate}</p>
""")
            
            if report.violations:
                html_parts.append("""
            <h3>🚨 违规详情</h3>
            <table>
                <tr><th>#</th><th>严重程度</th><th>类别</th><th>方法</th><th>说明</th><th>扣分</th></tr>
""")
                for i, v in enumerate(report.violations, 1):
                    html_parts.append(f"""                <tr class="violation {v.severity.value}">
                    <td>{i}</td>
                    <td>{v.severity.value.upper()}</td>
                    <td>{v.category.value}</td>
                    <td>{v.method_name}:{v.line_number}</td>
                    <td>{v.description}</td>
                    <td>{v.score_penalty}</td>
                </tr>
""")
                html_parts.append("            </table>\n")
            
            if report.recommendations:
                html_parts.append("""            <h3>💡 改进建议</h3>
""")
                for rec in report.recommendations:
                    html_parts.append(f'            <p class="recommendation">{rec}</p>\n')
            
            html_parts.append("        </div>\n")
        
        html_parts.append("""    </div>
</body>
</html>""")
        
        return ''.join(html_parts)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python patch_detector_enhanced.py file1.py [file2.py ...]")
        print("选项:")
        print("  --format FORMAT  输出格式 (text|json|html)，默认text")
        print("  --output FILE    输出到文件")
        sys.exit(1)
    
    files = []
    output_format = 'text'
    output_file = None
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--format':
            i += 1
            if i < len(sys.argv):
                output_format = sys.argv[i].lower()
        elif arg == '--output':
            i += 1
            if i < len(sys.argv):
                output_file = sys.argv[i]
        else:
            files.append(arg)
        i += 1
    
    detector = EnhancedPatchDetector()
    reports = []
    
    print(f"\n🔍 开始检测 {len(files)} 个文件...\n")
    
    for file_path in files:
        try:
            print(f"📄 正在分析: {file_path}")
            report = detector.detect(file_path)
            reports.append(report)
            print(f"   ✅ 完成 - 评分: {report.score}/100 | 违规: {len(report.violations)} | 时间: {report.detection_time:.3f}s\n")
        except Exception as e:
            print(f"   ❌ 错误: {e}\n")
    
    if not reports:
        print("没有成功分析的文件")
        sys.exit(1)
    
    report_text = detector.generate_report(reports, output_format)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n📊 报告已保存到: {output_file}")
    else:
        print("\n" + report_text)
    
    all_passed = all(r.score >= 80 for r in reports)
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
