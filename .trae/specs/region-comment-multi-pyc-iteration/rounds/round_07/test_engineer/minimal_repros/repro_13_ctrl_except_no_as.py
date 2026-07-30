# NO-DEFECT 控制：except 无 as 绑定（v6 不触发 body-drop）
def f(x):
    try:
        result = x + 1
    except ValueError:
        return 'error'
    return result
# NO-DEFECT
