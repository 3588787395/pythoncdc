#!/usr/bin/env python3
"""OK 轮次审计：用 git 历史中已提交的 <name>OK.py 作为"该文件当时是否真的 100%"的证据。

原理：pyc_batch_verify 的 batch 模式只处理 decompile_status != 'ok' 的条目，
一旦某文件被标成 ok 就永不复验 —— 索引里的 ok 标记可能是过期的（比较工具
归一化被移除、或此前变更已使其退化）。但 <name>OK.py 是**当时反编译器的真实
输出**并随提交入库，因此可以把历史版本的 OK.py 拿出来重新做字节码比对：
- rate == 1.0  → 该提交处该文件确为 ok（索引标记属实）
- rate  < 1.0  → 该提交处该文件实为 partial（索引标记虚高）

用法：
  python scripts/audit_ok_history.py --targets _r5_audit_targets.txt \
      --commits 3cf6dce2:c33af45b --out _r5_ok_history.json
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_verify_module():
    p = PROJECT_ROOT / 'scripts' / 'pyc_batch_verify.py'
    spec = importlib.util.spec_from_file_location('_pbv', str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _rel(pyc_path: str) -> str:
    return os.path.relpath(pyc_path, str(PROJECT_ROOT)).replace('\\', '/')


def _ok_py_rel(pyc_path: str) -> str:
    r = _rel(pyc_path)
    return r[: -len('.pyc')] + 'OK.py' if r.endswith('.pyc') else r + 'OK.py'


def _git_show(commit: str, repo_rel_path: str):
    """返回该提交处该文件的字节内容；文件不存在返回 None。"""
    try:
        out = subprocess.run(
            ['git', 'show', f'{commit}:{repo_rel_path}'],
            cwd=str(PROJECT_ROOT), capture_output=True, timeout=60,
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--targets', required=True, help='每行一个 pyc 绝对路径的文件')
    ap.add_argument('--commits', required=True, help='逗号分隔的 commit 列表，按由旧到新')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    pbv = _load_verify_module()
    targets = [l.strip() for l in open(args.targets, encoding='utf-8') if l.strip()]
    commits = [c.strip() for c in args.commits.split(',') if c.strip()]

    rows = []
    tmpdir = tempfile.mkdtemp(prefix='okhist_')
    for i, pyc in enumerate(targets, 1):
        base = os.path.basename(pyc)
        row = {'pyc': pyc, 'name': base, 'rel': _rel(pyc), 'hist': {}}
        ok_rel = _ok_py_rel(pyc)
        for c in commits:
            blob = _git_show(c, ok_rel)
            if blob is None:
                row['hist'][c] = None
                continue
            tmp = os.path.join(tmpdir, f'{i}_{c}.py')
            with open(tmp, 'wb') as f:
                f.write(blob)
            try:
                d = pbv.bytecode_diff(pyc, tmp)
                if d.get('error'):
                    row['hist'][c] = {'error': d['error']}
                else:
                    row['hist'][c] = {
                        'rate': round(d['match_rate'], 6),
                        'total': d['total_functions'],
                        'matched': d['matched_functions'],
                    }
            except Exception as e:
                row['hist'][c] = {'error': f'{type(e).__name__}: {e}'}
        rows.append(row)
        h = row['hist']
        desc = ' | '.join(
            f'{c}: ' + ('NO_File' if h[c] is None else
                        ('ERR' if 'error' in h[c] else f"{h[c]['rate']:.4f}"))
            for c in commits
        )
        print(f'[{i}/{len(targets)}] {base:28s} {desc}', flush=True)

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f'\nwritten: {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
