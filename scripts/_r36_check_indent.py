with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(21416, 21425):
    print(f'{i+1}: {repr(lines[i])}')
