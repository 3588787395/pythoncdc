"""批量验证所有 repro_*.py，输出 repro_verify_summary.txt + .json。

对每个 repro：py_compile → 反编译 → 编译 → 比较字节码，
判定是否复现缺陷（mismatched > 0）。
"""
import os
import sys
import json
import glob

sys.path.insert(0, '/workspace')
sys.path.insert(0, os.path.dirname(__file__))

from verify_repro import verify

REPRO_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    results = []
    for rp in repros:
        name = os.path.basename(rp)
        print(f"\n=== {name} ===")
        r = verify(rp)
        entry = {'file': name, 'compile_ok': r.get('compile_ok')}
        if r.get('compile_ok'):
            entry['total'] = r['total']
            entry['matched'] = r['matched']
            entry['mismatched'] = r['mismatched']
            entry['success_rate'] = r['success_rate']
            entry['reproduces'] = r['mismatched'] > 0
            entry['details'] = [
                {'name': n, 'status': s, 'extra': e}
                for (n, s, e) in r['details']
            ]
            print(f"  total={r['total']} matched={r['matched']} mismatched={r['mismatched']} reproduces={entry['reproduces']}")
            for n, s, e in r['details']:
                if s != 'match':
                    print(f"    [BAD] {n}: {s} {e or ''}")
        else:
            entry['reproduces'] = False
            entry['err'] = r.get('err', '')
            print(f"  compile FAILED: {entry['err']}")
        results.append(entry)

    total = len(results)
    compile_ok_count = sum(1 for r in results if r.get('compile_ok'))
    reproduced = sum(1 for r in results if r.get('reproduces'))
    summary = {
        'total_repros': total,
        'compile_ok': compile_ok_count,
        'reproduces_defect': reproduced,
        'not_reproduced': total - reproduced,
    }

    # 写 .json
    out_json = os.path.join(REPRO_DIR, 'repro_verify_summary.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'summary': summary, 'results': results}, f, indent=2, default=str)

    # 写 .txt
    out_txt = os.path.join(REPRO_DIR, 'repro_verify_summary.txt')
    lines = []
    lines.append("=" * 70)
    lines.append("Round 2 minimal_repros 验证摘要")
    lines.append("=" * 70)
    lines.append(f"总 repro 数: {total}")
    lines.append(f"py_compile 通过: {compile_ok_count}")
    lines.append(f"复现缺陷（反编译后字节码不一致）: {reproduced}")
    lines.append(f"未复现: {total - reproduced}")
    lines.append("")
    lines.append("说明：复现 = 至少一个 code object 的 dis 指令序列与原始不一致")
    lines.append("      （len_diff / instr_diff / missing 均计为复现）")
    lines.append("")
    lines.append(f"{'编号':<6}{'文件名':<48}{'compile':<10}{'复现':<8}{'total/matched'}")
    lines.append("-" * 90)
    for r in results:
        idx = r['file'].split('_')[1]
        if r.get('compile_ok'):
            tm = f"{r['total']}/{r['matched']}"
            rep = 'YES' if r['reproduces'] else 'no'
            lines.append(f"{idx:<6}{r['file']:<48}{'OK':<10}{rep:<8}{tm}")
        else:
            lines.append(f"{idx:<6}{r['file']:<48}{'FAIL':<10}{'-':<8}-")
    lines.append("")
    lines.append("=== 各 repro 复现明细 ===")
    for r in results:
        lines.append("")
        lines.append(f"--- {r['file']} ---")
        if not r.get('compile_ok'):
            lines.append(f"  compile FAILED: {r.get('err', '')}")
            continue
        lines.append(f"  total={r['total']} matched={r['matched']} mismatched={r['mismatched']} reproduces={r['reproduces']}")
        for d in r.get('details', []):
            if d['status'] != 'match':
                lines.append(f"    [BAD] {d['name']}: {d['status']} {d.get('extra') or ''}")
    lines.append("")
    lines.append(f"结论: {reproduced}/{total} 个 repro 复现缺陷（要求 ≥10）")

    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n=== SUMMARY ===")
    print(f"total={total} compile_ok={compile_ok_count} reproduced={reproduced}")
    print(f"wrote {out_json}")
    print(f"wrote {out_txt}")


if __name__ == '__main__':
    main()
