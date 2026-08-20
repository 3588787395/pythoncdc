"""Remove all debug output from region_ast_generator.py"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove else_blocks debug
old1 = """            if region.else_blocks:
                import sys as _sys_dbg_eb
                for _eb in region.else_blocks:
                    print(f"DEBUG else: eb={_eb.start_offset}, succs={[s.start_offset for s in _eb.successors]}", file=_sys_dbg_eb.stderr)
                    for _succ in _eb.successors:"""
new1 = """            if region.else_blocks:
                for _eb in region.else_blocks:
                    for _succ in _eb.successors:"""
if old1 in content:
    content = content.replace(old1, new1, 1)

# Remove try_blocks debug
old2 = """            if not _post_try_blocks_r19n2:
                import sys as _sys_dbg_tb
                print(f"DEBUG try_blocks: post_try_empty={not _post_try_blocks_r19n2}", file=_sys_dbg_tb.stderr)
                for _tb in region.try_blocks:"""
new2 = """            if not _post_try_blocks_r19n2:
                for _tb in region.try_blocks:"""
if old2 in content:
    content = content.replace(old2, new2, 1)

# Remove fc debug
old3 = """            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):
                import sys as _sys_dbg_fc
                print(f"DEBUG fc: post_try_empty={not _post_try_blocks_r19n2}, fc_keys={list(region.finally_copy_blocks.keys())}", file=_sys_dbg_fc.stderr)"""
new3 = """            if not _post_try_blocks_r19n2 and getattr(region, 'finally_copy_blocks', None):"""
if old3 in content:
    content = content.replace(old3, new3, 1)

# Remove post-try loop debug
old4 = """            _post_try_stmts_r19n2 = []
            import sys as _sys_dbg_pt
            print(f"DEBUG post-try: _post_try_blocks_r19n2={[b.start_offset for b in _post_try_blocks_r19n2]}", file=_sys_dbg_pt.stderr)
            for _ptb in _post_try_blocks_r19n2:
                # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                # post-try 块的结构归属是 try-except 之后的顺序代码。即使该块
                # 在 try body / handler 生成过程中被误标记为 generated（如
                # finally 正常路径副本块的后继，含 RETURN_VALUE 的块在
                # _generate_block_statements 中被处理时标记了 offset），也必须
                # 清除标记并生成语句，否则 post-try 代码（如 `return None`）
                # 会丢失。原实现仅清除 _post_try_pre_generated_r19n2 中的块，
                # 漏掉了被其他逻辑标记的块。
                print(f"DEBUG post-try: processing block {_ptb.start_offset}, in generated={_ptb in self.generated_blocks}", file=_sys_dbg_pt.stderr)
                self.generated_blocks.discard(_ptb)
                self.generated_offsets.discard(_ptb.start_offset)
                if _ptb in self.generated_blocks:
                    print(f"DEBUG post-try: block {_ptb.start_offset} still in generated, skipping", file=_sys_dbg_pt.stderr)
                    continue"""
new4 = """            _post_try_stmts_r19n2 = []
            for _ptb in _post_try_blocks_r19n2:
                # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                # post-try 块的结构归属是 try-except 之后的顺序代码。即使该块
                # 在 try body / handler 生成过程中被误标记为 generated（如
                # finally 正常路径副本块的后继，含 RETURN_VALUE 的块在
                # _generate_block_statements 中被处理时标记了 offset），也必须
                # 清除标记并生成语句，否则 post-try 代码（如 `return None`）
                # 会丢失。原实现仅清除 _post_try_pre_generated_r19n2 中的块，
                # 漏掉了被其他逻辑标记的块。
                self.generated_blocks.discard(_ptb)
                self.generated_offsets.discard(_ptb.start_offset)
                if _ptb in self.generated_blocks:
                    continue"""
if old4 in content:
    content = content.replace(old4, new4, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("All debug output removed!")
