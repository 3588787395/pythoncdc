import re

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            for r in self.regions:
                if isinstance(r, LoopRegion) and (r.condition_block is entry_block or
                    (r.header_block and entry_block.start_offset in [s.start_offset for s in r.header_block.predecessors])):
                    entry_region = r
                    break
            if isinstance(entry_region, LoopRegion) and (entry_region.condition_block == entry_block or
                (entry_region.header_block and entry_block.start_offset in [s.start_offset for s in entry_region.header_block.predecessors])):"""

new = """            for r in self.regions:
                if isinstance(r, LoopRegion) and (r.condition_block is entry_block or
                    (r.header_block and entry_block.start_offset in [s.start_offset for s in r.header_block.predecessors])):
                    # [Round6-whileTrue 修复] 仅当 entry_block 属于循环区域（在
                    # blocks 或 body_blocks 中）时才将 entry_region 设为该循环。
                    # 否则 entry_block 是循环前的预语句块（如 steps=...;
                    # engine.set_engine(engine)），不应被循环吸收。
                    if entry_block in r.blocks or entry_block in getattr(r, 'body_blocks', []):
                        entry_region = r
                        break
            if isinstance(entry_region, LoopRegion) and (entry_region.condition_block == entry_block or
                (entry_region.header_block and entry_block.start_offset in [s.start_offset for s in entry_region.header_block.predecessors])):"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: fixed entry block absorption into while True loop")
else:
    print("ERROR: old string not found")
