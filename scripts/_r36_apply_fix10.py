with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """                        elif isinstance(r, BoolOpRegion) and isinstance(other, IfRegion):
                            if r.entry and r.entry == other.entry:
                                entry_owner = self.region_analyzer.block_to_region.get(r.entry)
                                if entry_owner is r:
                                    pass
                                else:
                                    is_contained = True
                                    break
                            else:
                                is_contained = True
                                break"""

new = """                        elif isinstance(r, BoolOpRegion) and isinstance(other, IfRegion):
                            # [R36] If the BoolOpRegion owns its entry block (via
                            # block_to_region), it should NOT be filtered out even
                            # if the entry is in another IfRegion's blocks. This
                            # happens when value-context chained compares are
                            # operands of `and`/`or` — the chained compare's
                            # merge_block (a BoolOp jump block) is the BoolOp's
                            # entry, and it's also in the chained compare
                            # IfRegion's blocks. The BoolOpRegion owns the entry.
                            if r.entry and r.entry == other.entry:
                                entry_owner = self.region_analyzer.block_to_region.get(r.entry)
                                if entry_owner is r:
                                    pass
                                else:
                                    is_contained = True
                                    break
                            elif r.entry and r.entry in other.blocks:
                                entry_owner = self.region_analyzer.block_to_region.get(r.entry)
                                if entry_owner is r:
                                    pass
                                else:
                                    is_contained = True
                                    break
                            else:
                                is_contained = True
                                break"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix10 applied")
else:
    print("FAIL: old_string not found")
