# R96 repro 06: return in nested structure
def repro_06(data):
    for row in data:
        for cell in row:
            if cell is None:
                return cell
    return None
