#!/usr/bin/env python3
"""pyc 批量验证脚本：反编译 + 字节码 diff + OK.py 生成 + 批量模式 + 累计成功率统计。

提供三种工作模式：
  single <pyc_path> [--ok-py <path>]   反编译单个 pyc + 生成 <name>OK.py + 字节码 diff 报告
  batch  [--index <path>] [--max-count N] [--round N]   批量验证并回写 pyc_index.json
  stats  [--index <path>]               仅打印累计统计

依赖项目根目录下的 pycdc.decompile_pyc 与 testqouter.round1.base.compare_bytecode。

用法示例：
  python scripts/pyc_batch_verify.py single path/to/file.pyc
  python scripts/pyc_batch_verify.py batch --max-count 10 --round 1
  python scripts/pyc_batch_verify.py stats --index pyc_index.json
"""

import argparse
import io
import json
import marshal
import os
import py_compile
import sys
import time
import traceback
import types
from pathlib import Path

# threading 仅用于实现反编译超时控制（Python 标准库）
import threading

# ─── 项目路径设置 ───
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_INDEX_PATH = str(PROJECT_ROOT / 'pyc_index.json')
DECOMPILE_TIMEOUT = 60  # 秒，反编译单文件超时阈值


# ════════════════════════════════════════════════════════════════════
# 内部工具函数
# ════════════════════════════════════════════════════════════════════

def _import_decompiler():
    """延迟导入反编译器与字节码比对工具，便于 --help / stats 等场景无需依赖项目模块。"""
    from pycdc import decompile_pyc
    from testqouter.round1.base import compare_bytecode, get_bytecode_instructions
    return decompile_pyc, compare_bytecode, get_bytecode_instructions


def _decompile_with_timeout(decompile_fn, pyc_path, timeout=DECOMPILE_TIMEOUT):
    """带超时地调用反编译函数。返回 (source, error, traceback_str)。"""
    box = {'source': None, 'error': None, 'tb': None}

    def worker():
        try:
            box['source'] = decompile_fn(pyc_path)
        except Exception as e:  # noqa: BLE001 - 容错捕获所有异常
            box['error'] = f'{type(e).__name__}: {e}'
            box['tb'] = traceback.format_exc()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        # 线程仍在运行，视为超时（daemon 线程会在主进程退出时被回收）
        return None, f'timeout after {timeout}s', None
    return box['source'], box['error'], box['tb']


def _load_pyc_code(pyc_path):
    """加载 pyc 顶层 code object（跳过 16 字节头：magic+flags+timestamp+size）。"""
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def _extract_code_objects(code_obj):
    """递归提取所有 code object，按 co_name 命名。

    <module> 用 '<module>'。同名 code object 后出现的覆盖前者。
    返回 dict: {name: code_object}
    """
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const))
    return result


def _classify_decompile_status(rate, ok_py_generated, py_compile_ok):
    """根据验证结果对 decompile_status 进行分类。

    - 'ok'      : bytecode_match_rate == 1.0 AND py_compile 成功 AND OK.py 已生成
    - 'partial' : 0 < bytecode_match_rate < 1.0（反编译成功但未 100% 匹配）
    - 'failed'  : 反编译或 py_compile 失败（rate == 0.0 或流水线异常）
    - 'pending' : 未验证条目的初始状态（此处不产生）
    """
    if not ok_py_generated or not py_compile_ok:
        return 'failed'
    if rate == 1.0:
        return 'ok'
    if rate > 0.0:
        return 'partial'
    return 'failed'


def _update_index_entry(pyc_path, fields, clear_keys=None, index_path=None):
    """在 pyc_index.json 中查找匹配 pyc_path 的条目并更新字段。

    路径匹配对大小写和分隔符不敏感（Windows 兼容）。
    找到并回写返回 True，否则返回 False。
    """
    if index_path is None:
        index_path = DEFAULT_INDEX_PATH
    index_path = str(index_path)
    index_file = Path(index_path)
    if not index_file.exists():
        return False

    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    target = os.path.normcase(os.path.normpath(pyc_path))
    found = False
    for entry in entries:
        ep = entry.get('path', '')
        if ep and os.path.normcase(os.path.normpath(ep)) == target:
            entry.update(fields)
            for k in (clear_keys or []):
                entry.pop(k, None)
            found = True
            break

    if found:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    return found


