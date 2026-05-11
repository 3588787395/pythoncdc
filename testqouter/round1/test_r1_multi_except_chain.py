def test():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        return 1
    except ValueError:
        return 2
    except:
        return 3
    return 0
