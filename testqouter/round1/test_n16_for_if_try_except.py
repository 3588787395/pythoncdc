def test():
    result = []
    for i in range(3):
        if i > 0:
            try:
                x = 10 // i
                result.append(x)
            except:
                result.append(-1)
        else:
            result.append(0)
    return result
