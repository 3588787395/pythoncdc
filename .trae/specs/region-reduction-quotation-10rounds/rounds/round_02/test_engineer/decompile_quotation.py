"""轮 2 测试工程师：反编译 quotation.pyc（区域归约路径）。

调用 decompile_pyc(pyc, use_cfg=False, cfg_hybrid=False)（内部 use_region=True，
走 core/cfg/region_analyzer.py 的 11 个 _identify_*_regions 方法）。

产物：
- /tmp/r2_decompiled.py  反编译产物（只读，禁止修改）

约束：所有命令 ≤300 秒，禁止修改反编译产物，禁止修改 core/cfg/ 下源码。
"""
import sys
import time

sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'
OUT = '/tmp/r2_decompiled.py'


def main() -> None:
    t0 = time.time()
    src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
    elapsed = time.time() - t0

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(src)

    print(f"[decompile] pyc={PYC}")
    print(f"[decompile] out={OUT}")
    print(f"[decompile] elapsed_s={elapsed:.2f}")
    print(f"[decompile] src_len={len(src)}")
    print(f"[decompile] src_lines={src.count(chr(10)) + 1}")


if __name__ == '__main__':
    main()
