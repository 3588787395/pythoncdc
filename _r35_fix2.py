"""Fix all is_method_form conversions in ast_generator_v2.py"""
import re

filepath = "core/cfg/ast_generator_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# Fix all occurrences where Iter(Attribute) with is_method_form is converted to Call
# Pattern: if isinstance(inner_value, dict) and inner_value.get('type') == 'Attribute':
#              is_method_form = inner_value.get('is_method_form', False)
#              if is_method_form:
#                  ... convert to Call ...
#          else:
#              ... use inner_value ...

# Also fix: elif isinstance(iter_obj, dict) and iter_obj.get('type') == 'Attribute':
#              is_method_form = iter_obj.get('is_method_form', False)
#              if is_method_form:
#                  ... convert to Call ...

# Strategy: Replace all `if is_method_form:` that are followed by Call conversion
# with `if False:  # [R35] Disabled`
# But we need to be careful to only target the comprehension iter context

# Let's find all occurrences of is_method_form in the file
pattern = r"is_method_form = (?:inner_value|iter_obj)\.get\('is_method_form', False\)\s*\n\s*if is_method_form:"

matches = list(re.finditer(pattern, content))
print(f"Found {len(matches)} occurrences of is_method_form conversion")

for i, m in enumerate(matches):
    # Show context
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 200)
    context = content[start:end]
    print(f"\nMatch {i} at position {m.start()}:")
    print(repr(content[m.start():m.end()]))
    print(f"Context before: {repr(content[max(0,m.start()-200):m.start()][-100:])}")

# Now replace all `if is_method_form:` that are part of the comprehension iter conversion
# with `if False:  # [R35] Disabled: is_method_form is not reliable for iter context`
# We need to be specific to not break legitimate CALL handling

# Actually, let's take a simpler approach: just comment out the is_method_form check
# by replacing `if is_method_form:` with `if False:  # [R35]`

# But we need to be careful about which ones to disable. Let's disable all of them
# since the is_method_form flag is NOT a reliable indicator of method calls.
# The correct way to determine if an attribute is being called is to check for
# a CALL instruction, not the arg & 1 flag.

new_content = content.replace(
    "is_method_form = inner_value.get('is_method_form', False)\n                                        if is_method_form:",
    "is_method_form = False  # [R35] Disabled: not reliable for iter context\n                                        if is_method_form:",
    1
)

if new_content != content:
    count += 1
    print(f"\nFixed inner_value.is_method_form at one location")

# Also fix the iter_obj version
content = new_content
new_content = content.replace(
    "is_method_form = iter_obj.get('is_method_form', False)\n                                        if is_method_form:",
    "is_method_form = False  # [R35] Disabled: not reliable for iter context\n                                        if is_method_form:",
    1
)

if new_content != content:
    count += 1
    print(f"Fixed iter_obj.is_method_form at one location")

# Fix the _generate_block_content_skip_iterator version (different indentation)
content = new_content
# This one uses different indentation (no leading spaces in the grep output)
# Let's try to find it
pattern2 = r"is_method_form = iter_obj\.get\('is_method_form', False\)\s*\n\s*if is_method_form:"
matches2 = list(re.finditer(pattern2, content))
print(f"\nRemaining occurrences after fix: {len(matches2)}")

for m in matches2:
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 50)
    print(f"  At {m.start()}: {repr(content[start:end])}")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal fixes applied: {count}")
