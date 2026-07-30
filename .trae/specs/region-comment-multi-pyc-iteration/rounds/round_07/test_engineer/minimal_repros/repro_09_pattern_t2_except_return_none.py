# DEFECT-REPRO Pattern T2: except-as return None 常量，handler body 被丢弃
def f(x):
    try:
        result = x.strip()
    except AttributeError as e:
        return None
    return result
# DEFECT-REPRO
