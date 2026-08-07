#!/usr/bin/env python3
"""Fix the last store_names occurrence at line 33581."""

content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

old = """            if store_names:
                if len(store_names) == 1 and store_names[0] != module_name.split(".")[0]:
                    aliases = [{'name': module_name, 'asname': store_names[0]}]
                else:
                    aliases = [{'name': name, 'asname': None} for name in store_names]
                return [{'type': 'Import', 'names': aliases}]"""

new = """            if store_names:
                if len(store_names) == 1 and store_names[0] != module_name.split(".")[0]:
                    aliases = [{'name': module_name, 'asname': store_names[0]}]
                else:
                    if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                        aliases = [{'name': module_name, 'asname': None}]
                    else:
                        aliases = [{'name': name, 'asname': None} for name in store_names]
                return [{'type': 'Import', 'names': aliases}]"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed last store_names occurrence")
else:
    print("Pattern not found")

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)

import py_compile
try:
    py_compile.compile('core/cfg/region_ast_generator.py', doraise=True, quiet=2)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error at line {e.lineno}: {e.msg}')
