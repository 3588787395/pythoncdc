def f(sequences):
    result = []
    if not sequences:
        return result
    for s1 in sequences:
        candidate = s1[0]
        result.append(candidate)
    return result
