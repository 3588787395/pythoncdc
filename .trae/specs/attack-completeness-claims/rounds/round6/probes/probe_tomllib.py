def main():
    try:
        print(loads('a = 1\nb = "x"'))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
