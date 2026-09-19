#!/usr/bin/env python3
"""回归定位（bisect）矩阵：对一组 pyc，在多个提交处各跑一次反编译，得到
"文件 × 提交" 的字节码匹配率矩阵，从而定位每个文件的退化是从哪个提交开始的。

关键设计：
  * 每个提交用一个独立 git worktree，保证用的是该提交处的 core/ 代码；
  * 目标 pyc 先复制到临时镜像目录再跑，OK.py 只写在镜像里，
    绝不覆盖仓库 site-packages 下的真实 OK.py；
  * 自定义索引文件驱动 batch 模式（batch 只跑 decompile_status != 'ok' 的条目，
    故初始一律置 'partial'）。

用法：
  python scripts/regress_bisect.py --targets _r5_audit_targets.txt \
      --commits 3cf6dce2,51dde1da,739d342f,c33af45b \
      --wt-root D:/temp/pcdc_wt --mirror D:/temp/pcdc_mirror \
      --out _r5_bisect_matrix.json
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _rel(p: str) -> str:
    return os.path.relpath(p, str(PROJECT_ROOT)).replace('\\', '/')


def ensure_worktree(commit: str, wt_root: str) -> str:
    d = os.path.join(wt_root, commit)
    if os.path.isdir(os.path.join(d, '.git')) or os.path.isfile(os.path.join(d, '.git')):
        return d
    os.makedirs(wt_root, exist_ok=True)
    r = subprocess.run(['git', 'worktree', 'add', '--detach', d, commit],
                       cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'worktree add failed for {commit}: {r.stderr.strip()}')
    return d


def mirror_targets(targets, mirror: str):
    """把目标 pyc 复制到镜像目录，返回 {原路径: 镜像路径}。"""
    mapping = {}
    for p in targets:
        rel = _rel(p)
        dst = os.path.join(mirror, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(p, dst)
        mapping[p] = dst
    return mapping


def sync_driver(wt_dir: str) -> str:
    """把当前分支的 pyc_batch_verify.py 复制进 worktree。

    早期提交里该驱动脚本尚不存在（例如 3cf6dce2 就完全没有 scripts/ 目录），
    直接用 worktree 自带的脚本会让整轮测量静默失败（所有条目 status 不变、
    rate 为 None），看起来像"全部变 0"。驱动脚本只是 I/O 外壳，真正决定结果的
    是 core/ 代码，因此这里统一使用当前版本，保证各提交的比较口径一致。
    """
    src = PROJECT_ROOT / 'scripts' / 'pyc_batch_verify.py'
    dst_dir = Path(wt_dir) / 'scripts'
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst_dir / 'pyc_batch_verify.py'))
    return str(dst_dir / 'pyc_batch_verify.py')


def run_commit(wt_dir: str, commit: str, mapping, mirror: str, log_dir: str):
    """在 wt_dir 的代码上跑一遍 batch，返回 {镜像路径: rate 或 status}。"""
    idx_path = os.path.join(mirror, f'index_{commit}.json')
    entries = [{'path': dst, 'decompile_status': 'partial'} for dst in mapping.values()]
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    script = sync_driver(wt_dir)
    os.makedirs(log_dir, exist_ok=True)
    log = os.path.join(log_dir, f'batch_{commit}.log')
    py = sys.executable
    with open(log, 'w', encoding='utf-8') as lf:
        subprocess.run([py, script, 'batch', '--index', idx_path, '--round', '0'],
                       cwd=wt_dir, stdout=lf, stderr=subprocess.STDOUT)

    out = {}
    for e in json.load(open(idx_path, encoding='utf-8')):
        out[e['path']] = {
            'status': e.get('decompile_status'),
            'rate': e.get('bytecode_match_rate'),
            'matched': e.get('matched_functions'),
            'total': e.get('function_count'),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--targets', required=True)
    ap.add_argument('--commits', required=True)
    ap.add_argument('--wt-root', default='D:/temp/pcdc_wt')
    ap.add_argument('--mirror', default='D:/temp/pcdc_mirror')
    ap.add_argument('--log-dir', default='D:/temp/pcdc_logs')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    targets = [l.strip() for l in open(args.targets, encoding='utf-8') if l.strip()]
    commits = [c.strip() for c in args.commits.split(',') if c.strip()]

    mapping = mirror_targets(targets, args.mirror)
    print(f'targets={len(targets)} mirrored into {args.mirror}', flush=True)

    matrix = {p: {} for p in targets}
    for c in commits:
        wt = ensure_worktree(c, args.wt_root)
        print(f'--- running {c} in {wt} ---', flush=True)
        res = run_commit(wt, c, mapping, args.mirror, args.log_dir)
        for orig, mp in mapping.items():
            r = res.get(mp, {})
            matrix[orig][c] = r
        n_ok = sum(1 for v in res.values() if v.get('status') == 'ok')
        print(f'    done {c}: ok={n_ok}/{len(res)}', flush=True)

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, ensure_ascii=False, indent=2)
        print(f'written {args.out}')

    # 打印矩阵摘要
    print('\n' + '=' * 100)
    hdr = f'{"file":32s} ' + ' '.join(f'{c[:8]:>9s}' for c in commits)
    print(hdr)
    print('-' * len(hdr))
    for p in targets:
        name = os.path.basename(p)
        cells = []
        for c in commits:
            r = matrix[p][c].get('rate')
            cells.append(f'{r:9.4f}' if isinstance(r, (int, float)) else f'{str(r):>9s}')
        print(f'{name:32s} ' + ' '.join(cells))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
