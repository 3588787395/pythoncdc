# Source Generated with Decompyle++ (Python version)
# File: er2_plainguard.pyc (Python 3.11)

def f(sequences):
    result = []
    if not sequences:
        return result
    else:
        for s1 in sequences:
            candidate = s1[0]
            result.append(candidate)
        return result
