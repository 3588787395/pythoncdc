with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        if region.region_type.name == 'IF_ELIF_CHAIN':
            return self._if_generate_full_elif_chain(region)
        # [Round4-04] 链式比较作赋值右值'''

new = '''        if region.region_type.name == 'IF_ELIF_CHAIN':
            return self._if_generate_full_elif_chain(region)
        # [R36] Skip IfRegions whose entry is owned by a BoolOpRegion.
        # This happens when value-context chained compares are operands of
        # `and`/`or` (e.g. `return A < x < B or C < x < D`). The chained
        # compare IfRegions have entries that are BoolOp chain blocks, and
        # the BoolOpRegion owns them via block_to_region. Without this check,
        # the IfRegion generates `if ... : pass`, consuming blocks that the
        # BoolOpRegion needs for expression reconstruction.
        if region.entry is not None:
            _entry_owner = self.region_analyzer.block_to_region.get(region.entry)
            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:
                for b in region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(id(region))
                return []
        # [Round4-04] 链式比较作赋值右值'''

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix6 applied")
else:
    print("FAIL: old_string not found")
