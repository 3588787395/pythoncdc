def repro_09():
    for i in range(10):
        try:
            x = 1
        except ValueError:
            pass
        except TypeError:
            pass
    else:
        return None
