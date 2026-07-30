#!/usr/bin/env python3
"""构建 pyc 文件索引。

递归扫描 site-packages 目录下所有 .pyc 文件，提取元信息（路径、大小、
code object 数量等），并生成 pyc_index.json 供后续反编译流水线使用。

用法：
    python scripts/pyc_index_builder.py
    python scripts/pyc_index_builder.py --site-packages <path> --output <path>
"""
import argparse
import json
import marshal
import os
import sys
import types
from pathlib import Path


def count_code_objects(code):
    """递归统计 code object 数量（包含自身）。"""
    count = 1  # 自身
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            count += count_code_objects(const)
    return count


def load_pyc_code(pyc_path):
    """加载 pyc 并返回顶层 code object，失败返回 None。

    跳过 pyc 头（前 16 字节：magic 4B + flags 4B + timestamp 4B + size 4B，
    适用于 Python 3.7+）。
    """
    with open(pyc_path, 'rb') as f:
        f.read(16)  # 跳过 pyc 头
        return marshal.load(f)


def build_entry(pyc_path, site_packages_root):
    """为单个 pyc 文件构建索引条目。"""
    # 使用正斜杠统一格式
    abs_path = str(pyc_path.resolve()).replace(os.sep, '/')
    size = pyc_path.stat().st_size
    entry = {
        'path': abs_path,
        'size': size,
        'function_count': 0,
        'decompile_status': 'pending',
        'bytecode_match_rate': 0.0,
        'ok_py_generated': False,
        'last_tested_round': 0,
    }
    try:
        code = load_pyc_code(pyc_path)
        if isinstance(code, types.CodeType):
            entry['function_count'] = count_code_objects(code)
        else:
            # marshal.load 返回非 code object（极少见），标记为失败
            entry['decompile_status'] = 'failed'
            entry['error'] = 'top-level object is not a code object'
    except Exception as exc:  # noqa: BLE001 - 容错：任何加载失败都记录
        entry['decompile_status'] = 'failed'
        entry['error'] = f'{type(exc).__name__}: {exc}'
    return entry


def find_pyc_files(site_packages_dir):
    """递归查找 site-packages 目录下所有 .pyc 文件。"""
    root = Path(site_packages_dir)
    if not root.exists():
        return []
    # 使用 rglob 递归查找
    return sorted(root.rglob('*.pyc'))


def main():
    parser = argparse.ArgumentParser(
        description='扫描 pyc 文件并生成 pyc_index.json 索引'
    )
    default_root = Path(__file__).resolve().parent.parent / 'site-packages'
    default_output = Path(__file__).resolve().parent.parent / 'pyc_index.json'
    parser.add_argument(
        '--site-packages',
        default=str(default_root),
        help=f'site-packages 目录路径（默认: {default_root}）',
    )
    parser.add_argument(
        '--output',
        default=str(default_output),
        help=f'输出 JSON 文件路径（默认: {default_output}）',
    )
    args = parser.parse_args()

    site_packages_dir = Path(args.site_packages).resolve()
    output_path = Path(args.output).resolve()

    if not site_packages_dir.exists():
        print(f'[ERROR] site-packages 目录不存在: {site_packages_dir}', file=sys.stderr)
        sys.exit(1)

    print(f'[INFO] 扫描目录: {site_packages_dir}')
    print(f'[INFO] 输出文件: {output_path}')

    pyc_files = find_pyc_files(site_packages_dir)
    total = len(pyc_files)
    print(f'[INFO] 发现 .pyc 文件: {total} 个')

    entries = []
    success_count = 0
    failed_count = 0

    for idx, pyc_path in enumerate(pyc_files, start=1):
        entry = build_entry(pyc_path, site_packages_dir)
        entries.append(entry)
        if entry['decompile_status'] == 'failed':
            failed_count += 1
        else:
            success_count += 1

        # 每处理 20 个文件打印一次进度
        if idx % 20 == 0 or idx == total:
            print(f'[PROGRESS] {idx}/{total} '
                  f'(成功: {success_count}, 失败: {failed_count})')

    # 按 path 字母序排序
    entries.sort(key=lambda e: e['path'])

    # 写入 JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # 总结
    print('\n===== 总结 =====')
    print(f'总文件数: {total}')
    print(f'成功加载数: {success_count}')
    print(f'失败数: {failed_count}')
    print(f'索引已写入: {output_path}')


if __name__ == '__main__':
    main()
