#!/usr/bin/env python3
"""Apply fix to region_ast_generator.py generate() method"""
import sys

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        entry_block = self.cfg.entry_block
        if entry_block is not None:
            if self.region_analyzer.metadata.get('is_generator_entry'):
                self.generated_blocks.add(entry_block)
                entry_block = self.region_analyzer.metadata.get('generator_entry_block', entry_block)

        ast_nodes = []"""

new = """        entry_block = self.cfg.entry_block
        if entry_block is not None:
            if self.region_analyzer.metadata.get('is_generator_entry'):
                gen_entry = self.region_analyzer.metadata.get('generator_entry_block', entry_block)
                # Only mark the prologue block as generated if it is different from
                # the resume block (Case A: entry is the RETURN_GENERATOR prologue).
                # When they are the same (Case B: entry IS the resume block),
                # marking it generated would skip the entire body.
                if gen_entry is not entry_block:
                    self.generated_blocks.add(entry_block)
                entry_block = gen_entry

        ast_nodes = []"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Edit applied successfully')
else:
    print('ERROR: Old string not found in file')
    # Try to find the closest match
    import difflib
    lines_old = old.split('\n')
    for i, line in enumerate(content.split('\n')):
        if 'is_generator_entry' in line and 'metadata.get' in line:
            print(f'Found at line {i+1}: {repr(line)}')
            for j in range(i-2, min(i+5, len(content.split('\n')))):
                print(f'  {j+1}: {repr(content.split(chr(10))[j])}')
