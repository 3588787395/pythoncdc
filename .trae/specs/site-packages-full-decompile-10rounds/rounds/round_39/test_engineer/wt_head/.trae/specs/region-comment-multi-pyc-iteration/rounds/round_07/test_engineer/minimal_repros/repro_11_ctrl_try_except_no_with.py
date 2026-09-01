# NO-DEFECT 控制：try/except 无前置 with（Pattern T full-drop 不触发）
def f(x):
    try:
        result = x + 1
    except ValueError:
        result = -1
    return result
# NO-DEFECT
