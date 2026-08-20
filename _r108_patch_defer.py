"""Patch script: add deferred try generation before return body_stmts in _generate_try_body."""
p = 'core/cfg/region_ast_generator.py'
f = open(p, 'r', encoding='utf-8')
c = f.read()
f.close()

old = """                        self._generated_regions.add(child_id)

        return body_stmts

    def _generate_try(self, region: TryExceptRegion)"""

new = """                        self._generated_regions.add(child_id)

        # Generate deferred nested try regions (those after an IfRegion merge_block)
        for ntr in sorted(nested_try_regions, key=lambda r: r.try_offset_start):
            if id(ntr) in self._generated_regions or id(ntr) in self._generating_regions:
                continue
            _defer_for_if2 = False
            for _ir in self.region_analyzer.regions:
                if (isinstance(_ir, IfRegion) and _ir is not region
                        and getattr(_ir, 'parent', None) is region
                        and _ir.merge_block is not None):
                    if ntr.entry.start_offset > _ir.merge_block.start_offset:
                        _defer_for_if2 = True
                        break
            if _defer_for_if2:
                self.generated_blocks.discard(ntr.entry)
                for b in ntr.try_blocks:
                    self.generated_blocks.discard(b)
                for _, _, hblocks in ntr.except_handlers:
                    for hb in hblocks:
                        self.generated_blocks.discard(hb)
                for cb in ntr.cleanup_blocks:
                    self.generated_blocks.discard(cb)
                nested_ast = self._generate_try(ntr)
                if nested_ast:
                    body_stmts.append(nested_ast)
                for b in ntr.blocks:
                    self.generated_blocks.add(b)

        return body_stmts

    def _generate_try(self, region: TryExceptRegion)"""

n = c.count(old)
print(f'Found {n} occurrences')
if n == 1:
    c = c.replace(old, new)
    f = open(p, 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print('Done')
else:
    print('ERROR: expected exactly 1 occurrence')
