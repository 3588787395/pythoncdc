"""Repro 01: f-string with != in FormattedValue, before an if statement.

Pattern: if-condition block has pre-statements including an f-string
assignment whose FormattedValue contains COMPARE_OP (!=). The COMPARE_OP
clearing heuristic in _if_extract_cond_instructions truncates the f-string.

Expected: user_code preserves all 3 BUILD_STRING segments.
"""
def f(a, b):
    x = 'pre'
    user_code = f'val_{a!s}_{a != b!s}_end'
    if a == 0:
        return user_code
    return x
