def f(sequences):
    result = []
    while True:
        sequences = [s for s in sequences if s]
        if not sequences:
            return result
        for s1 in sequences:
            candidate = s1[0]
            for s2 in sequences:
                if candidate in s2[1:]:
                    candidate = None
                    break
            else:
                break
        if candidate is None:
            raise RuntimeError('Inconsistent hierarchy')
        result.append(candidate)
        for seq in sequences:
            if seq and seq[0] is candidate:
                del seq[0]
