file_path = 'core/cfg/region_ast_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '        self._safe_set_func_name(func_def, target_name)\n\n    def _process_instruction'
new = '        func_def[\'name\'] = target_name\n\n    def _process_instruction'

if old in content:
    content = content.replace(old, new, 1)
    print("OK: fixed infinite recursion")
else:
    print("FAIL: pattern not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
