with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The docstring ends with """ followed by the for loop
old = '        """\n        for r in self.regions:\n            if (isinstance(r, IfRegion)\n                    and r.entry is chain_block'

new = '        """\n        # [R36] Check cache first — _generate_if may have cached the chained\n        # compare expression when it detected the IfRegion is a BoolOp operand.\n        if hasattr(self, \'_chain_compare_expr_cache\'):\n            _cached = self._chain_compare_expr_cache.get(id(chain_block))\n            if _cached is not None:\n                return _cached\n        for r in self.regions:\n            if (isinstance(r, IfRegion)\n                    and r.entry is chain_block'

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: cache check added")
else:
    print("FAIL: pattern not found")
    # Find the actual pattern
    import re
    matches = list(re.finditer(r'"""$', content, re.MULTILINE))
    for m in matches[:5]:
        start = max(0, m.start() - 50)
        end = min(len(content), m.end() + 200)
        print(f"Found at {m.start()}: {repr(content[m.start():m.end()+100])}")
