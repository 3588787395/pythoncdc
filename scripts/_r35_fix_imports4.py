#!/usr/bin/env python3
"""Fix remaining indentation issues in region_ast_generator.py."""

content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

# Fix second _sn_list occurrence (line ~469)
old = """                                    else:
                                        if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                        _aliases = [{'name': module_name, 'asname': None}]
                                    else:
                                        _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
new = """                                    else:
                                        if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                            _aliases = [{'name': module_name, 'asname': None}]
                                        else:
                                            _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed second _sn_list occurrence")
else:
    print("Second _sn_list pattern not found - checking alternatives")
    # Try a more flexible match
    import re
    # Find all indentation issues
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "if '.' in module_name and _sn_list" in line:
            print(f"  Line {i+1}: {repr(line)}")
            if i+1 < len(lines):
                print(f"  Line {i+2}: {repr(lines[i+1])}")

# Fix store_names occurrences too
old2 = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]"""
new2 = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                                aliases = [{'name': module_name, 'asname': None}]
                            else:
                                aliases = [{'name': name, 'asname': None} for name in store_names]"""

if old2 in content:
    content = content.replace(old2, new2)
    print("Fixed store_names occurrences")
else:
    print("store_names pattern not found")

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)

# Verify syntax
import py_compile
try:
    py_compile.compile('core/cfg/region_ast_generator.py', doraise=True, quiet=2)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
