# Source Generated with Decompyle++ (Python version)
# File: repro_02_with_open_encoding_write.pyc (Python 3.11)

def write_text(path, s):
    with open(path, 'w', encoding='gbk') as f:
        f.write(s)
    return len(s)