# ════════════════════════════════════════════════════════════════════
# 1. 单 pyc 反编译 + OK.py 生成
# ════════════════════════════════════════════════════════════════════

def decompile_single(pyc_path: str, ok_py_path: str = None) -> dict:
    """反编译单个 pyc 并在 pyc 同目录生成 <name>OK.py。

    命名规则：quotation.pyc -> quotationOK.py（去 .pyc 后加 OK.py）。

    返回 dict:
      {success: bool, source: str, ok_py_path: str, error: str}
    """
    pyc_path = str(pyc_path)
    pyc = Path(pyc_path)
    if ok_py_path is None:
        # quotation.pyc -> quotationOK.py
        ok_py_path = str(pyc.with_suffix('')) + 'OK.py'
    else:
        ok_py_path = str(ok_py_path)

    result = {
        'success': False,
        'source': '',
        'ok_py_path': ok_py_path,
        'error': '',
    }

    decompile_fn, _, _ = _import_decompiler()
    source, err, _tb = _decompile_with_timeout(decompile_fn, pyc_path)
    if source is None:
        result['error'] = err or 'decompile returned None'
        return result

    try:
        with open(ok_py_path, 'w', encoding='utf-8') as f:
            f.write(source)
    except OSError as e:
        result['source'] = source
        result['error'] = f'write_ok_py_failed: {type(e).__name__}: {e}'
        return result

    result['success'] = True
    result['source'] = source
    return result


# ════════════════════════════════════════════════════════════════════
# 2. 字节码 diff
# ════════════════════════════════════════════════════════════════════

def bytecode_diff(pyc_path: str, ok_py_path: str) -> dict:
    """比对原 pyc 与反编译 OK.py 的字节码。

    返回 dict:
      {
        total_functions: int,           # 原 pyc 函数总数
        matched_functions: int,         # 字节码一致函数数
        match_rate: float,              # matched/total
        mismatches: [                   # 不一致清单
          {name, orig_count, decomp_count, jump_diffs, true_diffs, first_diff}
        ],
        missing_in_decomp: [str],       # 原 pyc 有但 OK.py 没有的函数
        extra_in_decomp: [str],         # OK.py 有但原 pyc 没有的函数
      }
    """
    _, compare_bytecode, _ = _import_decompiler()

    result = {
        'total_functions': 0,
        'matched_functions': 0,
        'match_rate': 0.0,
        'mismatches': [],
        'missing_in_decomp': [],
        'extra_in_decomp': [],
    }

    # 加载原 pyc 顶层 code object
    try:
        orig_code = _load_pyc_code(pyc_path)
    except Exception as e:
        result['error'] = f'load_pyc_failed: {type(e).__name__}: {e}'
        return result

    orig_map = _extract_code_objects(orig_code)

    # py_compile 编译 OK.py 为 code object
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
    except py_compile.PyCompileError as e:
        result['error'] = f'py_compile_failed: {e}'
        return result
    except SyntaxError as e:
        result['error'] = f'syntax_error: {type(e).__name__}: {e}'
        return result
    except Exception as e:
        result['error'] = f'py_compile_unexpected: {type(e).__name__}: {e}'
        return result

    # 加载编译后的 code object
    try:
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        result['error'] = f'load_compiled_failed: {type(e).__name__}: {e}'
        return result

    decomp_map = _extract_code_objects(decomp_code)

    # 名字集合差异
    orig_names = set(orig_map.keys())
    decomp_names = set(decomp_map.keys())
    common = orig_names & decomp_names

    result['missing_in_decomp'] = sorted(orig_names - decomp_names)
    result['extra_in_decomp'] = sorted(decomp_names - orig_names)
    result['total_functions'] = len(orig_map)

    # 逐个同名 code object 比对
    matched = 0
    mismatches = []
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if cmp.get('match'):
            matched += 1
        else:
            jump_diffs = cmp.get('jump_diffs', [])
            true_diffs = cmp.get('true_diffs', [])
            first_diff = None
            if true_diffs:
                first_diff = true_diffs[0]
            elif jump_diffs:
                first_diff = jump_diffs[0]
            mismatches.append({
                'name': name,
                'orig_count': cmp.get('orig_count', 0),
                'decomp_count': cmp.get('decomp_count', 0),
                'jump_diffs': len(jump_diffs),
                'true_diffs': len(true_diffs),
                'first_diff': first_diff,
            })

    result['matched_functions'] = matched
    result['mismatches'] = mismatches
    total = result['total_functions']
    result['match_rate'] = matched / total if total > 0 else 0.0
    return result


