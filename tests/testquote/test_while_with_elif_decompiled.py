# Source Generated with Decompyle++ (Python version)
# File: test_while_with_elif.pyc (Python 3.11)

def func(count, flag, redata):
    while count < 3:
        if flag == 1:
            count += 1
        elif flag == -1:
            count -= 1
        else:
            if redata:
                return redata
        count += 1
