lines = open('core/cfg/region_analyzer.py', 'r', encoding='utf-8').readlines()
new_lines = []
i = 0
while i < len(lines):
    if (i + 1 < len(lines) and
        lines[i].strip() == '"""' and
        lines[i+1].strip() == '"""' and
        i > 0 and 'else_is_follow' in lines[i-1]):
        new_lines.append(lines[i])
        i += 2
        continue
    new_lines.append(lines[i])
    i += 1
open('core/cfg/region_analyzer.py', 'w', encoding='utf-8').writelines(new_lines)
print('Fixed')
