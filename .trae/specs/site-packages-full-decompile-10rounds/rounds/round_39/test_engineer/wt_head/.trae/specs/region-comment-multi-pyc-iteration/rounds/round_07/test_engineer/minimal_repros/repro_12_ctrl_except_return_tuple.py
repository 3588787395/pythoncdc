# NO-DEFECT 控制：except-as return tuple（v2/v5 不触发 body-drop）
def f(x):
    try:
        result = x + 1
    except ValueError as e:
        return (-1, str(e))
    return result
# NO-DEFECT
