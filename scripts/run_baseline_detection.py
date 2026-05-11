"""
客观补丁检测基线报告生成器

使用 ObjectivePatchDetector v2.0 对 region_analyzer.py 和 region_ast_generator.py
运行6维客观补丁检测，生成完整的基线报告。

输出：
- 控制台：完整检测结果
- 文件：.trae/specs/cfg-region-ultimate-perfection-phase6/baseline_report.md
"""

import sys
import os
from datetime import datetime
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg.objective_patch_detector import ObjectivePatchDetector, PatchVerdict


# Spec中预测需删除的43个方法清单
SPEC_PREDICTED_PATCHES_ANALYZER = {
    '_select_back_edge_block',
    '_create_loop_region',
    '_find_loop_else',
    '_annotate_loop_continue_blocks',
    '_analyze_if_region',
    '_is_ternary_block',
    '_find_merge_point',
    '_collect_branch_blocks',
    '_identify_try_except_regions',
    '_parse_exception_table_strictly',
    '_create_try_except_region',
    '_find_try_else_by_postdominator',
    '_identify_with_regions',
    '_detect_nested_matches',
    '_collect_case_body',
    '_register_if_region',
    '_create_nested_if_regions',
    '_is_chained_compare_header',
    '_is_while_condition_block',
    '_find_real_loop_header',
    '_is_conditional_block',
    '_has_backward_jump_to_self',
    '_is_break_block',
    '_jumps_to_if_condition',
    '_is_break_in_loop',
    '_analyze_boolop_chain',
    '_annotate_control_flow_role',
    '_annotate_region_blocks',
    '_compute_effective_instructions',
    '_identify_boolop_regions',
    '_is_finally_normal_path_exit',
    '_build_region_hierarchy',
}

SPEC_PREDICTED_PATCHES_GENERATOR = {
    '_is_with_cleanup_block',
    '_find_natural_back_edge_block',
    '_classify_and_filter_loop_body_blocks',
    '_is_break_jump',
    '_block_matches_finally_suffix',
    '_try_build_chained_compare',
    '_is_normal_path_finally_copy',
    '_try_generate_chained_compare',
    '_try_generate_ifexp',
}

SPEC_ALL_PREDICTED = SPEC_PREDICTED_PATCHES_ANALYZER | SPEC_PREDICTED_PATCHES_GENERATOR


def get_method_line_count(filepath: str, method_name: str) -> int:
    """获取方法的行数（近似值）"""
    import ast
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            end = getattr(node, 'end_lineno', node.lineno)
            return end - node.lineno + 1
    return 0


