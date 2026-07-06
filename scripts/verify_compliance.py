import argparse
import json
import sys
from pathlib import Path


def load_compliance_report(filepath='compliance_report.json'):
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"合规报告不存在: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_compliance(allow_zero_violations=False):
    try:
        report = load_compliance_report()
    except FileNotFoundError as e:
        print(f"错误: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return False

    total_violations = report.get('total_violations', 0)
    violations = report.get('violations', [])

    print("=== 合规性验证 ===")
    print(f"总违规数: {total_violations}")

    if allow_zero_violations:
        if total_violations == 0:
            print("✅ 零违规检查通过")
            return True
        else:
            print(f"❌ 发现 {total_violations} 个违规:")
            for v in violations[:10]:
                file_info = v.get('file', 'unknown')
                method = v.get('method', 'N/A')
                issue = v.get('issue', '未知问题')
                print(f"   - [{file_info}] {method}: {issue}")

            if len(violations) > 10:
                print(f"   ... 还有 {len(violations) - 10} 条未显示")

            return False
    else:
        if total_violations == 0:
            print("✅ 无违规项")
        else:
            print(f"⚠️ 存在 {total_violations} 个违规（未强制零违规）")
            for v in violations[:10]:
                file_info = v.get('file', 'unknown')
                method = v.get('method', 'N/A')
                issue = v.get('issue', '未知问题')
                print(f"   - [{file_info}] {method}: {issue}")

        return True


def main():
    parser = argparse.ArgumentParser(description='验证方法合规性报告')
    parser.add_argument('--allow-zero-violations', action='store_true',
                        help='强制要求零违规')
    args = parser.parse_args()

    success = verify_compliance(allow_zero_violations=args.allow_zero_violations)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
