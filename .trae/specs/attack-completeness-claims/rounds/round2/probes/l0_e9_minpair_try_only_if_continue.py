"""AT-02/AT-04 最小对 A: try 体只有 if+continue（无后续语句）"""


def e9(items, g):
    for x in items:
        try:
            if x:
                continue
        finally:
            g(0)
