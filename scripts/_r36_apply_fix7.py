with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix6: Don't mark blocks as generated, just return [] to skip IfRegion
old1 = '''        if region.entry is not None:
            _entry_owner = self.region_analyzer.block_to_region.get(region.entry)
            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:
                for b in region.blocks:
                    self.generated_blocks.add(b)
                self._generated_regions.add(id(region))
                return []'''

new1 = '''        if region.entry is not None:
            _entry_owner = self.region_analyzer.block_to_region.get(region.entry)
            if isinstance(_entry_owner, BoolOpRegion) and _entry_owner is not region:
                # [R36] Don't mark blocks as generated — the BoolOpRegion will
                # handle them. Just skip this IfRegion.
                self._generated_regions.add(id(region))
                return []'''

# Fix3: Don't mark blocks as generated, just cache and return []
old2 = '''                            _cc_expr = self._build_chained_compare_from_region_data(region)
                            if _cc_expr is not None:
                                if not hasattr(self, '_chain_compare_expr_cache'):
                                    self._chain_compare_expr_cache = {}
                                self._chain_compare_expr_cache[id(_merge)] = _cc_expr
                                for b in region.blocks:
                                    self.generated_blocks.add(b)
                                self._generated_regions.add(id(region))
                                return []'''

new2 = '''                            _cc_expr = self._build_chained_compare_from_region_data(region)
                            if _cc_expr is not None:
                                if not hasattr(self, '_chain_compare_expr_cache'):
                                    self._chain_compare_expr_cache = {}
                                self._chain_compare_expr_cache[id(_merge)] = _cc_expr
                                # [R36] Don't mark blocks as generated — the
                                # BoolOpRegion will handle them via _try_build_chained_compare_in_boolop.
                                self._generated_regions.add(id(region))
                                return []'''

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix6b: applied")
else:
    print("FAIL: old1 not found")

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix3b: applied")
else:
    print("FAIL: old2 not found")

with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
