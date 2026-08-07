with open('core/cfg/region_ast_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """                if _merge_is_return_only and not _has_if_like_then:
                    results.append({'type': 'Return', 'value': boolop_expr})"""

new = """                if _merge_is_return_only and not _has_if_like_then:
                    if _merge_return_followup is not None:
                        self.generated_blocks.add(_merge_return_followup)
                    results.append({'type': 'Return', 'value': boolop_expr})"""

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_ast_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fix2b applied")
else:
    print("FAIL: old_string not found")
