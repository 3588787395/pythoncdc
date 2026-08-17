# R97 repro 04: statement order shift in for body
def repro_04(items):
    result = []
    for item in items:
        result.append(item)
    return result
