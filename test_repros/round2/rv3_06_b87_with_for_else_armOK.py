# Source Generated with Decompyle++ (Python version)
# File: rv3_06_b87_with_for_else_arm.pyc (Python 3.11)

def outer(flag):
    acc = []
    try:
        with open(__file__, 'r') as fh:
            for line in fh:
                if len(acc) < 2:
                    if flag:
                        acc.append(line[0])
                    else:
                        acc.append('-')
                else:
                    acc.append('else-taken')
                    break
    except OSError:
        acc.append('oserror')
        for k in range(2):
            try:
                acc.append(str(k))
            except ValueError:
                acc.append('bad')
    else:
        acc.append('try-else')
    return acc
