# R97 repro 06: multiple returns with code after
def repro_06(data):
    if not data:
        return {}
    result = {}
    for k, v in data.items():
        result[k] = v
    return result
