#!/usr/bin/env python3
"""R61 fix part 2: Add BoolOpRegion fallback dispatch in _process_if_blocks."""

FILE = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# The anchor: after child_expr_regions block, before PUSH_EXC_INFO check
old = """                    self._generated_regions.add(child_id)
                continue
            if any(i.opname == 'PUSH_EXC_INFO' for i in block.instructions):"""

new = """                    self._generated_regions.add(child_id)
                continue
            # [R61 fix] BoolOpRegion fallback: when BoolOpRegion's parent is
            # the enclosing LoopRegion (not the current IfRegion), it won't
            # appear in child_expr_regions (which is built from region.children).
            # Use get_entry_region_for_block to find it. This fixes the
            # JUMP_IF_TRUE_OR_POP expression assignment collapse pattern where
            # `x = a or b` inside an if-body has BoolOpRegion.parent=LoopRegion.
            if not hasattr(self, '_r61_boolop_fallback_checked'):
                self._r61_boolop_fallback_checked = set()
            if block not in self._r61_boolop_fallback_checked:
                self._r61_boolop_fallback_checked.add(block)
                _r61_er = self.region_analyzer.get_entry_region_for_block(block)
                if (_r61_er is not None
                        and isinstance(_r61_er, BoolOpRegion)
                        and _r61_er.entry is block
                        and not getattr(_r61_er, 'is_condition_context', False)):
                    _r61_bid = id(_r61_er)
                    if (_r61_bid not in self._generated_regions
                            and _r61_bid not in self._generating_regions):
                        _r61_ast = self._generate_boolop(_r61_er)
                        if _r61_ast:
                            if isinstance(_r61_ast, list):
                                stmts.extend(_r61_ast)
                            else:
                                stmts.append(_r61_ast)
                        for _r61_b in _r61_er.blocks:
                            self.generated_blocks.add(_r61_b)
                            self.generated_offsets.add(_r61_b.start_offset)
                        self._generated_regions.add(_r61_bid)
                        continue
            if any(i.opname == 'PUSH_EXC_INFO' for i in block.instructions):"""

count = content.count(old)
print(f"Occurrences of old string: {count}")
if count != 1:
    print("ERROR: old string is not unique!")
    exit(1)

content = content.replace(old, new, 1)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix part 2 applied successfully!")
