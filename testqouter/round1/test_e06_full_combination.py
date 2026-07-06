def test():
    result = []
    try:
        result.append(1)
    except:
        result.append(2)
    else:
        result.append(3)
    finally:
        result.append(4)
    return result
