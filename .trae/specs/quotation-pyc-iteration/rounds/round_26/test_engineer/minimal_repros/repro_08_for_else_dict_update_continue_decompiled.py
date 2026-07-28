# Source Generated with Decompyle++ (Python version)
# File: repro_08_for_else_dict_update_continue.pyc (Python 3.11)

def f(items, dict1):
    for k, v in items.items():
        if not k == 'skip':
            if k == 'a':
                continue
            elif isinstance(v, dict):
                dict1.update(v)
                continue
            else:
                dict1[k] = v
                continue
        else:
            continue
    dict1['done'] = True
