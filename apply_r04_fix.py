#!/usr/bin/env python3
"""Apply Round 4 fix: prevent condition negation in loop continue handling"""

import shutil

file_path = "core/cfg/region_ast_generator.py"

# Backup
shutil.copy2(file_path, file_path + ".r04_backup")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                if _else_is_pure_cont and not _then_is_pure_cont:
                    self.generated_blocks.add(_else_succ)
                    self.generated_offsets.add(_else_succ.start_offset)
                    _hdr_stmts.append({'type': 'If', 'test': _negate_expr(_expr),
                                       'body': [{'type': 'Continue'}]})
                    return"""

new_code = """                if _else_is_pure_cont and not _then_is_pure_cont:
                    _then_stmts_full = self._generate_block_statements(_then_succ)
                    if not _then_stmts_full:
                        _then_stmts_full = [{'type': 'Pass'}]
                    self.generated_blocks.add(_then_succ)
                    self.generated_offsets.add(_then_succ.start_offset)
                    self.generated_blocks.add(_else_succ)
                    self.generated_offsets.add(_else_succ.start_offset)
                    _hdr_stmts.append({'type': 'If', 'test': _expr,
                                       'body': _then_stmts_full,
                                       'orelse': [{'type': 'Continue'}]})
                    return"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Could not find the target code to replace!")
    # Try to find partial match
    if "_else_is_pure_cont and not _then_is_pure_cont" in content:
        idx = content.find("_else_is_pure_cont and not _then_is_pure_cont")
        print(f"Found partial match at position {idx}")
        print(f"Context: {repr(content[idx-20:idx+200])}")
    else:
        print("No partial match found either!")