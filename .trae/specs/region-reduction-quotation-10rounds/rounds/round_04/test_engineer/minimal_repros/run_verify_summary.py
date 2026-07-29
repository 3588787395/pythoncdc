"""批量验证 minimal_repros/ 下所有 repro，输出 repro_verify_summary.{txt,json}。

用法：
    python run_verify_summary.py
"""
import os
import sys
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verify_repro import verify

REPRO_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_TXT = os.path.join(REPRO_DIR, 'repro_verify_summary.txt')
OUT_JSON = os.path.join(REPRO_DIR, 'repro_verify_summary.json')


def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    repros = [r for r in repros if not r.endswith('verify_repro.py')]
    print(f'found {len(repros)} repros')

    results = {}
    lines = []
    lines.append('=' * 80)
    lines.append('Round 4 测试工程师 — minimal_repros 验证汇总')
    lines.append('=' * 80)
    lines.append(f'repro_dir: {REPRO_DIR}')
    lines.append(f'repro_count: {len(repros)}')
    lines.append('')

    defect_count = 0
    pass_count = 0
    compile_fail_count = 0

    for repro in repros:
        name = os.path.basename(repro)
        print(f'verifying {name}...')
        try:
            r = verify(repro)
        except Exception as e:
            r = {'compile_ok': False, 'err': f'{type(e).__name__}: {e}'}

        results[name] = r
        lines.append('-' * 80)
        lines.append(f'REPRO: {name}')
        if r.get('compile_ok'):
            total = r['total']
            matched = r['matched']
            mismatched = r['mismatched']
            rate = r['success_rate']
            lines.append(f'  compile_ok=True  total={total} matched={matched} mismatched={mismatched} rate={rate}%')
            for fname, status, extra in r['details']:
                tag = 'OK ' if status == 'match' else 'BAD'
                lines.append(f'    [{tag}] {fname}: {status} {extra or ""}')
            if mismatched > 0:
                defect_count += 1
                lines.append(f'  >> 复现缺陷（{mismatched} 个函数不一致）')
            else:
                pass_count += 1
                lines.append(f'  >> 全部匹配（无缺陷复现）')
        else:
            compile_fail_count += 1
            lines.append(f'  compile_ok=False  err={r.get("err", "")}')
            lines.append(f'  >> 编译失败')
        lines.append('')

    lines.append('=' * 80)
    lines.append('汇总')
    lines.append('=' * 80)
    lines.append(f'repro 总数: {len(repros)}')
    lines.append(f'复现缺陷 repro 数: {defect_count}')
    lines.append(f'全部匹配 repro 数: {pass_count}')
    lines.append(f'编译失败 repro 数: {compile_fail_count}')
    lines.append('')

    out = '\n'.join(lines) + '\n'
    with open(OUT_TXT, 'w', encoding='utf-8') as f:
        f.write(out)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f'wrote {OUT_TXT}')
    print(f'wrote {OUT_JSON}')
    print(f'defect_count={defect_count} pass_count={pass_count} compile_fail_count={compile_fail_count}')


if __name__ == '__main__':
    main()
