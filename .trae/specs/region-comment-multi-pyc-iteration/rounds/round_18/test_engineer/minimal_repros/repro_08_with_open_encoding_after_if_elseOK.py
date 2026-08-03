# Source Generated with Decompyle++ (Python version)
# File: repro_08_with_open_encoding_after_if_else.pyc (Python 3.11)

def read_after_else(path, a):
    if a:
        x = a
    else:
        return None
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
