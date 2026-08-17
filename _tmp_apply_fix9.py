#!/usr/bin/env python3
"""Fix: exclude nested try regions whose entry is in else_blocks from nested_try_regions."""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                is_entry_in_handler = False
                for _, _, hblocks in region.except_handlers:
                    if r.entry in hblocks:
                        is_entry_in_handler = True
                        break
                if not is_entry_in_handler and getattr(region, 'finally_blocks', None):
                    if r.entry in set(region.finally_blocks):
                        is_entry_in_handler = True
                is_child_in_try = is_child and not is_entry_in_handler"""

new = """                is_entry_in_handler = False
                for _, _, hblocks in region.except_handlers:
                    if r.entry in hblocks:
                        is_entry_in_handler = True
                        break
                if not is_entry_in_handler and getattr(region, 'finally_blocks', None):
                    if r.entry in set(region.finally_blocks):
                        is_entry_in_handler = True
                # [Round 05 fix] nested try whose entry is in else_blocks
                # belongs to the else clause, not the try body.
                is_entry_in_else = bool(getattr(region, 'else_blocks', None) and r.entry in set(region.else_blocks))
                is_child_in_try = is_child and not is_entry_in_handler and not is_entry_in_else"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
