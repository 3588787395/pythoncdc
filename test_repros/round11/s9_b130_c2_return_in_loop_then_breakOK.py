# Source Generated with Decompyle++ (Python version)
# File: s9_b130_c2_return_in_loop_then_break.pyc (Python 3.11)

def f10(count, reader, limit):
    while count <= limit:
        try:
            for items in reader:
                if len(items) > 0:
                    if items[0] == 1:
                        return items
                    else:
                        return items[2]
                else:
                    print('empty')
                    continue
        except BaseException:
            count += 1
        else:
            break
    return count
