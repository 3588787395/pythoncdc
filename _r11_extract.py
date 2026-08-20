with open('decompiler_test_comprehensive_decompiled_r11.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
start = None
for i, line in enumerate(lines):
    if 'def exception_handling_complex' in line:
        start = i
        break
if start is not None:
    for i in range(start, min(start + 50, len(lines))):
        print(f'{i+1}: {lines[i].rstrip()}')
