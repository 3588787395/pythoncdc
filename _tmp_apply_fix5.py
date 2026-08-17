#!/usr/bin/env python3
"""Fix: don't skip entire block when only specific offsets are generated.
When _find_await_store_target marks STORE_FAST offset as generated,
_generate_block_statements should skip only that instruction, not the entire block."""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = "        if block in self.generated_blocks or block.start_offset in self.generated_offsets:\n            return []"

new = """        if block in self.generated_blocks:
            return []
        # Check if ALL meaningful instructions in this block are in generated_offsets.
        # If only some are (e.g. STORE_FAST from await assignment), we should still
        # process the remaining instructions (e.g. LOAD_FAST + RETURN_VALUE).
        _meaningful = [i for i in block.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        if _meaningful and all(i.offset in self.generated_offsets for i in _meaningful):
            return []"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found')
