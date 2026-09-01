# Source Generated with Decompyle++ (Python version)
# File: repro_23_14.cpython-311.pyc (Python 3.11)

def if_return_elif(x, data):
    if len(data) == 0:
        return None
    elif x > 0:
        return data[0]
    elif x < 0:
        return data[-1]
    else:
        return data
