# Source Generated with Decompyle++ (Python version)
# File: r7v7_b2a03.pyc (Python 3.11)

class B2A03:
    def b2a03_shallow(self, xs, flag):
        acc = 0
        for x in xs:
            if x < 0 and flag:
                continue
            acc += x
            continue
        return acc
    def b2a03_deep(self, xs, flag):
        acc = 0
        for x in xs:
            if flag:
                if x != 0:
                    if x < 0:
                        continue
                    acc += x
                    continue
                    continue
                acc -= 1
        return acc
