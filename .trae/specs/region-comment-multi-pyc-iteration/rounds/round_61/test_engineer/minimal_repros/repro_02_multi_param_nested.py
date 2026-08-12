# 多参数嵌套 try
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 多参数嵌套 try
#
def multi_param_nested_try(x, y, z, w):
    try:
        r1 = op1(x, y)
        r2 = op2(z, w)
        return (r1, r2)
    except ValueError:
        return (0, 0)

