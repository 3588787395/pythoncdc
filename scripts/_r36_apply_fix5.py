with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """                        elif isinstance(other, BoolOpRegion) and isinstance(r, IfRegion):
                            if r.condition_block and r.condition_block in other.blocks:
                                pass
                            else:
                                is_contained = True
                                break"""

new = """                        elif isinstance(other, BoolOpRegion) and isinstance(r, IfRegion):
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

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix5 applied")
else:
    print("FAIL: old_string not found")
