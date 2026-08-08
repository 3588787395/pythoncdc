#!/usr/bin/env python3
"""R61: Add is_chain_assign flag to the chained assignment"""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                    if _chained_targets_r61:
                        results.append({
                            'type': 'Assign',
                            'targets': _chained_targets_r61,
                            'value': boolop_expr,
                        })"""

new = """                    if _chained_targets_r61:
                        results.append({
                            'type': 'Assign',
                            'targets': _chained_targets_r61,
                            'value': boolop_expr,
                            'is_chain_assign': True,
                        })"""

if old not in content:
    print("ERROR: old text not found!")
    # Try to find similar text
    idx = content.find("_chained_targets_r61:")
    if idx >= 0:
        print(f"Found at index {idx}: {repr(content[idx:idx+200])}")
    exit(1)

content = content.replace(old, new, 1)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! is_chain_assign flag added.")
