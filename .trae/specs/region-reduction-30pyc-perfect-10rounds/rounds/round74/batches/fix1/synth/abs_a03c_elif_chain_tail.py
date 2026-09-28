# synth a03c -- elif chain shared tail holding a trailing statement.
def synth_a03c_elif_chain_tail(flag, value, a, b, c):
    if flag == 1:
        data = 1
    elif flag == -1:
        data = -1
    else:
        data = 0
    his_data = load_his(value, a, b, c, data)
    return his_data


def load_his(value, a, b, c, data):
    return (value, a, b, c, data)
