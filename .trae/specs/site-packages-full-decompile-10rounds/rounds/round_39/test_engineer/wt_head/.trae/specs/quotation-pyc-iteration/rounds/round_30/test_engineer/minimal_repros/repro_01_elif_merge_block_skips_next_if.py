"""R30 最小复现01：elif chain merge_block 被错误标记为 generated_blocks
导致后续顶级 IfRegion 被跳过"""
import sys
sys.path.insert(0, '/workspace')

# Pattern: Two consecutive if-statements where the first is an if-elif chain
# and the second is a simple if. The merge_block of the first if-elif chain's
# last BoolOp is the entry block of the second if-statement.
#
# When _if_generate_elif_chain marks the merge_block as generated_blocks,
# the second IfRegion is skipped in the top-level loop because its entry
# is already in generated_blocks.
#
# Original code pattern:
#   if cond1:
#       ...
#   elif cond2:
#       ...
#   if fields is not None:   # <-- this IfRegion's entry = merge_block of first if-elif
#       fields = eval(fields)
#       fields = ','.join(fields)
#       params['fields'] = fields

def repro_01_elif_merge_block_is_next_if_entry():
    x = 1
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    if x is not None:
        y = 30
    return y


def repro_02_if_elif_then_if_chain():
    """Similar pattern: if-elif chain followed by if statement"""
    a = 5
    if a > 10:
        b = 1
    elif a > 5:
        b = 2
    else:
        b = 3
    if a is not None:
        b = 4
    return b


def repro_03_boolop_elif_merge_skips_next_if():
    """BoolOp elif with merge block = next if entry"""
    x = 1
    y = 2
    if x == 1 and y == 2:
        z = 10
    elif x == 3:
        z = 20
    if z is not None:
        z = 30
    return z


def repro_04_multiple_elif_then_if():
    """Multiple elif branches then a separate if"""
    val = 3
    if val == 1:
        result = 'a'
    elif val == 2:
        result = 'b'
    elif val == 3:
        result = 'c'
    else:
        result = 'd'
    if result is not None:
        result = result.upper()
    return result


def repro_05_elif_chain_with_boolop_condition():
    """Elif chain with BoolOp conditions followed by if"""
    x = 1
    y = 2
    if x == 1 or x == 2:
        z = 10
    elif y == 2:
        z = 20
    if z is not None:
        z += 1
    return z


def repro_06_simple_if_then_if():
    """Simple if (no elif) followed by if - should not be affected"""
    x = 1
    if x == 1:
        y = 10
    if x is not None:
        y = 20
    return y


def repro_07_elif_with_complex_boolop():
    """Elif with complex BoolOp followed by if"""
    a = 1
    b = 2
    c = 3
    if a == 1 and b == 2:
        d = 10
    elif c == 3 or a == 4:
        d = 20
    else:
        d = 30
    if d is not None:
        d = 40
    return d


def repro_08_nested_if_in_elif_then_if():
    """Nested if in elif body, then separate if"""
    x = 1
    if x == 1:
        y = 10
    elif x == 2:
        if x > 0:
            y = 20
        else:
            y = 21
    else:
        y = 30
    if y is not None:
        y = 40
    return y


def repro_09_elif_chain_with_return_in_branches():
    """Elif chain with returns followed by if"""
    x = 1
    if x == 1:
        return 10
    elif x == 2:
        return 20
    if x is not None:
        return 30
    return 40


def repro_10_elif_then_if_with_assignment():
    """Elif chain followed by if with complex assignment"""
    x = 1
    params = {}
    if x == 1:
        params['a'] = 1
    elif x == 2:
        params['a'] = 2
    if x is not None:
        params['b'] = 3
    return params


def repro_11_elif_boolop_merge_is_for_loop_entry():
    """Elif chain where merge block is a for loop entry"""
    items = [1, 2, 3]
    x = 1
    if x == 1:
        result = []
    elif x == 2:
        result = []
    else:
        result = []
    for item in items:
        result.append(item)
    return result


def repro_12_elif_chain_then_while_loop():
    """Elif chain followed by while loop"""
    x = 1
    y = 0
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    while y > 0:
        y -= 1
    return y
