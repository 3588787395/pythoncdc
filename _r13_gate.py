"""Round 13 验收闸门：重生成 OK.py -> 严格尺子复验 -> 与基线对比「翻正/回归」。

与 scripts/round_batch.py 的区别：本脚本以 **严格尺子**（_r10_strict_check）为唯一
判据，并把「基线里有缺陷、本轮变成无缺陷」与「基线里无缺陷、本轮变成有缺陷」分别
计数，因此一条命令即可同时回答「解决了几个」和「有没有退化」。

安全：重生成前把原 OK.py 备份到 D:/Temp/r13_gate_backup/；若新产物 py_compile
失败或严格尺子上缺陷函数数变多，则**自动回滚**该 OK.py 并标记 REGRESS-ROLLBACK。

用法：
  python _r13_gate.py --targets <每行一个pyc路径> --baseline <基线txt> [<基线txt> ...]
                --out <json输出> [--no-rollback]
基线 txt = _r10_strict_check.py 的原始输出（含 "DEFECT n/m <path>" / "OK n/m <path>"）。
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from _r10_strict_check import check_pyc  # noqa: E402
from scripts import pyc_batch_verify as pbv  # noqa: E402

BACKUP_DIR = Path('D:/Temp/r13_gate_backup')
DEFECT_RE = re.compile(r'\s*(DEFECT|OK)\s+(\d+)/(\d+)\s+(\S+)')


def load_baseline(paths):
    """基线 txt -> {pyc绝对路径: {缺陷函数名集合}}（未出现的文件视为无缺陷）。"""
    out = {}
    for p in paths:
        for line in io.open(p, encoding='utf-8').read().splitlines():
            m = DEFECT_RE.match(line)
            if not m:
                continue
            kind, _good, _tot, rel = m.groups()
            full = str((ROOT / 'site-packages' / rel).resolve()).replace('\\', '/')
            out.setdefault(full, set())
            if kind == 'DEFECT':
                out['_pending_' + full] = True
    # 第二遍：把 "- <module>.foo: [kind]" 归到最近的 DEFECT 文件
    for p in paths:
        cur = None
        for line in io.open(p, encoding='utf-8').read().splitlines():
            m = DEFECT_RE.match(line)
            if m:
                kind, _g, _t, rel = m.groups()
                cur = str((ROOT / 'site-packages' / rel).resolve()).replace('\\', '/')
                out.setdefault(cur, set())
                if kind == 'OK':
                    cur = None
                continue
            if cur is None:
                continue
            fm = re.match(r'\s*-\s+(\S+?):', line)
            if fm:
                out[cur].add(fm.group(1))
    return out


def compile_ok(py_path):
    import py_compile
    try:
        py_compile.compile(py_path, doraise=True, quiet=2)
        return True
    except Exception:
        return False


def run_one(pyc_path, baseline, rollback=True):
    rec = {'pyc': pyc_path, 'before': None, 'after': None, 'verdict': None}
    ok_py = str(Path(pyc_path).with_suffix('')) + 'OK.py'
    base_bad = baseline.get(pyc_path.replace('\\', '/'))
    before = check_pyc(pyc_path)
    if before is None:
        rec['verdict'] = 'NO-OKPY'
        return rec
    rec['before'] = {'ok': before['ok'], 'functions': before['functions'],
                     'bad': [b[0] for b in before['bad']]}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bak = BACKUP_DIR / (Path(ok_py).name + '.' +
                        str(abs(hash(pyc_path)) % 10 ** 8) + '.bak')
    shutil.copy2(ok_py, bak)

    single = pbv.decompile_single(pyc_path)
    if not single.get('success'):
        shutil.copy2(bak, ok_py)
        rec['verdict'] = 'DECOMPILE-FAIL(rolled back): %s' % single.get('error')
        return rec

    after = check_pyc(pyc_path)
    if after is None or 'error' in after or not compile_ok(ok_py):
        shutil.copy2(bak, ok_py)
        rec['verdict'] = 'BAD-OUTPUT(rolled back)'
        return rec
    rec['after'] = {'ok': after['ok'], 'functions': after['functions'],
                    'bad': [b[0] for b in after['bad']]}

    was_clean = len(rec['before']['bad']) == 0
    is_clean = len(rec['after']['bad']) == 0
    if is_clean and not was_clean:
        rec['verdict'] = 'FLIPPED-CLEAN'
    elif is_clean and was_clean:
        rec['verdict'] = 'CLEAN'
    elif not is_clean and was_clean:
        if rollback:
            shutil.copy2(bak, ok_py)
            rec['verdict'] = 'REGRESSION(rolled back)'
        else:
            rec['verdict'] = 'REGRESSION'
    elif len(rec['after']['bad']) < len(rec['before']['bad']):
        rec['verdict'] = 'IMPROVED'
    elif len(rec['after']['bad']) > len(rec['before']['bad']):
        if rollback:
            shutil.copy2(bak, ok_py)
            rec['verdict'] = 'WORSENED(rolled back)'
        else:
            rec['verdict'] = 'WORSENED'
    else:
        rec['verdict'] = 'UNCHANGED'
    rec['backup'] = str(bak)
    rec['baseline_bad'] = sorted(base_bad) if base_bad is not None else None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--targets', required=True)
    ap.add_argument('--baseline', nargs='+', required=True)
    ap.add_argument('--out', default=None)
    ap.add_argument('--no-rollback', action='store_true')
    ap.add_argument('--budget', type=float, default=280.0)
    ap.add_argument('--offset', type=int, default=0)
    args = ap.parse_args()

    baseline = load_baseline(args.baseline)
    targets = [l.strip().replace('\\', '/') for l in
               io.open(args.targets, encoding='utf-8').read().splitlines() if l.strip()]
    targets = targets[args.offset:]

    import time
    t0 = time.time()
    recs = []
    counts = {}
    for i, p in enumerate(targets, start=1):
        if time.time() - t0 > args.budget:
            print('[GATE] budget reached at %d/%d' % (i - 1, len(targets)))
            break
        if not os.path.exists(p):
            print('  [MISS] %s' % p)
            counts['MISS'] = counts.get('MISS', 0) + 1
            continue
        r = run_one(p, baseline, rollback=not args.no_rollback)
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
        short = p.split('site-packages/')[-1]
        b, a = r['before'], r['after']
        print('  [%-20s] %-58s %s -> %s' % (
            r['verdict'], short,
            '%d/%d' % (b['ok'], b['functions']) if b else '-',
            '%d/%d' % (a['ok'], a['functions']) if a else '-'))
        if a and a['bad'] and r['verdict'] not in ('CLEAN',):
            for nm in a['bad'][:4]:
                print('        bad: %s' % nm)
        recs.append(r)

    print('[GATE] SUMMARY ' + ' '.join('%s=%d' % kv for kv in sorted(counts.items())))
    print('[GATE] processed=%d remaining=%d elapsed=%.0fs' %
          (len(recs), len(targets) - len(recs), time.time() - t0))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        io.open(args.out, 'w', encoding='utf-8').write(
            json.dumps({'counts': counts, 'records': recs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
