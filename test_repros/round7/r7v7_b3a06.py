def b3a06_shallow(xs, flag, sink):
    for x in xs:
        if x > 0:
            sink.append(x)
        sink.append(0)
    return len(sink)


def b3a06_deep(xs, flag, sink):
    for x in xs:
        if flag:
            if x > 0:
                if x % 3 == 0:
                    sink.append(x)
                else:
                    sink.append(-x)
            sink.append(0)
    return len(sink)
