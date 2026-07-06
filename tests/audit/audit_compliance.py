#!/usr/bin/env python3
"""
防补丁合规性自动审计脚本

检测 region_analyzer.py 和 region_ast_generator.py 中的补丁特征。
4项检测：
  1. 禁止的方法名模式
  2. 后处理修正
  3. 跨职责修改
  4. 同一结构多生成路径

用法: python tests/audit/audit_compliance.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Violation:
    check_name: str
    file_path: str
    line: int
    description: str
    context: str = ""


class ComplianceAuditor:
    """合规性审计器 - 4项检测"""

    TARGET_FILES = [
        "core/cfg/region_analyzer.py",
        "core/cfg/region_ast_generator.py",
    ]

    FORBIDDEN_PREFIXES = ["_fix_", "_merge_", "_patch_", "_fallback_", "_workaround_"]

    POST_MODIFY_PATTERNS = [
        (r'(?<!\w)region\s*\.\s*blocks\s*=', 'region.blocks 赋值'),
        (r'(?<!\w)region\s*\.\s*type\s*=', 'region.type 赋值'),
        (r'(?<!\w)region\s*\.\s*body_blocks\s*\.\s*add\s*\(', 'region.body_blocks.add()'),
        (r'(?<!\w)region\s*\.\s*body_blocks\s*\.\s*remove\s*\(', 'region.body_blocks.remove()'),
        (r'(?<!\w)region\s*\.\s*body_blocks\s*\.\s*discard\s*\(', 'region.body_blocks.discard()'),
        (r'(?<!\w)region\s*\.\s*body_blocks\s*=', 'region.body_blocks 赋值'),
    ]

    CROSS_RESP_ANALYSIS_PREFIXES = [
        "_is_", "_has_", "_check_", "_detect_", "_find_", "_collect_", "_extract_"
    ]

    CROSS_RESP_ANALYSIS_ATTRS = [
        "self.loop_analyzer",
        "self.dominator",
        "self.dom_analyzer",
        "self.dominator_tree",
    ]

    GENERATE_METHOD_GROUP = {
        "IfRegion": ["_generate_if"],
        "LoopRegion": ["_generate_loop"],
        "TryExceptRegion": ["_generate_try"],
        "WithRegion": ["_generate_with"],
        "MatchRegion": ["_generate_match"],
        "AssertRegion": ["_generate_assert"],
        "BoolOpRegion": ["_generate_boolop"],
        "TernaryRegion": ["_generate_ternary"],
        "BasicRegion": ["_generate_basic_region"],
    }

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.violations: List[Violation] = []

    def audit(self) -> List[Violation]:
        self.violations = []
        self._check_forbidden_method_names()
        self._check_post_processing_modification()
        self._check_cross_responsibility()
        self._check_multiple_generation_paths()
        return self.violations

    def _read_lines(self, rel_path: str) -> Tuple[Optional[Path], List[str]]:
        file_path = self.base_path / rel_path
        if not file_path.exists():
            return None, []
        with open(file_path, "r", encoding="utf-8") as f:
            return file_path, f.readlines()

    # ---- 31.1 检测 _fix_*/_merge_*/_patch_*/_fallback_* 方法 ----

    def _check_forbidden_method_names(self):
        for rel_path in self.TARGET_FILES:
            file_path, lines = self._read_lines(rel_path)
            if file_path is None:
                continue
            for i, line in enumerate(lines, 1):
                for prefix in self.FORBIDDEN_PREFIXES:
                    if re.search(rf'def\s+{re.escape(prefix)}\w*\s*\(', line):
                        self.violations.append(Violation(
                            check_name="禁止的方法名模式",
                            file_path=str(file_path),
                            line=i,
                            description=f"方法名以 '{prefix}' 开头",
                            context=line.strip(),
                        ))

    # ---- 31.2 检测后处理修正 ----

    def _check_post_processing_modification(self):
        for rel_path in self.TARGET_FILES:
            file_path, lines = self._read_lines(rel_path)
            if file_path is None:
                continue

            hierarchy_line = self._find_method_line(lines, "_build_region_hierarchy")
            last_method_line = self._find_last_method_line(lines)

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                for pattern, desc in self.POST_MODIFY_PATTERNS:
                    m = re.search(pattern, line)
                    if m is None:
                        continue

                    if self._is_region_class_definition(lines, i):
                        continue
                    if self._is_region_initialization(lines, i):
                        continue

                    if hierarchy_line is not None and i > hierarchy_line:
                        self.violations.append(Violation(
                            check_name="后处理修正",
                            file_path=str(file_path),
                            line=i,
                            description=f"_build_region_hierarchy（行{hierarchy_line}）之后发现 {desc}",
                            context=stripped,
                        ))

    def _find_method_line(self, lines: List[str], method_name: str) -> Optional[int]:
        for i, line in enumerate(lines, 1):
            if re.search(rf'def\s+{re.escape(method_name)}\s*\(', line):
                return i
        return None

    def _find_last_method_line(self, lines: List[str]) -> Optional[int]:
        last = None
        for i, line in enumerate(lines, 1):
            if re.match(r'def\s+\w+\s*\(', line):
                last = i
        return last

    def _is_region_class_definition(self, lines: List[str], line_num: int) -> bool:
        start = max(0, line_num - 50)
        context = "".join(lines[start:line_num])
        return "class Region" in context or "class LoopRegion" in context

    def _is_region_initialization(self, lines: List[str], line_num: int) -> bool:
        start = max(0, line_num - 8)
        context = "".join(lines[start:line_num])
        markers = ["= LoopRegion(", "= IfRegion(", "= TryExceptRegion(", "= WithRegion(",
                     "= MatchRegion(", "= AssertRegion(", "= BoolOpRegion(", "= TernaryRegion("]
        return any(m in context for m in markers)

    # ---- 31.3 检测跨职责修改 ----

    def _check_cross_responsibility(self):
        rel_path = "core/cfg/region_ast_generator.py"
        file_path, lines = self._read_lines(rel_path)
        if file_path is None:
            return

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for attr in self.CROSS_RESP_ANALYSIS_ATTRS:
                if attr in stripped:
                    self.violations.append(Violation(
                        check_name="跨职责修改",
                        file_path=str(file_path),
                        line=i,
                        description=f"生成器访问分析器引用: {attr}",
                        context=stripped,
                    ))

            if re.search(r'self\.cfg\.get_block_by_offset\s*\(', line):
                self.violations.append(Violation(
                    check_name="跨职责修改",
                    file_path=str(file_path),
                    line=i,
                    description="生成器直接操作CFG: cfg.get_block_by_offset()",
                    context=stripped,
                ))

            m = re.match(r'\s*def\s+(_\w+)\s*\(', line)
            if m:
                method_name = m.group(1)
                for prefix in self.CROSS_RESP_ANALYSIS_PREFIXES:
                    if method_name.startswith(prefix):
                        self.violations.append(Violation(
                            check_name="跨职责修改",
                            file_path=str(file_path),
                            line=i,
                            description=f"生成器包含分析语义方法: {method_name} (前缀 '{prefix}')",
                            context=stripped,
                        ))

    # ---- 31.4 检测同一结构多生成路径 ----

    def _check_multiple_generation_paths(self):
        rel_path = "core/cfg/region_ast_generator.py"
        file_path, lines = self._read_lines(rel_path)
        if file_path is None:
            return

        all_methods = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            m = re.match(r'\s*def\s+(_\w+)\s*\(', stripped)
            if m:
                all_methods.append((i, m.group(1), stripped))

        internal_suffixes = ("_impl", "_internal", "_body", "_statements")

        for region_type, expected in self.GENERATE_METHOD_GROUP.items():
            related = [
                (ln, name, ctx)
                for ln, name, ctx in all_methods
                if any(name.startswith(exp) or name == exp for exp in expected)
            ]
            public_methods = [
                (ln, name, ctx)
                for ln, name, ctx in related
                if not any(name.endswith(s) for s in internal_suffixes)
            ]
            if len(public_methods) > 1:
                names = [n for _, n, _ in public_methods]
                self.violations.append(Violation(
                    check_name="同一结构多生成路径",
                    file_path=str(file_path),
                    line=public_methods[0][0],
                    description=f"{region_type} 存在多个公共生成方法: {names}",
                    context="",
                ))

        try_generate_methods = [
            (ln, name, ctx)
            for ln, name, ctx in all_methods
            if name.startswith("_try_generate_")
        ]
        if try_generate_methods:
            for ln, name, ctx in try_generate_methods:
                self.violations.append(Violation(
                    check_name="同一结构多生成路径",
                    file_path=str(file_path),
                    line=ln,
                    description=f"发现回退式生成方法: {name}",
                    context=ctx,
                ))

        has_try_generate_call = False
        for i, line in enumerate(lines, 1):
            if re.search(r'_try_generate_\w*\s*\(', line):
                has_try_generate_call = True
                self.violations.append(Violation(
                    check_name="同一结构多生成路径",
                    file_path=str(file_path),
                    line=i,
                    description="代码中调用了 _try_generate_* 回退方法",
                    context=line.strip(),
                ))

        generate_if_line = self._find_method_line(lines, "_generate_if")
        if generate_if_line is None:
            return

        indent_level = None
        for i in range(generate_if_line - 1, len(lines)):
            stripped = lines[i].strip()
            if not stripped or stripped.startswith("#"):
                continue
            if i == generate_if_line - 1:
                continue
            if re.match(r'def\s+_\w+\s*\(', stripped):
                break

            if re.search(r'\b_generate_if\b', stripped) and i != generate_if_line - 1:
                self.violations.append(Violation(
                    check_name="同一结构多生成路径",
                    file_path=str(file_path),
                    line=i + 1,
                    description=f"_generate_if 方法内部调用了另一个 _generate_if（行{i + 1}）",
                    context=stripped,
                ))


def print_report(violations: List[Violation]):
    if not violations:
        print("所有合规性检查通过")
        print("\n无违规项发现。")
        return

    print(f"\n发现 {len(violations)} 项违规：\n")

    by_check: Dict[str, List[Violation]] = {}
    for v in violations:
        by_check.setdefault(v.check_name, []).append(v)

    for check_name, vlist in by_check.items():
        print(f"  [{check_name}] 共 {len(vlist)} 项：")
        for v in vlist:
            rel = Path(v.file_path).name
            print(f"    {rel}:{v.line}  {v.description}")
            if v.context:
                print(f"      代码: {v.context[:120]}")
        print()


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    if not project_root.exists():
        print(f"错误: 项目根目录不存在: {project_root}", file=sys.stderr)
        sys.exit(2)

    auditor = ComplianceAuditor(str(project_root))
    violations = auditor.audit()

    print("=" * 64)
    print("  防补丁合规性自动审计报告")
    print("=" * 64)

    print_report(violations)

    if violations:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
