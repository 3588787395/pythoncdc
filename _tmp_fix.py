import re

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = "            if not _last or _last.opname not in NONE_CHECK_OPS or _last.argval is None:\n                return False\n            _jt_block = self.cfg.get_block_by_offset(_last.argval)"

new = "            if not _last or _last.argval is None:\n                return False\n            # [Round6-CONTAINS_OP] NONE_CHECK_OPS or POP_JUMP_IF_TRUE are OR-success\n            _is_or_candidate = (_last.opname in NONE_CHECK_OPS\n                                or 'IF_TRUE' in _last.opname)\n            if not _is_or_candidate:\n                return False\n            _jt_block = self.cfg.get_block_by_offset(_last.argval)"

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: replaced the NONE_CHECK_OPS check")
else:
    print("ERROR: old string not found")
    # Show context around line 12037
    lines = content.split('\n')
    for i in range(12035, 12042):
        print(f"  L{i+1}: {repr(lines[i])}")
