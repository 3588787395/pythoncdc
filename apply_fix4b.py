"""Apply fix4b - adjust condition to not check merge."""
filepath = 'f:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """                                if _jf_target is not None and _jf_target != merge:
                                    merge = else_succ"""

new_code = """                                if _jf_target is not None and _jf_target != else_succ:
                                    merge = else_succ"""

if old_code in content:
    content = content.replace(old_code, new_code, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix4b applied successfully!")
else:
    print("ERROR: old code not found for fix4b!")
