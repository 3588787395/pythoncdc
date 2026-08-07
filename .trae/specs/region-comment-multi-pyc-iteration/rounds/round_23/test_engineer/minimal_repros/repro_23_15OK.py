# Source Generated with Decompyle++ (Python version)
# File: repro_23_15.cpython-311.pyc (Python 3.11)

def nested_for_cond(data, keys):
    result = {}
    for key in keys:
        if key in data:
            val = data[key]
            if isinstance(val, list):
                result[key] = val[0]
                continue
            result[key] = val
    return result
