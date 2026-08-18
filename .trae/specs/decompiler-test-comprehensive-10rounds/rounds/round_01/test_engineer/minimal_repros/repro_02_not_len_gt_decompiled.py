# Source Generated with Decompyle++ (Python version)
# File: repro_02_not_len_gt.pyc (Python 3.11)

__doc__ = '复现02: elif not len(item) > 50 条件取反逻辑错误'
def check_str(item):
    if len(item) == 0:
        return True
    elif not len(item) > 50:
        return False
