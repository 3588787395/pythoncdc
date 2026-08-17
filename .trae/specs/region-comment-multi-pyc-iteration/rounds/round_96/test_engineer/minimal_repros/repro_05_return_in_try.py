# R96 repro 05: return in try-except
def repro_05(data):
    try:
        return data[0]
    except IndexError:
        return None
