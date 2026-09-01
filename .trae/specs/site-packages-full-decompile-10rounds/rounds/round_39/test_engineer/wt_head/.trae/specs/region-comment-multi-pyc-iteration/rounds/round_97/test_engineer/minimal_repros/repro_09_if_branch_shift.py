# R97 repro 09: if branch body shift
def repro_09(data, flag):
    if flag == 'a':
        data['a'] = 1
        return data
    elif flag == 'b':
        data['b'] = 2
        return data
    return None
