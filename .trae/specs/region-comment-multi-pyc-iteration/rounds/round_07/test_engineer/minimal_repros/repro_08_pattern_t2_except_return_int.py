# DEFECT-REPRO Pattern T2: except-as return int 常量，handler body 被丢弃
def f(x):
    try:
        result = x * 2
    except TypeError as e:
        return 42
    return result
# DEFECT-REPRO
