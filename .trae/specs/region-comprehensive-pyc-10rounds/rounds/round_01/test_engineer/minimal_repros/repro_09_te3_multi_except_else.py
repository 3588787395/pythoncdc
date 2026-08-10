# try with multiple except + else
def test():
    try:
        value = int("abc")
    except ValueError:
        value = "value error"
    except TypeError:
        value = "type error"
    else:
        print("no error")
    return value
