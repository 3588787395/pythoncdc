#!/usr/bin/env python3
"""Fix indentation issues from previous fix."""

content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

# Fix 1: _sn_list occurrences (2 places with different indentation)
# Pattern: if '.' in module_name ... \n _aliases = [{'name': module_name... (wrong indent)
# Should be: if '.' in module_name ... \n    _aliases = [{'name': module_name...

# Fix first occurrence (24-space base indent)
old1 = """                        else:
                            if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                            _aliases = [{'name': module_name, 'asname': None}]
                        else:
                            _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
new1 = """                        else:
                            if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                _aliases = [{'name': module_name, 'asname': None}]
                            else:
                                _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
content = content.replace(old1, new1, 1)

# Fix second occurrence (36-space base indent)
old2 = """                                    else:
                                    if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                        _aliases = [{'name': module_name, 'asname': None}]
                                    else:
                                        _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
# Check if this pattern exists
if old2 in content:
    content = content.replace(old2, """                                    else:
                                        if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                            _aliases = [{'name': module_name, 'asname': None}]
                                        else:
                                            _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]""", 1)

# Fix store_names occurrences
old3 = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]"""
new3 = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                                aliases = [{'name': module_name, 'asname': None}]
                            else:
                                aliases = [{'name': name, 'asname': None} for name in store_names]"""
content = content.replace(old3, new3, 1)

# Fix second store_names occurrence
old4 = """                        else:
                            if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]"""
new4 = new3  # same pattern
content = content.replace(old4, new4, 1)

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)
print('Done')

# Verify syntax
import py_compile
try:
    py_compile.compile('core/cfg/region_ast_generator.py', doraise=True, quiet=2)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
