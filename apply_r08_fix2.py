"""Apply R8 fix 2: Add explicit Continue after LOOP_BACK_EDGE block with user instructions."""
import re

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The exact code to find - using the line numbers from the file
old_code = """                if effective:
                    stmts.extend(self._build_effective_stmts(block, effective))
                else:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                self.generated_blocks.add(block)
                continue
            # 区域归约算法原则 2（每块唯一归属）："""

new_code = """                if effective:
                    stmts.extend(self._build_effective_stmts(block, effective))
                else:
                    bs = self._generate_block_statements(block)
                    if bs:
                        stmts.extend(bs)
                # [R8 fix] LOOP_BACK_EDGE 含有效用户指令时 JUMP_BACKWARD
                # 是显式 continue（非自然回边），必须输出 Continue 以
                # 保持字节码等价性（缺少 JUMP_BACKWARD 导致字节码差异）。
                _be_last2 = block.get_last_instruction()
                if _be_last2 and _be_last2.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    if self._current_loop:
                        _loop_hdr = self._current_loop.header_block
                        if _loop_hdr and _be_last2.argval is not None:
                            _be_target = self.cfg.get_block_by_offset(_be_last2.argval)
                            if _be_target and _be_target == _loop_hdr:
                                stmts.append({'type': 'Continue'})
                self.generated_blocks.add(block)
                continue
            # 区域归约算法原则 2（每块唯一归属）："""

if old_code not in content:
    print("ERROR: old_code not found!")
    # Show context around line 15085
    lines = content.split('\n')
    for i in range(15082, 15096):
        if i < len(lines):
            print(f"  {i+1}: {repr(lines[i])}")
else:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
