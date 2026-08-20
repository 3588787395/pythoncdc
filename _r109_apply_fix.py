import sys

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            for cb in region.cleanup_blocks:
                if cb not in self.generated_blocks:
                    self.generated_blocks.add(cb)

            # [R56 fix]"""

new = """            # cleanup_blocks may contain blocks from finally_blocks (finally
            # exception path blocks collected as cleanup). If marked generated
            # here, finalbody traversal skips them, losing user code (e.g. print).
            _finally_block_set_cleanup = set(region.finally_blocks) if region.finally_blocks else set()
            for cb in region.cleanup_blocks:
                if cb in _finally_block_set_cleanup:
                    continue
                if cb not in self.generated_blocks:
                    self.generated_blocks.add(cb)

            # [R56 fix]"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - replaced successfully")
else:
    print("NOT FOUND - checking for similar patterns...")
    idx = content.find('for cb in region.cleanup_blocks:')
    if idx >= 0:
        # Show surrounding context
        start = max(0, idx - 100)
        end = min(len(content), idx + 200)
        context = content[start:end]
        print(f"Context around 'for cb in region.cleanup_blocks:' (idx={idx}):")
        print(repr(context))
    else:
        print("'for cb in region.cleanup_blocks:' not found at all!")
