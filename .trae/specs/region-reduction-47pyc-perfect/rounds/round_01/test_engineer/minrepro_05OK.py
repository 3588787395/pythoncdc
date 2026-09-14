# Source Generated with Decompyle++ (Python version)
# File: minrepro_05.pyc (Python 3.11)

def bare_except_with_return_in_body(path):
    try:
        f = open(path, 'r')
        data = f.read()
    except BaseException:
        return None
    return data
