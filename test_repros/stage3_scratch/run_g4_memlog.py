# -*- coding: utf-8 -*-
"""G4 run wrapper with a memory guard and a memlog.

usage: python -X utf8 run_g4_memlog.py <memlog.txt> <min_avail_pagefile_mb> \
           <rule_proof_check args...>

Resolves paths against the caller cwd, runs
tools/completeness/rule_proof_check.py as a child with cwd=repo root,
echoes its stdout/stderr, and appends pre/post GlobalMemoryStatusEx
ullAvailPageFile snapshots plus elapsed time and exit code to the memlog.
Exit code: 2 when the memory guard trips, otherwise the child's exit code
(exit 1 with reason=mapping_or_proof_gap is the normal rehearsal gate).
"""
import ctypes
import datetime
import os
import subprocess
import sys
import time

REPO = r"F:\Downloads\pythoncdc-main"
CHECKER = os.path.join(REPO, "tools", "completeness", "rule_proof_check.py")


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def snapshot():
    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st


def log(fh, msg):
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    fh.write("%s %s\n" % (stamp, msg))
    fh.flush()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 64
    memlog_path, min_mb, checker_args = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    pre = snapshot()
    avail = pre.ullAvailPageFile // (1024 * 1024)
    with open(memlog_path, "a", encoding="utf-8") as fh:
        log(fh, "memguard pre avail_pagefile_mb=%d min_mb=%d"
            % (avail, min_mb))
    if avail < min_mb:
        print("[run_g4_memlog] memguard INSUFFICIENT avail_pagefile_mb=%d < %d"
              % (avail, min_mb))
        return 2
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", CHECKER] + checker_args,
        cwd=REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    elapsed = round(time.perf_counter() - t0, 1)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    post = snapshot()
    with open(memlog_path, "a", encoding="utf-8") as fh:
        log(fh, "g4 done exit=%d elapsed_s=%.1f avail_pagefile_mb=%d->%d "
                "load=%d%%" % (proc.returncode, elapsed, avail,
                               post.ullAvailPageFile // (1024 * 1024),
                               post.dwMemoryLoad))
    print("[run_g4_memlog] exit=%d elapsed_s=%.1f" % (proc.returncode, elapsed))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
