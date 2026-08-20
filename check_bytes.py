#!/usr/bin/env python3

import sys

def analyze_file(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    print(f"File: {filepath}")
    print(f"Size: {len(data)} bytes")
    nul_bytes = data.count(b'\x00')
    ff_bytes = data.count(b'\xff')
    fe_bytes = data.count(b'\xfe')
    print(f"NUL bytes: {nul_bytes}")
    print(f"FF bytes: {ff_bytes}")
    print(f"FE bytes: {fe_bytes}")
    if data[:50]:
        print(f"First 50 bytes: {data[:50]}")
    return data

def clean_file(data):
    # Remove NUL bytes
    data = data.replace(b'\x00', b'')
    return data

def main():
    data = analyze_file('decompiler_test_comprehensive_decompiled_r11.py')
    cleaned = clean_file(data)
    print(f"Cleaned size: {len(cleaned)} bytes")
    
    with open('decompiler_test_comprehensive_decompiled_r11_clean.py', 'wb') as f:
        f.write(cleaned)
    print("Cleaned file saved")

if __name__ == '__main__':
    main()