def generate_detailed_report(
    analyzer_verdicts: List[PatchVerdict],
    generator_verdicts: List[PatchVerdict],
    analyzer_file: str,
    generator_file: str,
) -> str:
    """生成详细的基线报告"""

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    lines = []
    lines.append("# 客观补丁检测基线报告")
    lines.append("")
    lines.append(f"### 检测时间: {now}")
    lines.append("### 检测器版本: v2.0 (6维D1-D6)")
    lines.append("")

    # ========== region_analyzer.py 检测结果 ==========
    lines.append("#### region_analyzer.py 检测结果")
    lines.append("")
    lines.append("| 方法名 | D1 | D2 | D3 | D4 | D5 | D6 | 违规数 | 判定 |")
    lines.append("|--------|----|----|----|----|----|----|--------|------|")

    for v in sorted(analyzer_verdicts, key=lambda x: x.method_name):
        line_count = get_method_line_count(analyzer_file, v.method_name)
        if v.is_patch:
            verdict = "🔴 补丁"
        elif v.violation_count > 0:
            verdict = f"⚠️ 可疑({v.violation_count}项)"
        else:
            verdict = "✅ 合规"
        lines.append(
            f"| {v.method_name} | "
            f"{v.d1_score:.1f} | {v.d2_score:.1f} | {v.d3_score:.1f} | "
            f"{v.d4_score:.1f} | {v.d5_score:.1f} | {v.d6_score:.1f} | "
            f"{v.violation_count}/6 | {verdict} |"
        )

    lines.append("")

    # ========== region_ast_generator.py 检测结果 ==========
    lines.append("#### region_ast_generator.py 检测结果")
    lines.append("")
    lines.append("| 方法名 | D1 | D2 | D3 | D4 | D5 | D6 | 违规数 | 判定 |")
    lines.append("|--------|----|----|----|----|----|----|--------|------|")

    for v in sorted(generator_verdicts, key=lambda x: x.method_name):
        line_count = get_method_line_count(generator_file, v.method_name)
        if v.is_patch:
            verdict = "🔴 补丁"
        elif v.violation_count > 0:
            verdict = f"⚠️ 可疑({v.violation_count}项)"
        else:
            verdict = "✅ 合规"
        lines.append(
            f"| {v.method_name} | "
            f"{v.d1_score:.1f} | {v.d2_score:.1f} | {v.d3_score:.1f} | "
            f"{v.d4_score:.1f} | {v.d5_score:.1f} | {v.d6_score:.1f} | "
            f"{v.violation_count}/6 | {verdict} |"
        )

    lines.append("")

    # ========== 统计汇总 ==========
    all_verdicts = analyzer_verdicts + generator_verdicts
    total = len(all_verdicts)
    patches = [v for v in all_verdicts if v.is_patch]
    suspicious = [v for v in all_verdicts if not v.is_patch and v.violation_count > 0]
    clean = [v for v in all_verdicts if v.violation_count == 0]

    lines.append("#### 统计汇总")
    lines.append("")
    lines.append(f"- 总方法数: **{total}**")
    lines.append(f"  - region_analyzer.py: {len(analyzer_verdicts)} 个方法")
    lines.append(f"  - region_ast_generator.py: {len(generator_verdicts)} 个方法")
    lines.append(f"- 🔴 补丁方法(≥3项违规): **{len(patches)}** 个 ({len(patches)/max(total,1)*100:.1f}%)")
    lines.append(f"- ⚠️ 可疑方法(1-2项): **{len(suspicious)}** 个 ({len(suspicious)/max(total,1)*100:.1f}%)")
    lines.append(f"- ✅ 合规方法(0项): **{len(clean)}** 个 ({len(clean)/max(total,1)*100:.1f}%)")
    lines.append("")

    # 各维度平均得分
    dims = ['d1_score', 'd2_score', 'd3_score', 'd4_score', 'd5_score', 'd6_score']
    dim_labels = {
        'd1_score': 'D1-算法依据性',
        'd2_score': 'D2-特殊分支数',
        'd3_score': 'D3-后处理修正',
        'd4_score': 'D4-跨域访问',
        'd5_score': 'D5-多路径生成',
        'd6_score': 'D6-硬编码引用',
    }
    lines.append("**各维度平均合规得分:**")
    for dim in dims:
        vals = [getattr(v, dim) for v in all_verdicts]
        avg = sum(vals) / max(len(vals), 1)
        bar_len = int(avg * 30)
        bar = '█' * bar_len + '░' * (30 - bar_len)
        lines.append(f"  - {dim_labels[dim]:15s}: [{bar}] {avg:.2f}")
    lines.append("")

    # ========== 与Spec预期对比 ==========
    detected_patch_names = set(v.method_name for v in patches)

    # Spec预测且实际检出为补丁的
    spec_detected = SPEC_ALL_PREDICTED & detected_patch_names
    # Spec预测但未检出为补丁的（可能是可疑或合规）
    spec_not_detected_as_patch = SPEC_ALL_PREDICTED - detected_patch_names
    # 新发现的补丁（Spec未预测到的）
    new_patches = detected_patch_names - SPEC_ALL_PREDICTED

    lines.append("#### 与Spec预期对比")
    lines.append("")
    lines.append(f"- Spec预测需删除: **{len(SPEC_ALL_PREDICTED)}** 个方法")
    lines.append(f"  - region_analyzer.py: {len(SPEC_PREDICTED_PATCHES_ANALYZER)} 个")
    lines.append(f"  - region_ast_generator.py: {len(SPEC_PREDICTED_PATCHES_GENERATOR)} 个")
    lines.append(f"- 实际检测为补丁(≥3项违规): **{len(detected_patch_names)}** 个")
    lines.append(f"- ✅ Spec预测且实际检出为补丁: **{len(spec_detected)}** 个 ({len(spec_detected)/max(len(SPEC_ALL_PREDICTED),1)*100:.1f}% 召回率)")
    lines.append(f"- 📋 Spec预测但未检出为补丁(可能为可疑/合规/不存在): **{len(spec_not_detected_as_patch)}** 个")
    if spec_not_detected_as_patch:
        for name in sorted(spec_not_detected_as_patch):
            # 查找这个方法的实际状态
            found = None
            for v in all_verdicts:
                if v.method_name == name:
                    found = v
                    break
            if found:
                status = f"补丁" if found.is_patch else f"可疑({found.violation_count}项)" if found.violation_count > 0 else "合规"
                lines.append(f"  - `{name}` → 实际状态: {status} (违规{found.violation_count}项)")
            else:
                lines.append(f"  - `{name}` → 方法未找到(可能已被删除或重命名)")
    lines.append(f"- 🆕 新发现的补丁(Spec未预测): **{len(new_patches)}** 个")
    if new_patches:
        for name in sorted(new_patches):
            lines.append(f"  - `{name}`")
    lines.append("")

    # ========== 方法分类清单 ==========
    lines.append("#### 方法分类清单")
    lines.append("")

    # 必须删除的补丁方法
    lines.append("##### 🔴 必须删除的补丁方法(≥3项违规):")
    lines.append("")
    for v in sorted(patches, key=lambda x: -x.violation_count):
        file_tag = "(analyzer)" if v in analyzer_verdicts else "(generator)"
        violations = ', '.join([d.split(':')[0] for d in v.violation_details])
        line_count = get_method_line_count(
            analyzer_file if v in analyzer_verdicts else generator_file,
            v.method_name
        )
        spec_mark = " ⭐Spec预测" if v.method_name in SPEC_ALL_PREDICTED else " 🆕新发现"
        lines.append(f"{len([p for p in patches if True])}. **`{v.method_name}`**{file_tag}{spec_mark} - 违反{violations} ({line_count}行)")
        for detail in v.violation_details:
            lines.append(f"   - {detail}")
    lines.append("")

    # 需要重写的方法（可疑）
    lines.append("##### ⚠️ 需要关注的方法(1-2项违规):")
    lines.append("")
    if suspicious:
        for i, v in enumerate(sorted(suspicious, key=lambda x: -x.violation_count), 1):
            file_tag = "(analyzer)" if v in analyzer_verdicts else "(generator)"
            violations = ', '.join([d.split(':')[0] for d in v.violation_details])
            line_count = get_method_line_count(
                analyzer_file if v in analyzer_verdicts else generator_file,
                v.method_name
            )
            lines.append(f"{i}. **`{v.method_name}`**{file_tag} - 违反{violations} ({line_count}行)")
            for detail in v.violation_details:
                lines.append(f"   - {detail}")
    else:
        lines.append("(无)")
    lines.append("")

    # 可以保留的方法（合规）
    lines.append("##### ✅ 可以保留的方法(0项违规):")
    lines.append("")
    if clean:
        for i, v in enumerate(sorted(clean, key=lambda x: x.method_name), 1):
            file_tag = "(analyzer)" if v in analyzer_verdicts else "(generator)"
            lines.append(f"{i}. `{v.method_name}`{file_tag}")
    else:
        lines.append("(无)")
    lines.append("")

    # ========== 维度违规分布分析 ==========
    lines.append("#### 各维度违规分布分析")
    lines.append("")

    dim_counts = {}
    for dim_idx, (dim, label) in enumerate(zip(dims, dim_labels.values())):
        count = sum(1 for v in all_verdicts if getattr(v, dim) < 0.5)
        pct = count / max(total, 1) * 100
        dim_counts[label] = (count, pct)

    lines.append("| 维度 | 违规方法数 | 占比 | 严重程度 |")
    lines.append("|------|-----------|------|---------|")
    severity_order = ['D6-硬编码引用', 'D4-跨域访问', 'D1-算法依据性', 'D3-后处理修正', 'D2-特殊分支数', 'D5-多路径生成']
    for label in severity_order:
        count, pct = dim_counts.get(label, (0, 0))
        if pct >= 50:
            severity = "🔴 严重"
        elif pct >= 25:
            severity = "🟠 较高"
        elif pct >= 10:
            severity = "🟡 中等"
        else:
            severity = "🟢 良好"
        lines.append(f"| {label} | {count}/{total} | {pct:.1f}% | {severity} |")
    lines.append("")

    # ========== 建议优先级 ==========
    lines.append("#### 重构建议与优先级")
    lines.append("")
    lines.append("**P0 - 立即处理(高影响补丁方法)**:")
    lines.append("")
    high_impact_patches = [v for v in patches if v.violation_count >= 4]
    if high_impact_patches:
        for i, v in enumerate(sorted(high_impact_patches, key=lambda x: -x.violation_count), 1):
            lines.append(f"{i}. `{v.method_name}` - {v.violation_count}项违规，建议立即删除或完全重写")
    else:
        lines.append("(无4+项违规的方法)")
    lines.append("")

    lines.append("**P1 - 本周处理(标准补丁方法)**:")
    lines.append("")
    std_patches = [v for v in patches if 3 <= v.violation_count < 4]
    if std_patches:
        for i, v in enumerate(sorted(std_patches, key=lambda x: -x.violation_count), 1):
            lines.append(f"{i}. `{v.method_name}` - {v.violation_count}项违规")
    else:
        lines.append("(无)")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*报告由 ObjectivePatchDetector v2.0 自动生成*")

    return '\n'.join(lines)


