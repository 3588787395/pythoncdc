# try-except-else-finally
def test():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        result = "error"
    else:
        print("success")
    finally:
        print("cleanup")
    return result
