# Source Generated with Decompyle++ (Python version)
# File: repro_r26_08_if_continue_nested_for.pyc (Python 3.11)

def f(data, out):
    for i in data:
        for key, value in i.items():
            if key == 'skip':
                continue
            elif key == 'a':
                continue
            elif isinstance(value, dict):
                out.update(value)
                continue
            else:
                out[key] = value
                continue
        out.append(1)