def main():
    """主函数"""

    print("=" * 70)
    print("客观补丁检测基线报告生成器")
    print("Objective Patch Detector v2.0 - Baseline Report Generator")
    print("=" * 70)
    print()

    # 目标文件
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer_file = os.path.join(base_dir, 'core', 'cfg', 'region_analyzer.py')
    generator_file = os.path.join(base_dir, 'core', 'cfg', 'region_ast_generator.py')
    report_dir = os.path.join(base_dir, '.trae', 'specs', 'cfg-region-ultimate-perfection-phase6')
    report_file = os.path.join(report_dir, 'baseline_report.md')

    # 验证文件存在
    for fp in [analyzer_file, generator_file]:
        if not os.path.exists(fp):
            print(f"❌ 错误: 文件不存在 - {fp}")
            sys.exit(1)

    # 创建检测器实例
    detector = ObjectivePatchDetector()
    print(f"✅ 检测器初始化完成")
    print(f"   检测维度: D1(算法依据) D2(分支数量) D3(后处理) D4(跨域访问) D5(多路径) D6(硬编码)")
    print(f"   判定阈值: ≥3项违规即为补丁方法")
    print()

    # 分析 region_analyzer.py
    print("-" * 70)
    print(f"正在分析: region_analyzer.py")
    print("-" * 70)
    analyzer_verdicts = detector.analyze_file(analyzer_file)
    print(f"✅ 完成: 检测到 {len(analyzer_verdicts)} 个方法")
    print()

    # 分析 region_ast_generator.py
    print("-" * 70)
    print(f"正在分析: region_ast_generator.py")
    print("-" * 70)
    generator_verdicts = detector.analyze_file(generator_file)
    print(f"✅ 完成: 检测到 {len(generator_verdicts)} 个方法")
    print()

    # 生成详细报告
    print("=" * 70)
    print("正在生成基线报告...")
    print("=" * 70)

    detailed_report = generate_detailed_report(
        analyzer_verdicts,
        generator_verdicts,
        analyzer_file,
        generator_file,
    )

    # 输出到控制台
    print()
    print(detailed_report)

    # 保存到文件
    os.makedirs(report_dir, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(detailed_report)
    print()
    print(f"💾 报告已保存至: {report_file}")

    # 输出摘要
    all_verdicts = analyzer_verdicts + generator_verdicts
    total = len(all_verdicts)
    patches = sum(1 for v in all_verdicts if v.is_patch)
    suspicious = sum(1 for v in all_verdicts if not v.is_patch and v.violation_count > 0)
    clean = total - patches - suspicious

    print()
    print("=" * 70)
    print("📊 检测摘要")
    print("=" * 70)
    print(f"  总方法数:     {total}")
    print(f"  🔴 补丁方法:  {patches} ({patches/max(total,1)*100:.1f}%)")
    print(f"  ⚠️ 可疑方法:  {suspicious} ({suspicious/max(total,1)*100:.1f}%)")
    print(f"  ✅ 合规方法:  {clean} ({clean/max(total,1)*100:.1f}%)")
    print("=" * 70)


if __name__ == '__main__':
    main()
