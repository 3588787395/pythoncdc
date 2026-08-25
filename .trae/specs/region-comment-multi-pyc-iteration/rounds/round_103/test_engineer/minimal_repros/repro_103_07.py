def multi_branch_elif_with_jump(x):
    if x == '1w':
        return 'weekly'
    elif x == 'mo':
        return 'monthly'
    elif x == '1y':
        return 'yearly'
    elif x == '1q':
        return 'quarterly'
    return 'unknown'
