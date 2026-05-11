import sys

with open('f:/pythoncdc/core/cfg/region_ast_generator.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\x0A')
print(f'Total lines: {len(lines)}')

# Check line 5047
line = lines[5046]  # 0-indexed
print(f'Line 5047 length: {len(line)}')
print(f'Line 5047 bytes around error position:')
for i in range(max(0, 60), min(len(line), 100)):
    b = line[i]
    c = chr(b) if 32 <= b < 127 else '?'
    marker = ' <-- ERROR' if b == 0xEF and i+1 < len(line) and line[i+1] == 0xBC else ''
    print(f'  {i}: {hex(b)} ({c}){marker}')
    if b > 127:
        # Check if this could be part of UTF-8
        print(f'      (checking UTF-8 validity...)')
