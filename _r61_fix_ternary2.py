#!/usr/bin/env python3
"""R61: Add STORE_SUBSCR/STORE_ATTR to the condition check in _generate_ternary"""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The existing condition only handles simple STORE ops.
# Need to add STORE_SUBSCR and STORE_ATTR so the handler block is entered.
old = """                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    # Check if the predecessor range contains
                    # MAKE_FUNCTION."""

new = """                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                   'STORE_SUBSCR', 'STORE_ATTR'):
                    # Check if the predecessor range contains
                    # MAKE_FUNCTION."""

if old not in content:
    print("ERROR: old text not found!")
    idx = content.find("if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):")
    if idx >= 0:
        print(f"Found at index {idx}")
        print(f"Context: {repr(content[idx:idx+200])}")
    exit(1)

content = content.replace(old, new, 1)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Added STORE_SUBSCR/STORE_ATTR to condition check.")
