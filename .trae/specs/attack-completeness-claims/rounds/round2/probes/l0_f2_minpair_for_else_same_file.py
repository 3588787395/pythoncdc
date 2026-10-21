"""AT-04 同文件最小对：n1（for-else 被塌陷）与 n2（无 else）对照"""


def n1(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)


def n2(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)
        g(1)
