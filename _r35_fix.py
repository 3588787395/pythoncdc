"""Fix is_method_form conversion in ast_generator_v2.py"""
import re

filepath = "core/cfg/ast_generator_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Line ~24024 - comprehension iter context
# Replace the is_method_form conversion in the comprehension iter handling
old_block = """                                    # [关键修复] 处理 Attribute 类型的迭代对象
                                    # 当推导式的迭代对象是方法调用时（如 data.values()）
                                    # iter_obj 是 Attribute 类型，需要转换为 Call 类型
                                    # 但只有当 is_method_form 为 True 时才转换（Python 3.11+ 标志位）
                                    elif isinstance(iter_obj, dict) and iter_obj.get('type') == 'Attribute':
                                        is_method_form = iter_obj.get('is_method_form', False)
                                        if is_method_form:
                                            iter_obj = {
                                                'type': 'Call',
                                                'func': iter_obj,
                                                'args': [],
                                                'kwargs': [],
                                                'lineno': iter_obj.get('lineno', 1)
                                            }"""

new_block = """                                    # [R35] Fix: is_method_form should NOT convert Attribute to Call
                                    # in comprehension iter context. The is_method_form flag is a
                                    # compiler optimization hint, not a definitive indicator of a
                                    # method call. When LOAD_ATTR is followed by GET_ITER (not CALL),
                                    # the attribute is being iterated, not called. If the attribute
                                    # IS a method call (e.g. data.values()), the CALL instruction
                                    # would have been processed earlier and iter_obj would already
                                    # be a Call node.
                                    elif isinstance(iter_obj, dict) and iter_obj.get('type') == 'Attribute':
                                        pass  # Keep as Attribute, do not convert to Call"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    print("Fix 1 applied: comprehension iter context (line ~24022)")
else:
    print("Fix 1 NOT FOUND - trying alternative match")
    # Try with different whitespace
    # Search for the pattern more loosely
    import re
    pattern = r"elif isinstance\(iter_obj, dict\) and iter_obj\.get\('type'\) == 'Attribute':\s*\n\s*is_method_form = iter_obj\.get\('is_method_form', False\)\s*\n\s*if is_method_form:\s*\n\s*iter_obj = \{\s*\n\s*'type': 'Call',\s*\n\s*'func': iter_obj,\s*\n\s*'args': \[\],\s*\n\s*'kwargs': \[\],\s*\n\s*'lineno': iter_obj\.get\('lineno', 1\)\s*\n\s*\}"
    
    # Find all matches
    matches = list(re.finditer(pattern, content))
    print(f"  Found {len(matches)} regex matches")
    for i, m in enumerate(matches):
        print(f"  Match {i}: position {m.start()}-{m.end()}")
        # Show context
        start = max(0, m.start() - 200)
        end = min(len(content), m.end() + 100)
        context = content[start:end]
        print(f"  Context: ...{repr(context[:300])}...")

# Fix 2: Line ~7216 - _generate_block_content_skip_iterator context
old_block2 = """# [关键修复] 处理 Attribute 类型的迭代对象（当 GET_ITER 被跳过时）
# 当 _generate_block_content_skip_iterator 跳过 GET_ITER 时，
# 迭代对象可能是 Attribute 类型（如 data.values）
# 但原始字节码中有 CALL 指令，所以这应该是一个方法调用
# 但只有当 is_method_form 为 True 时才转换（Python 3.11+ 标志位）
elif isinstance(iter_obj, dict) and iter_obj.get('type') == 'Attribute':
is_method_form = iter_obj.get('is_method_form', False)
if is_method_form:
# 将 Attribute 转换为 Call 节点（方法调用）
iter_obj = {
'type': 'Call',
'func': iter_obj,
'args': [],
'kwargs': [],
'lineno': iter_obj.get('lineno', 1)
}"""

# This block has different indentation, let's handle it separately
# For now, just apply Fix 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
