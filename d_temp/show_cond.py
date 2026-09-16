with open('F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_funcOK.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
start = None
for i, l in enumerate(lines):
    if 'def handle_exrights' in l:
        start = i
        break
if start is not None:
    end = start + 1
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    while end < len(lines):
        s = lines[end].strip()
        ci = len(lines[end]) - len(lines[end].lstrip()) if s else 999
        if s and ci <= base_indent:
            break
        end += 1
    print(''.join(lines[start:start+3]))
