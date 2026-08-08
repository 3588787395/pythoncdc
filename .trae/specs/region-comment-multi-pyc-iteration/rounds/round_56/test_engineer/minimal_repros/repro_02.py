def repro_02():
    for f in [1, 2, 3]:
        for i in range(10):
            try:
                x = f * i
            except:
                pass
    else:
        return None
