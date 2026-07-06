"""
方法创建审批流程模块 (METHOD_REVIEW_CHECKLIST)

定义补丁判定标准和方法创建审批规则。
提供补丁检测扫描函数。

用法:
    import METHOD_REVIEW_CHECKLIST as checklist

    patches = checklist.scan_for_patches("core/cfg/region_ast_generator.py")
    all_patches = checklist.scan_directory("core/cfg")
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path


# ============================================================================
# 32.1 方法创建6项必答问题
# ============================================================================

_METHOD_CREATION_QUESTIONS_RAW = [
    {
        "id": 1,
        "question": "该方法属于哪个区域类型？",
        "options": ["If", "Loop", "Try", "With", "Match", "BoolOp", "Ternary", "Sequence", "Basic"],
        "rule": "必须明确归属一种区域类型，不能跨类型处理",
        "rationale": "每个方法只能处理一种区域类型，确保职责单一",
        "validation": "检查方法签名和内部逻辑是否只涉及一种 Region 子类",
    },
    {
        "id": 2,
        "question": "该方法是识别方法还是生成方法？",
        "options": ["识别方法 (Identification)", "生成方法 (Generation)"],
        "rule": "只能二选一，不能同时包含识别和生成逻辑",
        "rationale": "识别和生成是正交的两个阶段，混合会导致耦合",
        "validation": "识别方法应只在 region_analyzer.py 中，生成方法应只在 region_ast_generator.py 中",
    },
    {
        "id": 3,
        "question": "该方法使用什么算法替代了模式匹配？",
        "options": ["回边检测", "支配树分析", "后支配者分析", "异常表解析", "区间包含分析", "其他结构化算法"],
        "rule": "必须基于编译器理论的结构化算法，禁止使用启发式模式匹配",
        "rationale": "算法驱动的识别具有可证明的正确性，模式匹配依赖经验且不完整",
        "validation": "检查方法是否依赖明确的图论/编译器数据结构而非字节码特征匹配",
    },
    {
        "id": 4,
        "question": "该方法能否处理任意嵌套层次？",
        "options": ["是 - 支持任意深度嵌套", "否 - 有限制"],
        "rule": "不能有限制嵌套深度的硬编码，必须通过递归或迭代通用处理",
        "rationale": "Python 允许任意深度嵌套，硬编码深度限制会导致深层代码反编译失败",
        "validation": "检查是否有嵌套层数计数器或栈深度限制的硬编码",
    },
    {
        "id": 5,
        "question": "该方法是否跨域获取信息？",
        "options": ["否 - 仅通过标准接口获取", "是 - 存在跨域访问"],
        "rule": "只能通过父域/子域/前域/后域间接获取信息，不能直接操作其他分析器的内部状态",
        "rationale": "跨域直接访问破坏模块边界，导致变更影响范围不可控",
        "validation": "检查是否访问了非本模块的数据结构（如生成器访问 dominator_analyzer 内部状态）",
    },
    {
        "id": 6,
        "question": "该区域类型是否已有识别/生成方法？",
        "options": ["否 - 这是首个方法", "是 - 已存在同名或同功能方法"],
        "rule": "每种区域类型只能有1个识别方法和1个生成方法",
        "rationale": "多个方法处理同一类型会导致行为不一致和调用混淆",
        "validation": "搜索同类型区域的其他 _identify_* / _generate_* 方法",
    },
]


class MethodCreationQuestion:
    def __init__(self, id: int, question: str, options: List[str],
                 rule: str, rationale: str, validation: str):
        self.id = id
        self.question = question
        self.options = options
        self.rule = rule
        self.rationale = rationale
        self.validation = validation

    def __repr__(self):
        return f"Q{self.id}: {self.question}"


METHOD_CREATION_QUESTIONS = [
    MethodCreationQuestion(**q) for q in _METHOD_CREATION_QUESTIONS_RAW
]


# ============================================================================
# 32.2 补丁判定标准（6项代码特征）
# ============================================================================

_PATCH_INDICATORS_RAW = [
    {
        "id": 1,
        "name": "补丁式方法命名",
        "pattern": r'_fix_|_merge_|_patch_|_fallback_|_workaround_',
        "detection": "方法名包含上述前缀",
        "severity": "FAIL",
        "explanation": "方法名中的补丁前缀表明该方法是为修复问题而添加，而非结构化的设计方案。\n"
                       "应使用描述性的算法名称替代。",
    },
    {
        "id": 2,
        "name": "后处理修正",
        "pattern": r'region\.(blocks|type|body_blocks)\s*=|region\.body_blocks\.(add|remove|discard)\s*\(',
        "detection": "在 _build_region_hierarchy 之后修改已识别区域的属性",
        "severity": "FAIL",
        "explanation": "在区域识别完成后修改区域属性表明原始识别逻辑不完整。\n"
                       "区域属性应在构造时一次性正确设置，不应在后续阶段修正。",
    },
    {
        "id": 3,
        "name": "特殊情况分支",
        "pattern": r'if\s+.+\s*==\s*\d+\s*:|elif\s+.+\s*==\s*\d+\s*:',
        "detection": "为特定偏移或操作码添加 if/elif 特例分支",
        "severity": "WARN",
        "explanation": "针对特定数值的特例分支表明算法不通用。\n"
                       "应使用数据结构驱动的方法替代硬编码的数值比较。",
    },
    {
        "id": 4,
        "name": "跨职责逻辑",
        "pattern": r'self\.(loop_analyzer|dominator|dom_analyzer)|get_block_by_offset|'
                   r'def\s+(_is_|_has_|_check_|_detect_|_find_|_collect_|_extract_)\w*',
        "detection": "生成器代码中包含分析逻辑，或分析器代码中包含生成逻辑",
        "severity": "WARN",
        "explanation": "生成器和分析器的职责应严格分离。\n"
                       "生成器中出现分析语义方法名表明职责混合。",
    },
    {
        "id": 5,
        "name": "多入口生成",
        "pattern": r'同一 RegionType 对应多个 _generate_* 方法|_try_generate_\w+',
        "detection": "同一结构类型有多个生成方法入口",
        "severity": "FAIL",
        "explanation": "每种区域类型应只有一个公共生成入口。\n"
                       "多入口表明存在回退或尝试机制，这不是结构化设计。",
    },
    {
        "id": 6,
        "name": "\"关键修复\"标记",
        "pattern": r'关键修复',
        "detection": "代码注释中出现 \"关键修复\" 字样",
        "severity": "WARN",
        "explanation": "\"关键修复\"注释表明该代码是为紧急修复而添加的补丁。\n"
                       "应将该修复纳入结构化方案。",
    },
]


class PatchIndicator:
    def __init__(self, id: int, name: str, pattern: str, detection: str,
                 severity: str, explanation: str):
        self.id = id
        self.name = name
        self.pattern = pattern
        self.detection = detection
        self.severity = severity
        self.explanation = explanation

    def __repr__(self):
        return f"I{self.id}: {self.name} [{self.severity}]"


PATCH_INDICATORS = [
    PatchIndicator(**p) for p in _PATCH_INDICATORS_RAW
]


# ============================================================================
# 32.3 补丁检测函数
# ============================================================================

@dataclass
class PatchResult:
    indicator_id: int
    indicator_name: str
    file_path: str
    line: int
    severity: str
    description: str
    context: str = ""


@dataclass
class PatchReport:
    file_path: str
    results: List[PatchResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=lambda: {"FAIL": 0, "WARN": 0})

    @property
    def clean(self) -> bool:
        return len(self.results) == 0


def scan_for_patches(filepath: str) -> PatchReport:
    """
    扫描单个文件中的补丁特征。

    Args:
        filepath: 文件路径

    Returns:
        PatchReport 包含所有检测到的补丁特征
    """
    path = Path(filepath)
    if not path.exists():
        return PatchReport(file_path=filepath)

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return PatchReport(file_path=filepath)

    report = PatchReport(file_path=str(path))
    indicators_map = {ind.id: ind for ind in PATCH_INDICATORS}

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        _detect_indicator_1(lines, i, stripped, report, indicators_map)
        _detect_indicator_2(lines, i, stripped, report, indicators_map)
        _detect_indicator_3(lines, i, stripped, report, indicators_map)
        _detect_indicator_4(lines, i, stripped, report, indicators_map)
        _detect_indicator_5(lines, i, stripped, report, indicators_map)
        _detect_indicator_6(lines, i, stripped, report, indicators_map)

    for r in report.results:
        report.summary[r.severity] += 1

    return report


def _detect_indicator_1(lines, i, stripped, report, indicators_map):
    ind = indicators_map[1]
    m = re.match(r'\s*def\s+_\w*('
                 r'fix_|merge_|patch_|fallback_|workaround_'
                 r')\w*\s*\(', stripped)
    if m:
        report.results.append(PatchResult(
            indicator_id=1,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description=f"方法名包含补丁前缀: {m.group(0).strip()}",
            context=stripped,
        ))


def _detect_indicator_2(lines, i, stripped, report, indicators_map):
    ind = indicators_map[2]
    if re.search(r'(?<!\w)region\s*\.\s*blocks\s*=(?!\s*=)', stripped):
        if not _is_region_initialization(lines, i):
            report.results.append(PatchResult(
                indicator_id=2,
                indicator_name=ind.name,
                file_path=report.file_path,
                line=i,
                severity=ind.severity,
                description="region.blocks 赋值操作",
                context=stripped,
            ))
    if re.search(r'(?<!\w)region\s*\.\s*type\s*=(?!\s*=)', stripped):
        if not _is_region_initialization(lines, i):
            report.results.append(PatchResult(
                indicator_id=2,
                indicator_name=ind.name,
                file_path=report.file_path,
                line=i,
                severity=ind.severity,
                description="region.type 赋值操作",
                context=stripped,
            ))
    if re.search(r'(?<!\w)region\s*\.\s*body_blocks\s*\.\s*(add|remove|discard)\s*\(', stripped):
        report.results.append(PatchResult(
            indicator_id=2,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description=f"region.body_blocks 修改操作",
            context=stripped,
        ))
    if re.search(r'(?<!\w)region\s*\.\s*body_blocks\s*=(?!\s*=)', stripped):
        if not _is_region_initialization(lines, i):
            report.results.append(PatchResult(
                indicator_id=2,
                indicator_name=ind.name,
                file_path=report.file_path,
                line=i,
                severity=ind.severity,
                description="region.body_blocks 赋值操作",
                context=stripped,
            ))


def _detect_indicator_3(lines, i, stripped, report, indicators_map):
    ind = indicators_map[3]
    if stripped.startswith("#"):
        return
    if "range(" in stripped or "len(" in stripped or "enumerate(" in stripped:
        return
    offsets = re.findall(
        r'\b(?:offset|block_id|argval)\s*==\s*(\d+)\b',
        stripped
    )
    if offsets:
        report.results.append(PatchResult(
            indicator_id=3,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description=f"硬编码偏移/ID比较: offset/block_id == {offsets[0]}",
            context=stripped,
        ))


def _detect_indicator_4(lines, i, stripped, report, indicators_map):
    ind = indicators_map[4]
    if stripped.startswith("#"):
        return

    if re.search(r'self\.loop_analyzer|self\.dominator[^_]|self\.dom_analyzer',
                 stripped):
        report.results.append(PatchResult(
            indicator_id=4,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description="代码中引用了分析器实例",
            context=stripped,
        ))

    if re.search(r'self\.cfg\.get_block_by_offset\s*\(', stripped):
        report.results.append(PatchResult(
            indicator_id=4,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description="直接操作CFG底层API: get_block_by_offset()",
            context=stripped,
        ))


def _detect_indicator_5(lines, i, stripped, report, indicators_map):
    ind = indicators_map[5]
    m = re.match(r'\s*def\s+(_try_generate_\w+)\s*\(', stripped)
    if m:
        report.results.append(PatchResult(
            indicator_id=5,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description=f"回退式生成方法: {m.group(1)}",
            context=stripped,
        ))

    if re.search(r'_try_generate_\w+\s*\(', stripped) and "def " not in stripped:
        report.results.append(PatchResult(
            indicator_id=5,
            indicator_name=ind.name,
            file_path=report.file_path,
            line=i,
            severity=ind.severity,
            description="调用了回退式生成方法 _try_generate_*",
            context=stripped,
        ))


def _detect_indicator_6(lines, i, stripped, report, indicators_map):
    ind = indicators_map[6]
    if stripped.startswith("#"):
        if "关键修复" in stripped:
            report.results.append(PatchResult(
                indicator_id=6,
                indicator_name=ind.name,
                file_path=report.file_path,
                line=i,
                severity=ind.severity,
                description="注释中出现 \"关键修复\" 标记",
                context=stripped,
            ))


def _is_region_initialization(lines: List[str], line_num: int) -> bool:
    start = max(0, line_num - 8)
    context = "".join(lines[start:line_num])
    markers = [
        "= LoopRegion(", "= IfRegion(", "= TryExceptRegion(",
        "= WithRegion(", "= MatchRegion(", "= AssertRegion(",
        "= BoolOpRegion(", "= TernaryRegion(",
    ]
    return any(m in context for m in markers)


def scan_directory(directory: str, patterns: Optional[List[str]] = None) -> List[PatchReport]:
    """
    扫描目录中所有Python文件的补丁特征。

    Args:
        directory: 目录路径
        patterns: 文件glob模式列表，默认 ["*.py"]

    Returns:
        List[PatchReport] 每个文件的补丁报告
    """
    if patterns is None:
        patterns = ["*.py"]

    reports: List[PatchReport] = []
    root = Path(directory)

    if not root.exists():
        return reports

    for pattern in patterns:
        for filepath in root.rglob(pattern):
            if filepath.is_file():
                report = scan_for_patches(str(filepath))
                if not report.clean:
                    reports.append(report)

    return reports


def format_scan_results(reports: List[PatchReport]) -> str:
    """格式化扫描结果为可读文本"""
    if not reports:
        return "未发现补丁特征。所有文件通过检查。"

    lines = []
    lines.append("=" * 72)
    lines.append("  补丁检测扫描结果")
    lines.append("=" * 72)

    total_fail = sum(r.summary.get("FAIL", 0) for r in reports)
    total_warn = sum(r.summary.get("WARN", 0) for r in reports)
    lines.append(f"\n总计: {len(reports)} 个文件存在补丁特征")
    lines.append(f"  FAIL: {total_fail}  WARN: {total_warn}")
    lines.append("")

    for report in reports:
        rel = Path(report.file_path).name
        lines.append(f"--- {rel} ({report.summary['FAIL']} FAIL, "
                     f"{report.summary['WARN']} WARN) ---")
        for r in report.results:
            lines.append(f"  [{r.severity}] 行{r.line}: {r.description}")
            if r.context:
                lines.append(f"    代码: {r.context[:100]}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# 审批检查快捷函数
# ============================================================================

def check_method_approval(method_name: str, region_type: str,
                          method_type: str, existing_methods: List[str]) -> List[str]:
    """
    执行方法创建审批检查，返回警告/错误列表。

    Args:
        method_name: 提议的方法名
        region_type: 区域类型 (If/Loop/Try/With/Match/BoolOp/Ternary/Sequence/Basic)
        method_type: 方法类型 (identification/generation)
        existing_methods: 已存在的同类型方法名列表

    Returns:
        List[str] 警告/错误消息，空列表表示通过
    """
    issues = []

    forbidden = ["_fix_", "_merge_", "_patch_", "_fallback_", "_workaround_"]
    for prefix in forbidden:
        if prefix in method_name:
            issues.append(f"[FAIL] 方法名 '{method_name}' 包含禁止前缀 '{prefix}'")

    valid_regions = {"If", "Loop", "Try", "With", "Match", "BoolOp", "Ternary",
                     "Sequence", "Basic"}
    if region_type not in valid_regions:
        issues.append(f"[FAIL] 未知区域类型 '{region_type}'，有效值: {valid_regions}")

    if method_type not in ("identification", "generation"):
        issues.append(f"[FAIL] 未知方法类型 '{method_type}'，应为 'identification' 或 'generation'")

    for existing in existing_methods:
        if existing != method_name:
            issues.append(
                f"[FAIL] 区域类型 '{region_type}' 已存在方法 '{existing}'，"
                f"每种区域类型只能有1个{method_type}方法"
            )

    return issues


if __name__ == "__main__":
    import sys

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    target_dir = project_root / "core" / "cfg"

    print("补丁检测扫描")
    print(f"目标目录: {target_dir}")
    print()

    reports = scan_directory(str(target_dir))

    if reports:
        print(format_scan_results(reports))
        sys.exit(1)
    else:
        print("所有文件通过检查，未发现补丁特征。")
        sys.exit(0)
