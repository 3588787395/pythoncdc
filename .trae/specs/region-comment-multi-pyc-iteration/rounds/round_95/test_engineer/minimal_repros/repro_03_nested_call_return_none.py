# repro_03: nested call + return None (like np_tp_pd pattern)
def f(data):
    pd.DataFrame(data)
    return None
