import re

file_path = 'core/cfg/region_ast_generator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add helper methods before _process_instruction
helper_methods = """    def _is_mangled_name(self, target_name, co_name):
        \"\"\"Detect if target_name is the mangled form of co_name.\"\"\"
        if not co_name or not target_name:
            return False
        if not (co_name.startswith('__') and not co_name.endswith('__')):
            return False
        return target_name.endswith(co_name) and target_name != co_name

    def _safe_set_func_name(self, func_def, target_name):
        \"\"\"Safely set function name, avoiding name mangling override.\"\"\"
        if func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):
            co_name = func_def.get('name', '')
            if self._is_mangled_name(target_name, co_name):
                return
        func_def['name'] = target_name

"""

# Insert before _process_instruction
marker = "    def _process_instruction(self, instr, block, stmt_instrs=None):"
if marker in content:
    content = content.replace(marker, helper_methods + marker, 1)
    print("OK: helper methods added")
else:
    print("FAIL: marker not found")

# 2. Replace all 8 override points
replacements = [
    # Point 1: line ~25509
    ("_func_def['name'] = region.value_target\n                                    results.append(_func_def)",
     "self._safe_set_func_name(_func_def, region.value_target)\n                                    results.append(_func_def)"),
    # Point 2: line ~29193
    ("_func_def['name'] = innermost.value_target\n            return _func_def",
     "self._safe_set_func_name(_func_def, innermost.value_target)\n            return _func_def"),
    # Point 3: line ~34555
    ("if target_name and func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):\n                            func_def['name'] = target_name",
     "if target_name and func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):\n                            self._safe_set_func_name(func_def, target_name)"),
    # Point 4: line ~34729
    ("if func_def.get('name') == target_name or func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):\n                func_def['name'] = target_name",
     "if func_def.get('name') == target_name or func_def.get('type') in ('FunctionDef', 'AsyncFunctionDef'):\n                self._safe_set_func_name(func_def, target_name)"),
]

for i, (old, new) in enumerate(replacements):
    if old in content:
        content = content.replace(old, new, 1)
        print(f"OK: replacement {i+1} applied")
    else:
        print(f"SKIP: replacement {i+1} not found")

# Points 5-8: these are all "func_def['name'] = target_name" in similar contexts
# Let's find remaining occurrences
remaining = content.count("func_def['name'] = target_name")
print(f"Remaining 'func_def[\\'name\\'] = target_name' occurrences: {remaining}")

# Replace all remaining occurrences
content = content.replace("func_def['name'] = target_name", "self._safe_set_func_name(func_def, target_name)")
print(f"Replaced all remaining occurrences")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
