# R97 repro 02: POP_TOP mislabeled as RETURN_VALUE
def repro_02(data):
    for item in data:
        print(item)
    return None
