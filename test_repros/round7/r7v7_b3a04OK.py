# Source Generated with Decompyle++ (Python version)
# File: r7v7_b3a04.pyc (Python 3.11)

class B3A04:
    def b3a04_shallow(self, xs, flag):
        total = 0
        for x in xs:
            if x:
                total += x
            total += 1
        return total
    def b3a04_deep(self, xs, flag):
        total = 0
        for x in xs:
            if flag and x:
                if x > 5:
                    total += 5
                total += x
            total += 1
        return total
