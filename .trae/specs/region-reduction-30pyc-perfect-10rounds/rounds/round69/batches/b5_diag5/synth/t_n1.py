def f(stop):
    while True:
        while not stop:
            from os.path import exists
            if exists:
                break
            time.sleep(0.01)
        break
