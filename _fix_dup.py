import sys
sys.path.insert(0, '.')
f = open('core/cfg/region_analyzer.py', 'r', encoding='utf-8')
s = f.read()
f.close()
dup_lines = '''                cond_succs_check = list(block.conditional_successors)
                if len(cond_succs_check) == 2:
                    if any(s in lr.blocks or s == lr.header_block or s == lr.entry for lr in loop_regions for s in cond_succs_check):
                        continue
                cond_succs_check = list(block.conditional_successors)'''
if dup_lines in s:
    s = s.replace(dup_lines, '                cond_succs_check = list(block.conditional_successors)', 1)
    f = open('core/cfg/region_analyzer.py', 'w', encoding='utf-8')
    f.write(s)
    f.close()
    print('Fixed duplicate OK')
else:
    print('No duplicate found')
