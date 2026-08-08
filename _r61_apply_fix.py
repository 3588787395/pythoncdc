#!/usr/bin/env python3
"""R61 fix: Add BoolOpRegion entry dispatch in _loop_dispatch_block."""
import re

FILE = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# The anchor: unique pattern in _loop_dispatch_block
old = "                    self._generated_regions.add(id(_child))\n                    return True\n                break\n        block_role = self.region_analyzer.get_block_role(block)\n        if block_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):"

new = """                    self._generated_regions.add(id(_child))
                    return True
                break
        # [R61 fix] BoolOpRegion entry dispatch in loop body.
        # Region reduction algorithm principle 4 (parent references child entry)
        # + principle 2 (unique block ownership) + principle 3 (nesting = abstract
        # node): when a loop body block is the entry of a BoolOpRegion (value-
        # context short-circuit, e.g. `x = a or b`), it must be dispatched to
        # _generate_boolop. Without this, the BoolOpRegion entry block is processed
        # by _generate_block_statements as a plain expression statement, collapsing
        # `a or b` to just `b` (dropping `a` + JUMP_IF_TRUE_OR_POP + COPY + STORE).
        _boolop_entry_region = None
        for _child in (region.children or []):
            if (isinstance(_child, BoolOpRegion)
                    and _child.entry is block
                    and not getattr(_child, 'is_condition_context', False)):
                _bid = id(_child)
                if (_bid not in self._generated_regions
                        and _bid not in self._generating_regions):
                    _boolop_entry_region = _child
                break
        if _boolop_entry_region is None:
            _er_b = self.region_analyzer.get_entry_region_for_block(block)
            if (_er_b is not None
                    and isinstance(_er_b, BoolOpRegion)
                    and _er_b.entry is block
                    and not getattr(_er_b, 'is_condition_context', False)):
                _bid = id(_er_b)
                if (_bid not in self._generated_regions
                        and _bid not in self._generating_regions):
                    _boolop_entry_region = _er_b
        if _boolop_entry_region is not None:
            _boolop_ast = self._generate_region(_boolop_entry_region)
            if _boolop_ast:
                if isinstance(_boolop_ast, list):
                    body_stmts.extend(_boolop_ast)
                else:
                    body_stmts.append(_boolop_ast)
            for _b in _boolop_entry_region.blocks:
                self.generated_blocks.add(_b)
                self.generated_offsets.add(_b.start_offset)
            self._generated_regions.add(id(_boolop_entry_region))
            return True
        block_role = self.region_analyzer.get_block_role(block)
        if block_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):"""

# Check uniqueness
count = content.count(old)
print(f"Occurrences of old string: {count}")
if count != 1:
    print("ERROR: old string is not unique!")
    # Try to find partial matches
    idx = content.find("self._generated_regions.add(id(_child))\n                    return True\n                break\n        block_role")
    print(f"Partial match at offset: {idx}")
    if idx >= 0:
        # Show surrounding context
        start = max(0, idx - 100)
        end = min(len(content), idx + 200)
        print(f"Context: ...{repr(content[start:end])}...")
    exit(1)

content = content.replace(old, new, 1)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix applied successfully!")
