#!/usr/bin/env python3
"""R92 fix v2: Use instance variable for cross-method communication"""

with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of _r92_post_if_blocks with self._r92_post_if_blocks
# But NOT in the local variable declaration
content = content.replace('_r92_post_if_blocks = [', 'self._r92_post_if_blocks = [')
content = content.replace('if _r92_post_if_blocks:', 'if self._r92_post_if_blocks:')
content = content.replace('for _b in _r92_post_if_blocks:', 'for _b in self._r92_post_if_blocks:')
# Fix the remaining reference
content = content.replace('_r92_post_stmts = self._process_if_blocks(\n                _r92_post_if_blocks,', '_r92_post_stmts = self._process_if_blocks(\n                self._r92_post_if_blocks,')

with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
