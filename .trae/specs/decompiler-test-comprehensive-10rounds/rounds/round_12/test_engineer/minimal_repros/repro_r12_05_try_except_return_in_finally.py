# R12 MinRepro 05: try-except with return in finally

def risky(x):
    try:
        return 1 / x
    except ZeroDivisionError:
        return 0
    finally:
        print('done')
