#!/usr/bin/env python3
"""Fix _compute_generator_entry_metadata to check predecessors for RETURN_GENERATOR.

When the CFG builder splits RETURN_GENERATOR into a separate block, the entry_block
may not contain RETURN_GENERATOR directly. We need to check predecessors as well.
"""

FILE = 'core/cfg/region_analyzer.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

old = """    def _compute_generator_entry_metadata(self) -> None:
        entry_block = self.cfg.entry_block
        if entry_block is not None:
            is_generator_entry = all(
                instr.opname in ('RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'CACHE', 'NOP')
                for instr in entry_block.instructions
            ) and any(instr.opname == 'RETURN_GENERATOR' for instr in entry_block.instructions)
            if is_generator_entry:
                resume_block = self.find_generator_resume_block(entry_block)
                self.metadata['generator_entry_block'] = resume_block if resume_block else entry_block
                self.metadata['is_generator_entry'] = True
            else:
                self.metadata['generator_entry_block'] = entry_block
                self.metadata['is_generator_entry'] = False
        else:
            self.metadata['generator_entry_block'] = None
            self.metadata['is_generator_entry'] = False"""

new = """    def _compute_generator_entry_metadata(self) -> None:
        entry_block = self.cfg.entry_block
        if entry_block is not None:
            is_generator_entry = all(
                instr.opname in ('RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'CACHE', 'NOP')
                for instr in entry_block.instructions
            ) and any(instr.opname == 'RETURN_GENERATOR' for instr in entry_block.instructions)
            # [R01 fix] Region reduction principle 1 (bottom-up reduction):
            # CPython 3.11 async/coroutine functions start with RETURN_GENERATOR + POP_TOP
            # at offset 0. The CFG builder may split these into a separate block, making
            # the entry_block NOT contain RETURN_GENERATOR directly. Check if any
            # predecessor block is a RETURN_GENERATOR prologue (contains only
            # RETURN_GENERATOR/POP_TOP/CACHE/NOP). If so, this is a generator/coroutine
            # entry, and the predecessor should be marked as generated (skip prologue).
            if not is_generator_entry:
                for pred in entry_block.predecessors:
                    if (any(i.opname == 'RETURN_GENERATOR' for i in pred.instructions) and
                        all(i.opname in ('RETURN_GENERATOR', 'POP_TOP', 'CACHE', 'NOP')
                            for i in pred.instructions)):
                        is_generator_entry = True
                        # Mark the prologue block as generated so it's skipped
                        self.block_to_region[pred] = None  # release from any region
                        break
            if is_generator_entry:
                resume_block = self.find_generator_resume_block(entry_block)
                self.metadata['generator_entry_block'] = resume_block if resume_block else entry_block
                self.metadata['is_generator_entry'] = True
            else:
                self.metadata['generator_entry_block'] = entry_block
                self.metadata['is_generator_entry'] = False
        else:
            self.metadata['generator_entry_block'] = None
            self.metadata['is_generator_entry'] = False"""

if old in content:
    content = content.replace(old, new, 1)
    with open(FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("FIX APPLIED: _compute_generator_entry_metadata now checks predecessors")
else:
    print("ERROR: old code not found")
