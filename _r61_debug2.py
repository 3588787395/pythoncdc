#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Simple: read file, print first 10 lines
with open('_r60_full_verify.txt', 'rb') as f:
    raw = f.read()
print(f'File size: {len(raw)} bytes')
print(f'First 20 bytes: {raw[:20]}')
text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')
print(f'Lines: {len(lines)}')
for i, line in enumerate(lines[:10]):
    print(f'  [{i}] {repr(line.strip())}')
