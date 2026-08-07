f = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()
start = 30690  # 0-indexed
end = min(35376, len(lines))
found = []
for i in range(start, end):
    line = lines[i]
    if '_build_store_statement' in line or '_generate_stmts_from' in line or ('for ' in line and 'instr' in line and 'in ' in line):
        found.append((i+1, line.rstrip()))
for l in found[:30]:
    print(f'{l[0]}: {l[1]}')
