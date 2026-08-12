# 参数解包 + try-except
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: 参数解包 + try-except
#
def func_with_args_and_try(a, b, c):
    try:
        result = process(a, b)
        return result
    except Exception as e:
        log(e)
        return None

