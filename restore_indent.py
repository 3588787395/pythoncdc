import re

FILE = r'd:\Desktop\ptrade相关\pythoncdc\core\cfg\region_ast_generator.py'
AFFECTED_START = 971
AFFECTED_END = 4309
BASE_INDENT = 16

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(AFFECTED_START - 1, AFFECTED_END):
    stripped = lines[i].lstrip()
    if stripped:
        lines[i] = ' ' * BASE_INDENT + stripped
    else:
        lines[i] = '\n'

with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Restored broken state")
