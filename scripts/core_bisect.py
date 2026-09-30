#!/usr/bin/env python3
"""低成本逐提交 bisect：只替换 core/ 目录，不建整棵 git worktree。

适用前提：候选提交之间的差异只落在 core/ 内（可用
`git diff --stat A..B -- . ':!core'` 验证）。相比 regress_bisect.py
每次都要 `git worktree add`（全量检出，单个可耗时 1-2 分钟），
本脚本直接在仓库工作树里 `git checkout <commit> -- core/`，
单次切换是秒级，适合 10+ 个提交的粗细粒度排查。

安全保证：
  * 只动 core/ 一个目录，跑完必定 `git checkout HEAD -- core/` 还原；
  * 目标 pyc 从镜像目录读取，OK.py 只写镜像，绝不覆盖仓库 site-packages；
  * 使用独立索引文件，不触碰 pyc_index.json。

用法：
  python scripts/core_bisect.py --targets _r5_bisect5.txt \
      --commits 3cf6dce2,50548e37,...,51dde1da \
      --mirror D:/temp/pcdc_mirror_cb --out _r5_core_bisect.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRIVER = PROJECT_ROOT / 'scripts' / 'pyc_batch_verify.py'


def _rel(p: str) -> str:
    return os.path.relpath(p, str(PROJECT_ROOT)).replace('\\', '/')


def mirror_targets(targets, mirror: str):
    mapping = {}
    for p in targets:
        dst = os.path.join(mirror, _rel(p))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(p, dst)
        mapping[p] = dst
    return mapping


def _clear_pycache():
    for root, dirs, _ in os.walk(PROJECT_ROOT / 'core'):
        for d in list(dirs):
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                dirs.remove(d)


def _git(*args):
    return subprocess.run(['git', *args], cwd=str(PROJECT_ROOT),
                          capture_output=True, text=True, encoding='utf-8')


def run_one(commit: str, mapping, idx_path: str):
    entries = [{'path': dst, 'decompile_status': 'partial'} for dst in mapping.values()]
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    r = subprocess.run([sys.executable, str(DRIVER), 'batch',
                        '--index', idx_path, '--round', '0'],
                       cwd=str(PROJECT_ROOT), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        print(f'    [warn] driver rc={r.returncode} {r.stderr[-200:]}', flush=True)

    out = {}
    for e in json.load(open(idx_path, encoding='utf-8')):
        out[e['path']] = {'status': e.get('decompile_status'),
                          'rate': e.get('bytecode_match_rate')}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--targets', required=True)
    ap.add_argument('--commits', required=True)
    ap.add_argument('--mirror', default='D:/temp/pcdc_mirror_cb')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    targets = [l.strip() for l in open(args.targets, encoding='utf-8') if l.strip()]
    commits = [c.strip() for c in args.commits.split(',') if c.strip()]
    mapping = mirror_targets(targets, args.mirror)
    idx_path = os.path.join(args.mirror, 'index_core_bisect.json')

    print(f'targets={len(targets)} commits={len(commits)} mirror={args.mirror}', flush=True)

    if _git('status', '--porcelain', 'core').stdout.strip():
        print('!! core/ 有未提交改动，先提交或还原再跑', flush=True)
        return 2

    matrix = {p: {} for p in targets}
    try:
        for c in commits:
            if _git('checkout', c, '--', 'core/').returncode != 0:
                print(f'!! checkout {c} failed', flush=True)
                continue
            _clear_pycache()
            res = run_one(c, mapping, idx_path)
            for orig, mp in mapping.items():
                matrix[orig][c] = res.get(mp, {})
            line = ' | '.join(
                f"{os.path.basename(p)}=" + (
                    f"{matrix[p][c].get('rate'):.4f}" if isinstance(matrix[p][c].get('rate'), (int, float))
                    else str(matrix[p][c].get('status')))
                for p in targets)
            print(f'[{c}] {line}', flush=True)
    finally:
        print('restoring core/ ...', flush=True)
        _git('checkout', 'HEAD', '--', 'core/')
        _clear_pycache()
        # 防污染自检：checkout 后 core/ 必须与 HEAD 完全一致。
        # 早期版本的 finally 曾静默失败，导致工作区残留旧提交的 core/，
        # 后续测量全部在错误代码上跑（表现为"同一文件时而 100% 时而 50%"）。
        st = _git('status', '--porcelain', 'core').stdout.strip()
        if st:
            print(f'!! 还原后 core/ 仍不干净，请手动 git checkout HEAD -- core/\n{st}', flush=True)
            return 3
        print('core/ restored clean', flush=True)

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, ensure_ascii=False, indent=2)
        print(f'written {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
