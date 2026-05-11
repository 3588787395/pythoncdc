#!/usr/bin/env python
"""Phase 6 Final Acceptance Test Script"""
import sys
import ast
sys.path.insert(0, 'f:/pythoncdc')

from core.cfg.objective_patch_detector import ObjectivePatchDetector

def get_method_lengths(filepath):
    """使用AST获取方法行数"""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    lengths = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lengths[node.name] = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
    return lengths

def main():
    detector = ObjectivePatchDetector()

    print('=' * 80)
    print('ObjectivePatchDetector v2.0 - Final Acceptance Test')
    print('=' * 80)

    # Detect region_analyzer.py
    print('\n>>> region_analyzer.py <<<')
    analyzer_verdicts = detector.analyze_file('f:/pythoncdc/core/cfg/region_analyzer.py')
    analyzer_lines = get_method_lengths('f:/pythoncdc/core/cfg/region_analyzer.py')

    # Detect region_ast_generator.py
    print('\n>>> region_ast_generator.py <<<')
    generator_verdicts = detector.analyze_file('f:/pythoncdc/core/cfg/region_ast_generator.py')
    generator_lines = get_method_lengths('f:/pythoncdc/core/cfg/region_ast_generator.py')

    # Generate combined report
    print('\n' + '=' * 80)
    report = detector.generate_report(analyzer_verdicts + generator_verdicts)
    print(report)

    # Key metrics
    all_verdicts = analyzer_verdicts + generator_verdicts
    all_lengths = {**analyzer_lines, **generator_lines}
    patch_methods = [v for v in all_verdicts if v.violation_count >= 3]
    suspicious = [v for v in all_verdicts if 1 <= v.violation_count < 3]
    compliant = [v for v in all_verdicts if v.violation_count == 0]

    print(f'\n{"="*60}')
    print('KEY METRICS SUMMARY')
    print(f'{"="*60}')
    print(f'Total methods analyzed: {len(all_verdicts)}')
    print(f'Patch methods (>=3 violations): {len(patch_methods)}')
    print(f'Suspicious methods (1-2 violations): {len(suspicious)}')
    print(f'Compliant methods (0 violations): {len(compliant)}')

    if all_lengths:
        line_values = list(all_lengths.values())
        max_lines = max(line_values) if line_values else 0
        avg_lines = sum(line_values) / len(line_values) if line_values else 0
        over80 = sum(1 for l in line_values if l > 80)
        over100 = sum(1 for l in line_values if l > 100)
        over150 = sum(1 for l in line_values if l > 150)

        print(f'\nMethod Size Metrics:')
        print(f'  Max method lines: {max_lines}')
        print(f'  Avg method lines: {avg_lines:.1f}')
        print(f'  Methods >80 lines: {over80}')
        print(f'  Methods >100 lines: {over100}')
        print(f'  Methods >150 lines: {over150}')

    # Per-file breakdown
    print(f'\n{"="*60}')
    print('PER-FILE BREAKDOWN')
    print(f'{"="*60}')

    for fname, verdicts, lengths in [('region_analyzer.py', analyzer_verdicts, analyzer_lines),
                                       ('region_ast_generator.py', generator_verdicts, generator_lines)]:
        f_patch = sum(1 for v in verdicts if v.violation_count >= 3)
        f_susp = sum(1 for v in verdicts if 1 <= v.violation_count < 3)
        f_comp = sum(1 for v in verdicts if v.violation_count == 0)
        total = len(verdicts)
        comp_rate = (f_comp / total * 100) if total > 0 else 0

        # Calculate scores
        avg_d1 = sum(v.d1_score for v in verdicts) / total if total > 0 else 0
        avg_d2 = sum(v.d2_score for v in verdicts) / total if total > 0 else 0
        avg_d3 = sum(v.d3_score for v in verdicts) / total if total > 0 else 0
        avg_d4 = sum(v.d4_score for v in verdicts) / total if total > 0 else 0
        avg_d5 = sum(v.d5_score for v in verdicts) / total if total > 0 else 0
        avg_d6 = sum(v.d6_score for v in verdicts) / total if total > 0 else 0
        overall = (avg_d1 + avg_d2 + avg_d3 + avg_d4 + avg_d5 + avg_d6) / 6

        print(f'\n{fname}:')
        print(f'  Total: {total} | Compliant: {f_comp} ({comp_rate:.1f}%) | Suspicious: {f_susp} | Patch: {f_patch}')
        print(f'  Dimension Scores: D1={avg_d1:.2f} D2={avg_d2:.2f} D3={avg_d3:.2f} D4={avg_d4:.2f} D5={avg_d5:.2f} D6={avg_d6:.2f}')
        print(f'  Overall Score: {overall:.2f}/1.00')

if __name__ == '__main__':
    main()
