def n8p02(a):
    try:
        with CM(a):
            g(a)
            return None
    except Exception as e:
        h(e)
