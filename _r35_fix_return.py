"""Fix _generate_return_ast to not skip CALL instructions"""
import re

filepath = "core/cfg/region_ast_generator.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: First code path (return_instr is not None)
old1 = "skip_ops = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\n                                'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\n                                'PRECALL', 'CALL')"
new1 = "skip_ops = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\n                                'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\n                                'PRECALL')\n                    # [R35] Do NOT skip CALL - needed for comprehension reconstruction"

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix 1 applied: first code path")
else:
    print("Fix 1 NOT FOUND - trying regex")
    # Try regex
    pattern1 = r"skip_ops = \('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\s*'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\s*'PRECALL', 'CALL'\)"
    matches = list(re.finditer(pattern1, content))
    print(f"  Regex matches: {len(matches)}")
    if matches:
        content = re.sub(pattern1, new1.replace('\\n', '\n'), content, count=1)
        print("  Fix 1 applied via regex")

# Fix 2: Second code path (return_instr is None)
old2 = "_skip_base = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\n              'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\n              'PRECALL', 'CALL')"
new2 = "_skip_base = ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\n              'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\n              'PRECALL')\n                # [R35] Do NOT skip CALL - needed for comprehension reconstruction"

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fix 2 applied: second code path")
else:
    print("Fix 2 NOT FOUND - trying regex")
    pattern2 = r"_skip_base = \('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL',\s*'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO',\s*'PRECALL', 'CALL'\)"
    matches = list(re.finditer(pattern2, content))
    print(f"  Regex matches: {len(matches)}")
    if matches:
        content = re.sub(pattern2, new2.replace('\\n', '\n'), content, count=1)
        print("  Fix 2 applied via regex")

# Also check for any remaining 'PRECALL', 'CALL' in skip lists
remaining = re.findall(r"'PRECALL',\s*'CALL'", content)
print(f"\nRemaining 'PRECALL', 'CALL' patterns: {len(remaining)}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
