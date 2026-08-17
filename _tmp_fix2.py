import re

filepath = 'core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                    if lr_a.is_while_true and cond_b and cond_b == lr_a.header_block:
                        if body_a_set and body_b_set and body_b_set <= body_a_set:
                            removal_set.add(id(lr_a))
                            continue
                    if lr_b.is_while_true and cond_a and cond_a == lr_b.header_block:
                        if body_a_set and body_b_set and body_a_set <= body_b_set:
                            removal_set.add(id(lr_b))
                            continue"""

new = """                    if lr_a.is_while_true and cond_b and cond_b == lr_a.header_block:
                        # [Round6-whileTrue 修复] 仅当内层循环 body 覆盖外层
                        # while True 的几乎所有块时才移除外层循环。若外层 while True
                        # 包含多个内层 while 循环（body 差异 > 2 块），外层循环
                        # 非冗余——它是 `while True: while x: ...; while y: ...` 的
                        # 外层包装，移除会丢失无限循环语义，导致末尾产生虚假
                        # return None。
                        _diff_a = body_a_set - body_b_set
                        if body_a_set and body_b_set and len(_diff_a) <= 2:
                            removal_set.add(id(lr_a))
                            continue
                    if lr_b.is_while_true and cond_a and cond_a == lr_b.header_block:
                        _diff_b = body_b_set - body_a_set
                        if body_a_set and body_b_set and len(_diff_b) <= 2:
                            removal_set.add(id(lr_b))
                            continue"""

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: fixed while True loop removal logic")
else:
    print("ERROR: old string not found")
    lines = content.split('\n')
    for i in range(3655, 3666):
        print(f"  L{i+1}: {repr(lines[i])}")
