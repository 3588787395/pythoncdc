# Source Generated with Decompyle++ (Python version)
# File: repro_23_08.pyc (Python 3.11)

def for_tuple_unpack(data):
    result = {}
    for key, value in data.items():
        if value > 0:
            result[key] = value
        continue
    return result
