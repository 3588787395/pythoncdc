# DEFECT-REPRO Pattern T2: except-as return 简单常量，handler body 被丢弃（无 with 前置）
def f(x):
    try:
        result = x + 1
    except ValueError as e:
        return 'error'
    return result
# DEFECT-REPRO
