#!/usr/bin/env python3
"""候选最小复现探针：对 tmp/cand/*.py 逐个做 compile→decompile→compile 比对。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import os
CAND = HERE / (os.environ.get('CANDDIR') or 'cand')
sys.path.insert(0, str(HERE.parent / 'minimal_repros'))

import run_repros as rr  # noqa: E402

CAND.mkdir(exist_ok=True)


def main():
    verbose = '-v' in sys.argv
    files = sorted(CAND.glob('*.py'))
    npass = nfail = 0
    for f in files:
        ok, detail = rr.check_repro(f, verbose and False)
        if ok:
            npass += 1
            print(f'[PASS] {f.name}')
        else:
            nfail += 1
            print(f'[FAIL] {f.name:24s} {detail}')
            if verbose:
                src = f.read_text(encoding='utf-8')
                try:
                    print('  --- decompiled ---')
                    for ln in rr.decompile(src, str(f)).splitlines():
                        print('  | ' + ln)
                except Exception as e:
                    print(f'  | decompile error {type(e).__name__}: {e}')
    print(f'cand total={len(files)} pass={npass} fail={nfail}')


if __name__ == '__main__':
    main()
