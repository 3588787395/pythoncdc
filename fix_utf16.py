#!/usr/bin/env python3

import sys

def fix_utf16_file(src, dst):
    """Convert UTF-16 LE file to UTF-8, removing BOM and NUL bytes"""
    with open(src, 'rb') as f:
        data = f.read()
    
    # Remove BOM (FF FE)
    if data.startswith(b'\xff\xfe'):
        data = data[2:]
    
    # Decode UTF-16 LE
    try:
        text = data.decode('utf-16le')
    except Exception as e:
        print(f"UTF-16 decode error: {e}")
        return False
    
    # Encode to UTF-8
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"Converted {src} to {dst} (UTF-16 LE -> UTF-8)")
    return True

if __name__ == '__main__':
    fix_utf16_file('decompiler_test_comprehensive_decompiled_r11.py', 'decompiler_test_comprehensive_decompiled_r11_utf8.py')
