# R97 repro 10: nested return with JUMP_FORWARD
def repro_10(data):
    for row in data:
        for cell in row:
            if cell is None:
                return None
    return data
