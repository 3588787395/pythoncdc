"""Add more debug to trace where block 50 is collected"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add debug to else_blocks collection
old1 = """            if region.else_blocks:
                for _eb in region.else_blocks:
                    for _succ in _eb.successors:"""

new1 = """            if region.else_blocks:
                import sys as _sys_dbg_eb
                for _eb in region.else_blocks:
                    print(f"DEBUG else: eb={_eb.start_offset}, succs={[s.start_offset for s in _eb.successors]}", file=_sys_dbg_eb.stderr)
                    for _succ in _eb.successors:"""

# Add debug to try_blocks collection
old2 = """            if not _post_try_blocks_r19n2:
                for _tb in region.try_blocks:"""

new2 = """            if not _post_try_blocks_r19n2:
                import sys as _sys_dbg_tb
                print(f"DEBUG try_blocks: post_try_empty={not _post_try_blocks_r19n2}", file=_sys_dbg_tb.stderr)
                for _tb in region.try_blocks:"""

# Add debug to finally_copy_blocks collection
old3 = """            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):"""

new3 = """            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):
                import sys as _sys_dbg_fc
                print(f"DEBUG fc: post_try_empty={not _post_try_blocks_r19n2}, fc_keys={list(region.finally_copy_blocks.keys())}", file=_sys_dbg_fc.stderr)"""

if old1 in content and old2 in content and old3 in content:
    content = content.replace(old1, new1, 1)
    content = content.replace(old2, new2, 1)
    content = content.replace(old3, new3, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Debug added successfully!")
else:
    print(f"old1 found: {old1 in content}")
    print(f"old2 found: {old2 in content}")
    print(f"old3 found: {old3 in content}")
