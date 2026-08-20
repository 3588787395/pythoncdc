import os
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'cfg', 'region_ast_generator.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'and any(i.opname in' in content:
    print('First fix is present')
else:
    print('First fix is MISSING')
if 'in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)' in content:
    print('Second check still uses old role-based logic')
    # Find line number
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)' in line:
            print(f'  Found at line {i+1}')
