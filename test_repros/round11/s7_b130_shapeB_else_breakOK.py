# Source Generated with Decompyle++ (Python version)
# File: s7_b130_shapeB_else_break.pyc (Python 3.11)

def f7(count, reader, limit):
    while count <= limit:
        try:
            for items in reader:
                if len(items) > 0:
                    print(items)
                    continue
                print('empty')
                continue
        except BaseException:
            count += 1
        else:
            break
    return count
