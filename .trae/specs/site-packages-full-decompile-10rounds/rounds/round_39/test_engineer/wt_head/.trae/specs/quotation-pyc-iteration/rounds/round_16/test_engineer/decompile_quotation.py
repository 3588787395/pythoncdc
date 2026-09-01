"""R16 测试工程师：反编译 quotation.pyc 并写入 /tmp/r16_decompiled.py"""
import sys
import time

sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'
OUT = '/tmp/r16_decompiled.py'

t0 = time.time()
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
elapsed = time.time() - t0
print(f"[decompile] elapsed={elapsed:.2f}s, len={len(src)}")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"[decompile] wrote {OUT}")
