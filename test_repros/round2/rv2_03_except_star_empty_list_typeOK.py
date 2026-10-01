# Source Generated with Decompyle++ (Python version)
# File: rv2_03_except_star_empty_list_type.pyc (Python 3.11)

def f(tag):
    out = [tag]
    try:
        tag = tag + 'x'
    except* []:
        out.append('empty-list-type')
    return out
