#!/usr/bin/env python3
"""Fix dotted module import handling in region_ast_generator.py."""
content = open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8').read()

# Fix _sn_list[0] != module_name -> _sn_list[0] != module_name.split('.')[0]
content = content.replace('_sn_list[0] != module_name:', '_sn_list[0] != module_name.split(".")[0]:')

# Fix store_names[0] != module_name -> store_names[0] != module_name.split('.')[0]
content = content.replace('store_names[0] != module_name:', 'store_names[0] != module_name.split(".")[0]:')

open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8').write(content)
print('Done - fixed all occurrences')
