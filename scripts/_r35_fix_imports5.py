#!/usr/bin/env python3
"""Fix duplicate/broken store_names block at line 32495."""

content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

# The broken pattern: duplicate else blocks
old = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                                aliases = [{'name': module_name, 'asname': None}]
                            else:
                                aliases = [{'name': name, 'asname': None} for name in store_names]"""

new = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                                aliases = [{'name': module_name, 'asname': None}]
                            else:
                                aliases = [{'name': name, 'asname': None} for name in store_names]"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed duplicate store_names block")
else:
    print("Pattern not found")

# Check for any other similar issues
lines = content.split('\n')
for i, line in enumerate(lines):
    if "if '.' in module_name and store_names" in line:
        print(f"  Line {i+1}: {repr(line)}")
        if i+1 < len(lines):
            print(f"  Line {i+2}: {repr(lines[i+1])}")

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile('core/cfg/region_ast_generator.py', doraise=True, quiet=2)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
