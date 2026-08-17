# R96 repro 08: return dict value
def repro_08(data, key):
    if key in data:
        return data[key]
    return None