# ════════════════════════════════════════════════════════════════════
# 3. 批量模式
# ════════════════════════════════════════════════════════════════════

def batch_verify(index_path: str = None, max_count: int = None, round_num: int = 1) -> dict:
    """批量验证 pyc_index.json 中的条目。

    对每个 decompile_status != 'ok' 的 pyc 执行：
      1. 反编译生成 OK.py
      2. 字节码 diff
      3. 更新 pyc_index.json 条目
      4. 打印进度

    单个 pyc 失败不中断流程。返回累计统计 dict。
    """
    if index_path is None:
        index_path = DEFAULT_INDEX_PATH
    index_path = str(index_path)
    index_file = Path(index_path)

    if not index_file.exists():
        raise FileNotFoundError(f'pyc_index.json not found: {index_path}')

    with open(index_file, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # 筛选待验证条目（decompile_status != 'ok'）
    pending = [e for e in entries if e.get('decompile_status') != 'ok']
    if max_count is not None:
        pending = pending[:max_count]

    total_pyc = len(entries)
    print(f'[BATCH] index={index_path}')
    print(f'[BATCH] total={total_pyc}, pending={len(pending)}, round={round_num}')
    print('-' * 70)

    for idx, entry in enumerate(pending, start=1):
        pyc_path = entry.get('path', '')
        print(f'[{idx}/{len(pending)}] {pyc_path}')

        if not pyc_path or not os.path.exists(pyc_path):
            entry['decompile_status'] = 'failed'
            entry['error'] = 'pyc file not found'
            entry['bytecode_match_rate'] = 0.0
            entry['ok_py_generated'] = False
            entry['last_tested_round'] = round_num
            print('    FAILED: pyc file not found')
            continue

        # 步骤 1: 反编译 + 生成 OK.py
        try:
            single = decompile_single(pyc_path)
        except Exception as e:
            entry['decompile_status'] = 'failed'
            entry['error'] = f'unexpected: {type(e).__name__}: {e}'
            entry['bytecode_match_rate'] = 0.0
            entry['ok_py_generated'] = False
            entry['last_tested_round'] = round_num
            print(f'    FAILED (unexpected): {e}')
            continue

        if not single['success']:
            entry['decompile_status'] = 'failed'
            entry['error'] = single['error']
            entry['bytecode_match_rate'] = 0.0
            entry['ok_py_generated'] = False
            entry['last_tested_round'] = round_num
            print(f'    FAILED: {single["error"]}')
            continue

        ok_py_path = single['ok_py_path']
        entry['ok_py_generated'] = True

        # 步骤 2: 字节码 diff
        try:
            diff = bytecode_diff(pyc_path, ok_py_path)
        except Exception as e:
            entry['decompile_status'] = 'failed'
            entry['error'] = f'diff_exception: {type(e).__name__}: {e}'
            entry['bytecode_match_rate'] = 0.0
            entry['last_tested_round'] = round_num
            print(f'    DIFF FAILED: {e}')
            continue

        if diff.get('error'):
            entry['decompile_status'] = 'failed'
            entry['error'] = diff['error']
            entry['bytecode_match_rate'] = 0.0
            entry['last_tested_round'] = round_num
            print(f'    DIFF ERROR: {diff["error"]}')
            continue

        # 步骤 3: 更新条目（pipeline 成功完成：decompile + py_compile 均成功）
        rate = diff['match_rate']
        status = _classify_decompile_status(rate, ok_py_generated=True, py_compile_ok=True)
        entry['bytecode_match_rate'] = rate
        entry['decompile_status'] = status
        entry['last_tested_round'] = round_num
        entry.pop('error', None)  # 清除之前可能的失败记录
        print(f'    {status.upper()}: {diff["total_functions"]} funcs, '
              f'{diff["matched_functions"]} matched, rate={rate:.2%}')

    # 写回 pyc_index.json
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print('-' * 70)
    print(f'[BATCH] index written back: {index_path}')

    # 返回累计统计
    return cumulative_stats(index_path)


# ════════════════════════════════════════════════════════════════════
# 4. 累计成功率统计
# ════════════════════════════════════════════════════════════════════

def cumulative_stats(index_path: str = None) -> dict:
    """读取 pyc_index.json，统计所有已验证 pyc（last_tested_round > 0）的累计成功率。

    返回 dict:
      {total_pyc, verified_pyc, ok_pyc, partial_pyc, failed_pyc,
       total_functions, matched_functions, cumulative_match_rate}
    """
    if index_path is None:
        index_path = DEFAULT_INDEX_PATH
    index_path = str(index_path)
    index_file = Path(index_path)

    empty = {
        'total_pyc': 0,
        'verified_pyc': 0,
        'ok_pyc': 0,
        'partial_pyc': 0,
        'failed_pyc': 0,
        'total_functions': 0,
        'matched_functions': 0,
        'cumulative_match_rate': 0.0,
    }

    if not index_file.exists():
        return empty

    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except (json.JSONDecodeError, OSError):
        return empty

    total_pyc = len(entries)
    verified_pyc = 0
    ok_pyc = 0
    partial_pyc = 0
    failed_pyc = 0
    total_functions = 0
    matched_functions = 0

    for e in entries:
        if e.get('last_tested_round', 0) > 0:
            verified_pyc += 1
            status = e.get('decompile_status')
            if status == 'ok':
                ok_pyc += 1
            elif status == 'partial':
                partial_pyc += 1
            elif status == 'failed':
                failed_pyc += 1
            fc = e.get('function_count', 0)
            rate = e.get('bytecode_match_rate', 0.0)
            total_functions += fc
            # 按比例折算匹配函数数
            matched_functions += int(round(fc * rate))

    cumulative_rate = matched_functions / total_functions if total_functions > 0 else 0.0
    return {
        'total_pyc': total_pyc,
        'verified_pyc': verified_pyc,
        'ok_pyc': ok_pyc,
        'partial_pyc': partial_pyc,
        'failed_pyc': failed_pyc,
        'total_functions': total_functions,
        'matched_functions': matched_functions,
        'cumulative_match_rate': cumulative_rate,
    }


# ════════════════════════════════════════════════════════════════════
# CLI 命令处理
# ════════════════════════════════════════════════════════════════════

def _print_diff_report(diff: dict, decompile_status: str = None):
    """打印单个 pyc 的字节码 diff 报告。"""
    print()
    print('字节码 diff 报告:')
    if decompile_status is not None:
        print(f'  decompile_status:   {decompile_status}')
    print(f'  total_functions:   {diff["total_functions"]}')
    print(f'  matched_functions: {diff["matched_functions"]}')
    print(f'  match_rate:        {diff["match_rate"]:.2%}')
    print(f'  missing_in_decomp: {diff["missing_in_decomp"]}')
    print(f'  extra_in_decomp:   {diff["extra_in_decomp"]}')
    if diff.get('error'):
        print(f'  error: {diff["error"]}')
        return
    if diff['mismatches']:
        print(f'  mismatches ({len(diff["mismatches"])}):')
        for m in diff['mismatches'][:10]:
            print(f'    - {m["name"]}: orig={m["orig_count"]} decomp={m["decomp_count"]} '
                  f'jump_diffs={m["jump_diffs"]} true_diffs={m["true_diffs"]}')
            if m['first_diff']:
                print(f'      first_diff: {m["first_diff"]}')


def _print_stats(stats: dict):
    """打印累计统计。"""
    print('=' * 70)
    print('累计统计:')
    print(f'  total_pyc:             {stats["total_pyc"]}')
    print(f'  verified_pyc:          {stats["verified_pyc"]}')
    print(f'  ok_pyc:                {stats["ok_pyc"]}')
    print(f'  partial_pyc:           {stats["partial_pyc"]}')
    print(f'  failed_pyc:            {stats["failed_pyc"]}')
    print(f'  total_functions:       {stats["total_functions"]}')
    print(f'  matched_functions:     {stats["matched_functions"]}')
    print(f'  cumulative_match_rate: {stats["cumulative_match_rate"]:.2%}')
    print('=' * 70)


def _cmd_single(pyc_path: str, ok_py_path: str) -> int:
    """single 子命令：反编译 + 生成 OK.py + 字节码 diff + 打印报告 + 回写 pyc_index.json。"""
    pyc_path = str(Path(pyc_path).resolve())
    print(f'[SINGLE] {pyc_path}')

    single = decompile_single(pyc_path, ok_py_path)
    if not single['success']:
        print(f'  FAILED: {single["error"]}')
        _update_index_entry(pyc_path, {
            'decompile_status': 'failed',
            'bytecode_match_rate': 0.0,
            'ok_py_generated': False,
            'error': single['error'],
        })
        return 1

    print(f'  OK.py: {single["ok_py_path"]}')
    print(f'  source: {len(single["source"])} chars')

    diff = bytecode_diff(pyc_path, single['ok_py_path'])

    if diff.get('error'):
        # py_compile 或加载失败：decompile 成功但 recompile 失败
        status = _classify_decompile_status(0.0, ok_py_generated=True, py_compile_ok=False)
        rate = 0.0
        fields = {
            'decompile_status': status,
            'bytecode_match_rate': rate,
            'ok_py_generated': True,
            'error': diff['error'],
        }
        clear_keys = None
    else:
        rate = diff['match_rate']
        status = _classify_decompile_status(rate, ok_py_generated=True, py_compile_ok=True)
        fields = {
            'decompile_status': status,
            'bytecode_match_rate': rate,
            'ok_py_generated': True,
        }
        clear_keys = ['error']  # 清除之前可能的失败记录

    _print_diff_report(diff, decompile_status=status)
    _update_index_entry(pyc_path, fields, clear_keys=clear_keys)
    return 0


def _cmd_batch(index_path: str, max_count: int, round_num: int) -> int:
    """batch 子命令：批量验证模式。"""
    print(f'[BATCH] index={index_path or DEFAULT_INDEX_PATH}, '
          f'max_count={max_count}, round={round_num}')
    stats = batch_verify(index_path, max_count, round_num)
    print()
    _print_stats(stats)
    return 0


def _cmd_stats(index_path: str) -> int:
    """stats 子命令：仅打印累计统计。"""
    stats = cumulative_stats(index_path)
    _print_stats(stats)
    return 0


# ════════════════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='pyc 批量验证工具：反编译 + 字节码 diff + OK.py 生成 + 累计统计',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s single path/to/file.pyc
  %(prog)s single path/to/file.pyc --ok-py path/to/fileOK.py
  %(prog)s batch --max-count 10 --round 1
  %(prog)s batch --index pyc_index.json --round 2
  %(prog)s stats --index pyc_index.json
        """,
    )
    sub = parser.add_subparsers(dest='command')

    # single 子命令
    p_single = sub.add_parser('single', help='反编译单个 pyc + 生成 OK.py + 字节码 diff')
    p_single.add_argument('pyc_path', help='pyc 文件路径')
    p_single.add_argument('--ok-py', default=None,
                           help='OK.py 输出路径（默认: <name>OK.py，与 pyc 同目录）')

    # batch 子命令
    p_batch = sub.add_parser('batch', help='批量验证模式（回写 pyc_index.json）')
    p_batch.add_argument('--index', default=None,
                          help=f'pyc_index.json 路径（默认: {DEFAULT_INDEX_PATH}）')
    p_batch.add_argument('--max-count', type=int, default=None,
                          help='限制处理数量（用于单轮测试）')
    p_batch.add_argument('--round', type=int, default=1,
                          help='当前轮次标记（写入 last_tested_round）')

    # stats 子命令
    p_stats = sub.add_parser('stats', help='仅打印累计统计')
    p_stats.add_argument('--index', default=None,
                          help=f'pyc_index.json 路径（默认: {DEFAULT_INDEX_PATH}）')

    args = parser.parse_args()

    if args.command == 'single':
        return _cmd_single(args.pyc_path, args.ok_py)
    elif args.command == 'batch':
        return _cmd_batch(args.index, args.max_count, args.round)
    elif args.command == 'stats':
        return _cmd_stats(args.index)

    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
