#!/usr/bin/env python3
"""R20 测试工程师：反编译 quotation.pyc 并生成产物（输出 /tmp/r20_decompiled.py）。

R20 是 V2 10 轮迭代的最终验证与收尾轮次，沿用 R19 的反编译流程与超时上限。
"""
import subprocess, sys, time

PYC = '/workspace/quotation.pyc'
OUT = '/tmp/r20_decompiled.py'


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
