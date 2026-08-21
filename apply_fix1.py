"""Apply fix to region_ast_generator.py - replace the Continue generation block."""
import re

filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# The old code block to replace
old_code = """            if (_last is not None
                    and _last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                    and not _meaningful):
                _cont = {'type': 'Continue'}
                if isinstance(if_result, list):
                    if_result = if_result + [_cont]
                else:
                    if_result = [if_result, _cont]
                self.generated_blocks.add(_blk)
                self.generated_offsets.add(_blk.start_offset)"""

# The new code with explicit continue check
new_code = """            if (_last is not None
                    and _last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                    and not _meaningful):
                # [spf-r01-fix1] 仅当 then_blocks 中存在以显式 JUMP_BACKWARD 结尾的
                # 块时才生成 Continue。若 then_blocks 末块以非跳转指令结尾
                # （fall-through 到 merge/back_edge），是循环自然回边（隐式
                # continue），不生成显式 Continue——否则编译器生成额外
                # JUMP_BACKWARD，导致 FOR_ITER 目标偏移 +2。
                # 典型：for k,v in d.items(): if not k < 'm': <body>
                _has_explicit_continue = False
                for _tb in (region.then_blocks or []):
                    _tb_last = _tb.get_last_instruction()
                    if (_tb_last is not None
                            and _tb_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')):
                        _has_explicit_continue = True
                        break
                if _has_explicit_continue:
                    _cont = {'type': 'Continue'}
                    if isinstance(if_result, list):
                        if_result = if_result + [_cont]
                    else:
                        if_result = [if_result, _cont]
                    self.generated_blocks.add(_blk)
                    self.generated_offsets.add(_blk.start_offset)"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: old code not found!")
    # Try to find it
    idx = content.find("and not _meaningful):")
    if idx >= 0:
        print(f"Found 'and not _meaningful):' at position {idx}")
        print(f"Context: {repr(content[idx:idx+200])}")
