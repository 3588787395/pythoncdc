# Source Generated with Decompyle++ (Python version)
# File: rv_06_while_mixed_in_class.pyc (Python 3.11)

class RV06:
    def run(self, a, b, c):
        n = 0
        while a and b or c:
            n += 1
            if n > 5:
                break
        return n
