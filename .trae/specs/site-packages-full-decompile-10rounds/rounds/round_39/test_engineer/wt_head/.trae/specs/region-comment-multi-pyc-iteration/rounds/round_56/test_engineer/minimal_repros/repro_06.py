def repro_06():
    try:
        for i in range(10):
            try:
                x = 1
            except:
                pass
        return x
    except Exception as e:
        return None
