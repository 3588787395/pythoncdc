# Source Generated with Decompyle++ (Python version)
# File: repro_01_with_open_encoding.pyc (Python 3.11)

def read_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
