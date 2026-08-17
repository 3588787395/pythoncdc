#!/usr/bin/env python3
"""Fix _generate_constant: escape \r and \\ in triple-quoted strings"""

filepath = 'core/cfg/code_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = """            if '\\n' in value:
                    # 多行字符串使用三引号
                    if '\"\"\"' in value:
                        # 如果包含三引号，使用单引号三引号
                        return f\"'''{value}'''\"
                    else:
                        # 否则使用双引号三引号
                        return f'\"\"\"{value}\"\"\"'"""

# The above might not match due to escaping. Let me use a different approach.
# Search for the actual pattern in the file.
import re

# Find the multiline string handling code
pattern = r"if '\\n' in value:.*?return f'\"\"\"\{value\}\"\"\"'"
match = re.search(pattern, content, re.DOTALL)
if match:
    print(f"Found at position {match.start()}-{match.end()}")
    print(f"Matched text: {repr(match.group()[:100])}...")
else:
    print("Pattern not found, trying manual search...")
    # Find by line number
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "'\\n' in value" in line or "if '\\n' in value" in line:
            print(f"Found at line {i+1}: {repr(line)}")
            for j in range(i, min(i+8, len(lines))):
                print(f"  {j+1}: {repr(lines[j])}")
            break
