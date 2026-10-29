# Source Generated with Decompyle++ (Python version)
# File: er1_c3merge.pyc (Python 3.11)

def f(sequences):
    result = []
    while True:
        sequences = [s for s in sequences if s]
        if sequences:
            for s1 in sequences:
                candidate = s1[0]
                for s2 in sequences:
                    if candidate in s2[1:]:
                        candidate = None
                        break
                else:
                    break
        else:
            return result
        if candidate is None:
            raise RuntimeError('Inconsistent hierarchy')
        result.append(candidate)
        for seq in sequences:
            if seq and seq[0] is candidate:
                del seq[0]
