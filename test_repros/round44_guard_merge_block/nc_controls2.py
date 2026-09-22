def nc_g_while_and_chain(a, b):
    while a and b:
        a = 0
    return b


def nc_h_while_or_chain(a, b):
    while a > 0 or b > 0:
        b = 0
    return a


def nc_i_guard_then_while_and_chain(data, done):
    n = len(data)
    while not done and n > 0:
        n = n - 1
    return n


def nc_j_three_guards_then_while(index, key):
    l = len(index)
    if l == 0:
        return 0
    if index[0] > key:
        return 0
    if key > index[l - 1]:
        return l
    end = l - 1
    while end > 0:
        end = end - 1
    return end


def nc_k_guard_then_for(index, key):
    l = len(index)
    if l == 0:
        return 0
    if index[0] > key:
        return 0
    total = 0
    for i in index:
        total = total + i
    return total


def nc_l_guard_then_while_true(index, key):
    l = len(index)
    if l == 0:
        return 0
    if index[0] > key:
        return 0
    n = l
    while True:
        if n <= 0:
            break
        n = n - 1
    return n
