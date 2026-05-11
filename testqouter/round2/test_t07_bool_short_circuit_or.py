def test():
    def side():
        return 2
    return False or side()
