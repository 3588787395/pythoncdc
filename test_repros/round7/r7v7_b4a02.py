def b4a02_shallow(xs, flag):
    acc = 0
    try:
        for x in xs:
            try:
                acc += x
            finally:
                acc += 1
    finally:
        acc += 2
    return acc


def b4a02_deep(xs, flag):
    acc = 0
    if flag:
        try:
            for x in xs:
                if x > 0:
                    try:
                        if x > 10:
                            acc += 10
                        else:
                            acc += x
                    finally:
                        acc += 1
                else:
                    acc -= 1
        finally:
            acc += 2
    return acc
