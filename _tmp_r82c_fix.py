"""R82c fix: use _build_chained_compare_from_region_data instead of _build_assert_chained_compare
in the return-context chained compare path, to get attr-middle fallback support."""

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if _has_return_r82:
                _chained_cond_r82 = self._build_assert_chained_compare(
                    cond_block,
                    list(region.chained_compare_blocks),
                    list(region.chained_compare_ops),
                )"""

new = """            if _has_return_r82:
                _chained_cond_r82 = self._build_chained_compare_from_region_data(region)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: R82c fix applied")
else:
    print("FAILED: Could not find target text")
