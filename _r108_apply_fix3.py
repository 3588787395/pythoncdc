"""Fix: always clear generated marker for post-try blocks"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            _post_try_stmts_r19n2 = []
            for _ptb in _post_try_blocks_r19n2:
                # 清除标记（仅清除我们设置的，不影响其他标记）
                if _ptb in _post_try_pre_generated_r19n2:
                    self.generated_blocks.discard(_ptb)
                    self.generated_offsets.discard(_ptb.start_offset)
                if _ptb in self.generated_blocks:
                    continue"""

new = """            _post_try_stmts_r19n2 = []
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

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Old text not found!")
