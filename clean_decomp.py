#!/usr/bin/env python3

import sys

def clean_decompiled(src, dst):
    with open(src, 'rb') as f:
        data = f.read()
    data = data.replace(b'\x00', b'')
    with open(dst, 'wb') as f:
        f.write(data)

if __name__ == '__main__':
    clean_decompiled('latest_decompiled.py', 'latest_decompiled_clean.py')
