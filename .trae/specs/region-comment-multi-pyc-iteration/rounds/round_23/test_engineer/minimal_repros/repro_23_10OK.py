# Source Generated with Decompyle++ (Python version)
# File: repro_23_10.cpython-311.pyc (Python 3.11)

def try_in_while(data, n):
    i = 0
    result = []
    while i < n:
        try:
            result.append(data[i])
        except IndexError:
            result.append(None)
        else:
            i += 1
            i < n
            return result
