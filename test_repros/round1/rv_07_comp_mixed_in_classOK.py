# Source Generated with Decompyle++ (Python version)
# File: rv_07_comp_mixed_in_class.pyc (Python 3.11)

class RV07:
    def pick(self, vals, a, b, c):
        picked = [v for v in vals if a and b or c]
        return len(picked)
