#!/usr/bin/env python3
"""Fix _find_await_store_target to handle fall-through blocks with STORE_* + subsequent instructions."""

import re

FILE = 'core/cfg/region_ast_generator.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# The exact old code to replace
old = """            if store_instrs and len(non_noise) == 1 and non_noise[0] is store_instrs[0]:
                store_i = store_instrs[0]
                target = store_i.argval if store_i.argval else f'var_{store_i.arg}'
                # 标记该块已生成，避免后续作为独立赋值语句重复处理
                self.generated_blocks.add(succ)
                return target"""

new = """            # [R01 fix] Region reduction principle 2 (unique block ownership) + 4 (entry reference):
            # await assignment fall-through may contain STORE_* + subsequent instructions
            # (e.g. `x = await ...; return x` has STORE_FAST + LOAD_FAST + RETURN_VALUE).
            # Original required len(non_noise) == 1, causing await expr to be dropped when
            # fall-through had additional statements. Fix: only check first non-noise instr
            # is STORE_*. Mark only STORE_* offset as generated, not entire block, so
            # subsequent statements are still processed by _generate_block_statements.
            if store_instrs and non_noise and non_noise[0] is store_instrs[0]:
                store_i = store_instrs[0]
                target = store_i.argval if store_i.argval else f'var_{store_i.arg}'
                # Mark STORE_* offset as generated to avoid duplicate assignment
                self.generated_offsets.add(store_i.offset)
                # If fall-through has only STORE_*, mark entire block as generated
                if len(non_noise) == 1:
                    self.generated_blocks.add(succ)
                return target"""

if old in content:
    content = content.replace(old, new, 1)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("FIX APPLIED: _find_await_store_target relaxed")
else:
    print("ERROR: old code not found")
    # Try to find similar code
    idx = content.find('len(non_noise) == 1')
    if idx >= 0:
        print(f"Found 'len(non_noise) == 1' at position {idx}")
        print(f"Context: {repr(content[idx-200:idx+200])}")
    else:
        print("'len(non_noise) == 1' not found in file")
