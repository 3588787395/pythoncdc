# Source Generated with Decompyle++ (Python version)
# File: repro_06_with_then_if_attr_compare.pyc (Python 3.11)

def f(p, obj):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if obj.flag is not None:
        x = content + '_' + obj.flag
    return x
