#!/usr/bin/env python3
"""R21 测试工程师：反编译 quotation.pyc 并生成产物（输出 /tmp/r21_decompiled.py）。

R21 是 V3 10 轮迭代的首轮，重点攻克 get_str_data 的 BUILD_CONST_KEY_MAP+STORE_SUBSCR
dict 构造消费模式。沿用 V2 round_20 的反编译流程与超时上限。
"""
import subprocess, sys, time

PYC = '/workspace/quotation.pyc'
OUT = '/tmp/r21_decompiled.py'


def main():
    t0 = time.time()
    r = subprocess.run(
        [sys.executable, '/workspace/pycdc.py', '--region', PYC],
        capture_output=True, text=True, timeout=240,
    )
    if r.returncode != 0:
        print(f'[decompile] FAILED rc={r.returncode}', file=sys.stderr)
        print(r.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(r.stdout)
    elapsed = time.time() - t0
    print(f'[decompile] pyc={PYC}')
    print(f'[decompile] out={OUT}')
    print(f'[decompile] elapsed_s={elapsed:.2f}')
    print(f'[decompile] src_len={len(r.stdout)}')
    print(f'[decompile] src_lines={r.stdout.count(chr(10))}')


if __name__ == '__main__':
    main()
