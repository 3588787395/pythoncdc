#!/usr/bin/env python3
import sys
from pathlib import Path

# 检查反编译文件
def check_file(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
            
        print(f"文件大小: {len(raw)} 字节")
        print(f"前20字节十六进制: {raw[:20].hex()}")
        
        # 尝试UTF-8解码
        try:
            text = raw.decode('utf-8')
            print("\nUTF-8解码成功，前20行:")
            lines = text.split('\n')[:20]
            for i, line in enumerate(lines, 1):
                print(f"{i:2}: {repr(line)}")
        except UnicodeDecodeError as e:
            print(f"UTF-8解码失败: {e}")
            
            # 尝试其他编码
            for encoding in ['latin-1', 'cp1252']:
                try:
                    text = raw.decode(encoding)
                    print(f"\n{encoding}解码成功，前20行:")
                    lines = text.split('\n')[:20]
                    for i, line in enumerate(lines, 1):
                        print(f"{i:2}: {repr(line)}")
                    break
                except:
                    continue
    except Exception as e:
        print(f"读取文件出错: {e}")

if __name__ == '__main__':
    check_file('decompiler_test_comprehensive_decompiled_round01.py')