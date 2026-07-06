def test():
    result = 0
    for i in range(3):
        if i > 0:
            for j in range(5):
                if j > 2:
                    break
                result += j
    return result
