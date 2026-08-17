"""R82b fix: remove _has_swap_r82 check - merge_block may only have RETURN_VALUE."""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            _has_return_r82 = any(i.opname == 'RETURN_VALUE' for i in _mb_instrs_r82)
            _has_swap_r82 = any(i.opname == 'SWAP' for i in _mb_instrs_r82)
            if _has_return_r82 and _has_swap_r82:"""

new = """            _has_return_r82 = any(i.opname == 'RETURN_VALUE' for i in _mb_instrs_r82)
            if _has_return_r82:"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R82b fix applied")
else:
    print("FAILED: Could not find target text")
