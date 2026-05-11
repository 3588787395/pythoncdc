def test():
    result = 0
    try:
        x = 1
    except ValueError:
        result = 1
    else:
        result = 2
    finally:
        result += 10
    return result
