"""轮 3 测试工程师：批量验证 minimal_repros，输出 repro_verify_summary.txt / .json。

对每个 repro_NN_*.py：编译 → 反编译 → 字节码比较，记录 matched/total/首处 diff。
判定 repro 是否「复现缺陷」：若任一 code object 不一致则复现缺陷（BAD）。
"""
import sys
import os
import json
import glob

sys.path.insert(0, '/workspace')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from verify_repro import verify  # noqa: E402

REPRO_GLOB = os.path.join(HERE, 'repro_*.py')


def main():
    files = sorted(glob.glob(REPRO_GLOB))
    files = [f for f in files if os.path.basename(f) != 'verify_repro.py']
    lines = []
    summary = {'repros': []}
    pass_count = 0
    fail_count = 0
    for f in files:
        name = os.path.basename(f)
        r = verify(f)
        entry = {'file': name}
        if not r.get('compile_ok'):
            entry['status'] = 'compile_fail'
            entry['err'] = r.get('err', '')[:200]
            fail_count += 1
            lines.append(f"[COMPILE_FAIL] {name}: {entry['err']}")
            summary['repros'].append(entry)
            continue
        total = r['total']
        matched = r['matched']
        mismatched = r['mismatched']
        reproduces = mismatched > 0
        entry['status'] = 'reproduces' if reproduces else 'pass'
        entry['total'] = total
        entry['matched'] = matched
        entry['mismatched'] = mismatched
        # 首处不一致
        first_bad = None
        for nm, st, extra in r['details']:
            if st != 'match':
                first_bad = {'name': nm, 'status': st, 'extra': extra}
                break
        entry['first_bad'] = first_bad
        if reproduces:
            fail_count += 1
            tag = 'REPRODUCES'
        else:
            pass_count += 1
            tag = 'PASS(no defect)'
        line = f"[{tag}] {name}: total={total} matched={matched} mismatched={mismatched}"
        if first_bad:
            line += f" | first_bad={first_bad['name']} {first_bad['status']} {first_bad['extra'] or ''}"
        lines.append(line)
        summary['repros'].append(entry)

    summary['total_repros'] = len(files)
    summary['reproduces_count'] = fail_count
    summary['pass_count'] = pass_count

    out_txt = os.path.join(HERE, 'repro_verify_summary.txt')
    out_json = os.path.join(HERE, 'repro_verify_summary.json')
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)

    print("\n".join(lines))
    print(f"\n[summary] total_repros={summary['total_repros']} reproduces={fail_count} pass={pass_count}")
    print(f"[summary] wrote {out_txt} + {out_json}")


if __name__ == '__main__':
    main()
