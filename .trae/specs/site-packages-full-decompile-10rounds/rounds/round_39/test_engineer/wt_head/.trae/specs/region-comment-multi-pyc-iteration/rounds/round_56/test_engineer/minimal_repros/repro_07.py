def repro_07():
    for i in range(10):
        try:
            if i == 5:
                break
            x = 1
        except:
            pass
    else:
        return None
