#!/usr/bin/env python3
"""R102 分片断点续跑批量验证驱动（只读测量，禁止写回 pyc_index.json）。

从 pyc_index.json 读取全部条目，按子集选择 pyc，逐个调用
scripts/pyc_batch_verify.py 的 decompile_single + bytecode_diff，
把 matched/total/rate/status 逐条写入 progress.json（断点续跑）。

用法:
  python chunked_verify.py --subset partial   --limit 20 --offset 0 --state progress.json
  python chunked_verify.py --subset ok-sample --limit 15 --offset 0 --state progress.json
  python chunked_verify.py --list-only        （只打印选中清单不执行）

说明:
  - 单个 pyc 在独立子进程内处理，父进程看门狗 90 秒，超时标记 timeout 并继续。
  - 每处理完一条立即落盘 progress.json，可随时 Ctrl-C / 断点续跑。
  - 不调用 _update_index_entry，绝不写回主索引；OK.py 由工具照常生成。
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import traceback
from pathlib import Path

# ─── 项目根定位：向上找包含 pycdc.py 的目录 ───
HERE = Path(__file__).resolve().parent


def _find_project_root():
    p = HERE
    for _ in range(8):
        if (p / 'pycdc.py').exists():
            return p
        p = p.parent
    raise RuntimeError('project root (pycdc.py) not found from ' + str(HERE))


PROJECT_ROOT = _find_project_root()
INDEX_PATH = PROJECT_ROOT / 'pyc_index.json'
WATCHDOG_SECONDS = 90

# 子进程 worker 必须是模块级函数（Windows spawn）


def _worker(conn, pyc_path):
    result = {'pyc': pyc_path}
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
        from scripts.pyc_batch_verify import decompile_single, bytecode_diff

        single = decompile_single(pyc_path)
        result['decompile_success'] = bool(single.get('success'))
        result['ok_py_path'] = single.get('ok_py_path', '')
        if not single.get('success'):
            result['error'] = single.get('error', 'decompile returned None')
            result['total_functions'] = 0
            result['matched_functions'] = 0
            result['match_rate'] = 0.0
            result['mismatches'] = []
        else:
            diff = bytecode_diff(pyc_path, single['ok_py_path'])
            if diff.get('error'):
                result['error'] = diff['error']
                result['total_functions'] = diff.get('total_functions', 0)
                result['matched_functions'] = 0
                result['match_rate'] = 0.0
                result['mismatches'] = []
            else:
                rate = diff['match_rate']
                result['error'] = ''
                result['total_functions'] = diff['total_functions']
                result['matched_functions'] = diff['matched_functions']
                result['match_rate'] = rate
                result['mismatches'] = diff['mismatches']
                result['missing_in_decomp'] = diff['missing_in_decomp']
                result['extra_in_decomp'] = diff['extra_in_decomp']
                if rate == 1.0 and not diff['mismatches']:
                    result['status'] = 'ok'
                elif rate > 0.0:
                    result['status'] = 'partial'
                else:
                    result['status'] = 'failed'
    except Exception:  # noqa: BLE001
        result.setdefault('decompile_success', False)
        result['worker_exception'] = traceback.format_exc()
        result.setdefault('error', 'worker exception')
        result.setdefault('total_functions', 0)
        result.setdefault('matched_functions', 0)
        result.setdefault('match_rate', 0.0)
        result.setdefault('mismatches', [])
        result.setdefault('status', 'failed')
    finally:
        try:
            conn.send(result)
            conn.close()
        except Exception:  # noqa: BLE001
            pass


def load_index():
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def select_subset(entries, subset):
    if subset == 'partial':
        sel = [e for e in entries if e.get('decompile_status') == 'partial']
    elif subset == 'ok-sample':
        ok_sorted = sorted(
            (e for e in entries if e.get('decompile_status') == 'ok'),
            key=lambda e: e.get('path', ''))
        k = 30
        n = len(ok_sorted)
        picked, seen = [], set()
        for i in range(k):
            idx = i * n // k
            if idx not in seen:
                seen.add(idx)
                picked.append(ok_sorted[idx])
        sel = picked
    elif subset == 'all':
        sel = list(entries)
    else:
        raise ValueError(f'unknown subset: {subset}')
    return sel


def run_chunk(sel, state_path, limit, offset, budget_seconds):
    # 载入断点
    progress = {'meta': {}, 'results': {}}
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)

    window = sel[offset: offset + limit] if limit is not None else sel[offset:]
    todo = []
    for e in window:
        p = e['path']
        if p not in progress['results']:
            todo.append(e)
    print(f'[CHUNK] window={len(window)} offset={offset} '
          f'pending={len(todo)} already-done={len(window) - len(todo)}')
    if not todo:
        print('[CHUNK] nothing to do')
        return

    t_start = time.time()
    done = interrupted = timed_out = 0
    ctx = mp.get_context('spawn')

    for i, e in enumerate(todo, start=1):
        elapsed_total = time.time() - t_start
        if budget_seconds and elapsed_total > budget_seconds:
            print(f'[BUDGET] {elapsed_total:.0f}s > {budget_seconds}s, stop before #{i}')
            interrupted = len(todo) - i + 1
            break

        pyc_path = e['path']
        exists = os.path.exists(pyc_path)
        rec = {
            'pyc': pyc_path,
            'index_status': e.get('decompile_status'),
            'index_rate': e.get('bytecode_match_rate'),
            'index_function_count': e.get('function_count'),
            'measured_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        if not exists:
            rec.update({'status': 'missing', 'error': 'pyc file not found',
                        'total_functions': 0, 'matched_functions': 0,
                        'match_rate': 0.0, 'elapsed_s': 0.0})
            progress['results'][pyc_path] = rec
            _flush(state_path, progress)
            print(f'[{i}/{len(todo)}] MISSING {pyc_path}')
            continue

        parent_conn, child_conn = mp.Pipe(duplex=False)
        proc = ctx.Process(target=_worker, args=(child_conn, pyc_path), daemon=True)
        t0 = time.time()
        proc.start()
        child_conn.close()  # 父进程侧关闭写端
        proc.join(timeout=WATCHDOG_SECONDS)

        res = None
        if parent_conn.poll():
            try:
                res = parent_conn.recv()
            except EOFError:
                res = None
        dt = time.time() - t0

        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=5)
            rec.update({'status': 'timeout',
                        'error': f'watchdog: exceeded {WATCHDOG_SECONDS}s',
                        'total_functions': 0, 'matched_functions': 0,
                        'match_rate': 0.0, 'elapsed_s': round(dt, 2)})
            timed_out += 1
            tag = 'TIMEOUT'
        elif res is None:
            rec.update({'status': 'crashed', 'error': 'no result from worker',
                        'total_functions': 0, 'matched_functions': 0,
                        'match_rate': 0.0, 'elapsed_s': round(dt, 2),
                        'worker_traceback': '(no result)'})
            tag = 'CRASHED'
        else:
            rec.update(res)
            rec['elapsed_s'] = round(dt, 2)
            if 'worker_exception' in res:
                rec['worker_traceback'] = res['worker_exception']
            tag = str(res.get('status', '?')).upper()

        progress['results'][pyc_path] = rec
        _flush(state_path, progress)
        done += 1
        extra = ''
        if 'match_rate' in rec and rec.get('status') not in ('timeout',):
            extra = (f" total={rec.get('total_functions')} "
                     f"matched={rec.get('matched_functions')} "
                     f"rate={rec.get('match_rate'):.4f}")
        err = rec.get('error') or rec.get('worker_exception', '') or ''
        print(f'[{i}/{len(todo)}] {tag} ({rec["elapsed_s"]:.1f}s) {Path(pyc_path).name}'
              f'{extra}' + (f' ERR={err[:120]}' if err and tag != 'OK' else ''))

    print(f'[CHUNK] done={done} timeout={timed_out} skipped-by-budget={interrupted} '
          f'wall={time.time() - t_start:.0f}s')


def _json_default(o):
    """dis._Unknown 等不可序列化哨兵对象转为可读字符串。"""
    return f'<{type(o).__name__}:{o!r}>'


def _flush(state_path, progress):
    tmp = state_path.with_suffix('.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=1, default=_json_default)
    os.replace(str(tmp), str(state_path))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--subset', choices=['partial', 'ok-sample', 'all'], default='partial')
    ap.add_argument('--limit', type=int, default=None)
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--state', default=str(HERE / 'progress.json'))
    ap.add_argument('--budget-seconds', type=int, default=250,
                    help='本条命令的墙钟预算，超过即安全停机（默认 250s）')
    ap.add_argument('--list-only', action='store_true')
    args = ap.parse_args()

    entries = load_index()
    sel = select_subset(entries, args.subset)
    print(f'[SELECT] subset={args.subset} selected={len(sel)} '
          f'(index total={len(entries)})')

    if args.list_only:
        for i, e in enumerate(sel):
            mark = '' if i >= args.offset else ' (before offset)'
            print(f'  [{i}] {e["path"]} status={e.get("decompile_status")} '
                  f'rate={e.get("bytecode_match_rate")}{mark}')
        return 0

    run_chunk(sel, Path(args.state), args.limit, args.offset, args.budget_seconds)
    return 0


if __name__ == '__main__':
    sys.exit(main())
