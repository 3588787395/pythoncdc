# Source Generated with Decompyle++ (Python version)
# File: repro_04_with_statement_in_try_except.cpython-311.pyc (Python 3.11)

def example(path, mode):
    try:
        if os.path.exists(path):
            with open(path, mode) as fp:
                data = fp.read()
            if data:
                return data
    except Exception:
        print('error')
    return None
