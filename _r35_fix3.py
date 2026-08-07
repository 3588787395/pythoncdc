"""Fix ALL is_method_form conversions using regex"""
import re

filepath = "core/cfg/ast_generator_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ALL occurrences of:
#   is_method_form = <var>.get('is_method_form', False)
#   <whitespace>if is_method_form:
# with:
#   is_method_form = False  # [R35] Disabled: is_method_form is a compiler hint, not reliable for iter context
#   <whitespace>if is_method_form:

pattern = r"(is_method_form = (?:inner_value|iter_obj)\.get\('is_method_form', False\))(\s*\n\s*)(if is_method_form:)"

def replacer(m):
    return f"is_method_form = False  # [R35] Disabled: compiler hint, not reliable for iter context{m.group(2)}if is_method_form:"

new_content, count = re.subn(pattern, replacer, content)

print(f"Replaced {count} occurrences")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done")
