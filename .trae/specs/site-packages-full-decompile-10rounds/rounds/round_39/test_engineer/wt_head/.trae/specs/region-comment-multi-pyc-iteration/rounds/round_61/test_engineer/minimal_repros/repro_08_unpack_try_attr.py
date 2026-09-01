# 解包 + try + 属性访问
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 解包 + try + 属性访问
#
def unpack_try_attr(obj, params):
    a, b = params
    try:
        result = method(a, b)
        return obj.attr if result else None
    except:
        return None

