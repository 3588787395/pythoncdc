# Source Generated with Decompyle++ (Python version)
# File: repro_04_with_open_errors_encoding.pyc (Python 3.11)

def read_ignore(path):
    with open(path, 'r', errors='ignore', encoding='utf-8') as f:
        return f.read()
        return None
