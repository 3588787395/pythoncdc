#!/usr/bin/env python3
"""Fix _generate_constant: escape \\ and \r in triple-quoted strings"""

filepath = 'core/cfg/code_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if '\\n' in value:
                    # 多行字符串使用三引号
                    if '\"\"\"' in value:
                        # 如果包含三引号，使用单引号三引号
                        return f\"'''{value}'''\"
                    else:
                        # 否则使用双引号三引号
                        return f'\"\"\"{value}\"\"\"'"""

new = """            if '\\n' in value:
                    # 多行字符串使用三引号
                    # Escape backslash and carriage return to preserve them
                    # (backslash would start escape sequence, \\r may be stripped by file I/O)
                    escaped = value.replace('\\\\', '\\\\\\\\').replace('\\r', '\\\\r')
                    if '\"\"\"' in escaped:
                        # 如果包含三引号，使用单引号三引号
                        return f\"'''{escaped}'''\"
                    else:
                        # 否则使用双引号三引号
                        return f'\"\"\"{escaped}\"\"\"'"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found, trying alternate approach...')
    
    # Try reading the actual lines
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "'\\n' in value" in line:
            # Found the line, now replace the block
            start = i
            # Find the end of the if block (next line with same or less indentation that's not else)
            end = start
            for j in range(start+1, min(start+15, len(lines))):
                if lines[j].strip().startswith('else:') and '单行字符串' in lines[j]:
                    end = j - 1
                    break
                end = j
            
            print(f"Block from line {start+1} to {end+1}:")
            for j in range(start, end+1):
                print(f"  {j+1}: {repr(lines[j])}")
            break
