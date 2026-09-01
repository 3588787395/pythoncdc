# 嵌套 try + 参数解包
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 嵌套 try + 参数解包
#
def nested_try_unpack(x):
    try:
        a, b = split(x)
        try:
            return compute(a, b)
        except:
            return (a, None)
    except:
        return (None, None)

