#!/usr/bin/env python3
"""R61: Fix post-store processing for chained assignment"""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Change the condition to also process post-store instructions
# when chained targets are detected
old = """                if region.merge_block and not _chained_targets_r61:
                    _merge_instrs = [i for i in region.merge_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _store_ops_set = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                      'STORE_ATTR', 'STORE_SUBSCR')"""

new = """                if region.merge_block:
                    _merge_instrs = [i for i in region.merge_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    _store_ops_set = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                      'STORE_ATTR', 'STORE_SUBSCR')"""

if old not in content:
    print("ERROR: old text not found!")
    idx = content.find("if region.merge_block and not _chained_targets_r61:")
    if idx >= 0:
        print(f"Found at index {idx}: {repr(content[idx:idx+300])}")
    exit(1)

content = content.replace(old, new, 1)
print("Step 1: Changed condition to process post-store for chained targets too")

# Now modify the _first_store_idx logic to find the LAST store when chained
old2 = """                    if not _merge_is_other_entry_r10f3:
                        _first_store_idx = -1
                        for _psi, i in enumerate(_merge_instrs):
                            if i.opname in _store_ops_set:
                                _first_store_idx = _psi
                                break"""

new2 = """                    if not _merge_is_other_entry_r10f3:
                        # [R61 fix] When chained targets are detected (COPY +
                        # multiple STOREs), find the LAST store in the chain
                        # so post-store processing handles instructions after
                        # all chained stores (e.g. new_kwargs[k] = [price, amount]
                        # after `price = base_price = expr`).
                        if _chained_targets_r61:
                            _first_store_idx = -1
                            _STORE_TYPES_R61_chk = ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                            for _psi, i in enumerate(_merge_instrs):
                                if i.opname in _STORE_TYPES_R61_chk:
                                    _first_store_idx = _psi
                                    # Don't break - continue to find the last one
                                elif _first_store_idx >= 0 and i.opname not in _STORE_TYPES_R61_chk:
                                    break
                        else:
                            _first_store_idx = -1
                            for _psi, i in enumerate(_merge_instrs):
                                if i.opname in _store_ops_set:
                                    _first_store_idx = _psi
                                    break"""

if old2 not in content:
    print("ERROR: old2 text not found!")
    idx = content.find("if not _merge_is_other_entry_r10f3:")
    if idx >= 0:
        print(f"Found at index {idx}: {repr(content[idx:idx+400])}")
    exit(1)

content = content.replace(old2, new2, 1)
print("Step 2: Modified _first_store_idx to find last store for chained targets")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! File saved.")
