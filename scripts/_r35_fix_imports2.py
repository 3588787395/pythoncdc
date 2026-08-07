#!/usr/bin/env python3
"""Fix dotted module import: use full module_name when stored_name == first component."""

content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

# Fix the _sn_list else branch: when module is dotted and stored_name == first component,
# use full module_name instead of stored_name
old_sn = """_aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
new_sn = """if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                            _aliases = [{'name': module_name, 'asname': None}]
                        else:
                            _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
content = content.replace(old_sn, new_sn, 1)

# Fix the second occurrence (different indentation)
old_sn2 = """                                    _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
new_sn2 = """                                    if '.' in module_name and _sn_list[0] == module_name.split('.')[0]:
                                        _aliases = [{'name': module_name, 'asname': None}]
                                    else:
                                        _aliases = [{'name': _n, 'asname': None} for _n in _sn_list]"""
content = content.replace(old_sn2, new_sn2, 1)

# Fix store_names else branch (2 occurrences)
old_store = """aliases = [{'name': name, 'asname': None} for name in store_names]"""
new_store = """if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]"""
content = content.replace(old_store, new_store, 1)

# Second occurrence with different indentation
old_store2 = """                        aliases = [{'name': name, 'asname': None} for name in store_names]"""
new_store2 = """                        if '.' in module_name and store_names[0] == module_name.split('.')[0]:
                            aliases = [{'name': module_name, 'asname': None}]
                        else:
                            aliases = [{'name': name, 'asname': None} for name in store_names]"""
content = content.replace(old_store2, new_store2, 1)

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)
print('Done - fixed all occurrences')

# Verify
verify = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()
count = verify.count("module_name.split('.')[0]")
print(f"Total split('.')[0] occurrences: {count}")
