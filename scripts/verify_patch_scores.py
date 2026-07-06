import argparse
import json
import sys
from pathlib import Path


def load_json_report(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_score(report, key='score'):
    if isinstance(report, dict):
        return report.get(key)
    return None


def verify_patch_scores(min_score=98):
    reports = [
        Path('core/cfg/report_region_analyzer.json'),
        Path('core/cfg/report_region_ast_generator.json'),
    ]

    all_passed = True
    results = []

    for report_path in reports:
        if not report_path.exists():
            print(f"❌ 报告文件不存在: {report_path}")
            all_passed = False
            continue

        try:
            data = load_json_report(report_path)
            score = extract_score(data)

            if score is None:
                print(f"❌ 无法从报告提取评分: {report_path}")
                all_passed = False
                results.append((str(report_path), None, False))
                continue

            passed = score >= min_score
            status = "✅ 通过" if passed else "❌ 未通过"
            print(f"{status} | 文件: {report_path.name} | 评分: {score} (阈值: {min_score})")
            results.append((str(report_path), score, passed))

            if not passed:
                all_passed = False

        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误 ({report_path}): {e}")
            all_passed = False
            results.append((str(report_path), None, False))
        except Exception as e:
            print(f"❌ 处理报告时出错 ({report_path}): {e}")
            all_passed = False
            results.append((str(report_path), None, False))

    print("\n=== 验证结果汇总 ===")
    for path, score, passed in results:
        score_str = f"{score:.2f}" if score is not None else "N/A"
        status_str = "PASS" if passed else "FAIL"
        print(f"{status_str:4s} | {Path(path).name}: {score_str}")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description='验证补丁检测评分')
    parser.add_argument('--min-score', type=float, default=98,
                        help='最低评分阈值 (默认: 98)')
    args = parser.parse_args()

    success = verify_patch_scores(min_score=args.min_score)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
