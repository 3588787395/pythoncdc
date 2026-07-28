# Source Generated with Decompyle++ (Python version)
# File: repro_10_for_else_continue_then_append.pyc (Python 3.11)

def f(items, data_out):
    for i in items:
        for key, value in i.items():
            if not key == 'skip':
                match key:
                    case 'a':
                        continue
                    case _:
                        continue
        data_out.append(1)
