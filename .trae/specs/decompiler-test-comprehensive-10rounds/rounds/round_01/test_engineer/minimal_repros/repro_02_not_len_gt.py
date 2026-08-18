"""复现02: elif not len(item) > 50 条件取反逻辑错误"""
def check_str(item):
    if len(item) == 0:
        return True
    elif not len(item) > 50:
        return False
    return None
