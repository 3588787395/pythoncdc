#!/usr/bin/env python3
"""Revert the merge_block block_to_region fix."""

filepath = 'core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        region.is_condition_context = is_condition_context
        self.regions.append(region)
        for b in region.blocks:
            # [Round 06 fix] merge_block contains code after the BoolOp
            # expression (e.g., STORE_FAST + subsequent statements).
            # Registering it in block_to_region prevents IfRegion from
            # detecting conditional jumps within merge_block, causing
            # `if 'name' in my_dict:` to be decompiled as a bare expr.
            # Fix: don't register merge_block for non-condition BoolOp.
            if b is merge and not is_condition_context:
                continue
            if is_condition_context:
                self.block_to_region[b] = region
                claimed.add(b)
            elif b not in self.block_to_region:
                self.block_to_region[b] = region
                claimed.add(b)
        return region"""

new = """        region.is_condition_context = is_condition_context
        self.regions.append(region)
        for b in region.blocks:
            if is_condition_context:
                self.block_to_region[b] = region
                claimed.add(b)
            elif b not in self.block_to_region:
                self.block_to_region[b] = region
                claimed.add(b)
        return region"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Revert applied successfully')
else:
    print('ERROR: Old string not found')
