with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """                        elif isinstance(other, BoolOpRegion) and isinstance(r, IfRegion):
                            # [R36] If the IfRegion shares the same entry as the
                            # BoolOpRegion and the BoolOpRegion owns the entry,
                            # the IfRegion is a spurious artifact (e.g. value-context
                            # chained compare detected as IfRegion with the `or`
                            # jump block as entry). Filter it out.
                            if (r.entry and r.entry == other.entry
                                    and self.region_analyzer.block_to_region.get(r.entry) is other):
                                is_contained = True
                                break
                            if r.condition_block and r.condition_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break"""

new = """                        elif isinstance(other, BoolOpRegion) and isinstance(r, IfRegion):
                            # [R36] If the IfRegion's entry is in the BoolOpRegion's
                            # blocks AND the BoolOpRegion owns that entry (via
                            # block_to_region), the IfRegion is a spurious artifact
                            # (e.g. value-context chained compare detected as IfRegion
                            # whose entry is a BoolOp chain block). Filter it out so
                            # the BoolOpRegion handles generation.
                            if (r.entry and r.entry in other.blocks
                                    and self.region_analyzer.block_to_region.get(r.entry) is other):
                                is_contained = True
                                break
                            if r.condition_block and r.condition_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix5b applied")
else:
    print("FAIL: old_string not found")
