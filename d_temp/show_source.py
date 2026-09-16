with open('F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_funcOK.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
start = None
for i, l in enumerate(lines):
    if 'def handle_exrights' in l:
        start = i
        break
if start is not None:
    print(''.join(lines[start:start+5]))
