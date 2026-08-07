f = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()
# Find which method contains line 33700
i = 33699  # 0-indexed
while i >= 0:
    line = lines[i].strip()
    if line.startswith('def '):
        print(f'Line {i+1}: {line}')
        break
    i -= 1
# Also find the method containing line 34082
i = 34081
while i >= 0:
    line = lines[i].strip()
    if line.startswith('def '):
        print(f'Line {i+1}: {line}')
        break
    i -= 1
