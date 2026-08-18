# Source Generated with Decompyle++ (Python version)
# File: repro_04_if_not_isinstance.pyc (Python 3.11)

__doc__ = '复现04: if not isinstance(item, str) 被错误反编译为 if isinstance(item, str): pass else:'
def convert_item(item):
    if isinstance(item, str):
        pass
    else:
        converted = item
    return converted
