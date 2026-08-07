import os

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 31837 is at index 31836 (0-based)
# Verify it's the right line
assert '_ns_n >= 2' in lines[31836], f"Line 31837 mismatch: {repr(lines[31836])}"

new_line = (
    "                        # [R39 fix] Stack depth guard: when expr_reconstructor\n"
    "                        # simulated stack has fewer than _ns_n elements\n"
    "                        # (e.g. nested for-loop conditional branch causes\n"
    "                        # incomplete stack tracking), skip tuple unpack\n"
    "                        # path to prevent _ns_stack[-_ns_n + _si] IndexError\n"
    "                        # that drops the entire function body (pass).\n"
    "                        if _ns_n >= 2 and len(_ns_stack) >= _ns_n:\n"
)

lines[31836] = new_line

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done! Replaced line 31837 with guarded version.")
