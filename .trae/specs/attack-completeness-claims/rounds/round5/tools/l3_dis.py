#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 探针：dump 指定探针 pyc 的 dis 片段（用于 §3/§6 的字节码级证据定位）。"""
import dis
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.abspath(os.path.join(HERE, "..", "probes"))


def main():
    name = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else None
    path = os.path.join(PROBES, name + ".pyc")
    with open(path, "rb") as f:
        f.read(16)  # PEP 552 header (magic + flags + mtime/size)
        code = marshal.load(f)
    for const in code.co_consts:
        if hasattr(const, "co_name"):
            if only and const.co_name != only:
                continue
            print("=" * 20, const.co_name)
            buf = io.StringIO()
            dis.dis(const, file=buf)
            for line in buf.getvalue().splitlines():
                print(line)


if __name__ == "__main__":
    import marshal
    main()
