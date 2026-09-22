def nc_a_prologue_emitted(index):
    l = len(index)
    while l > 0:
        l = l - 1
    return l


def nc_b_empty_body_while(flag):
    while flag:
        pass
    return 0


def nc_c_for_preheader(items):
    total = 0
    for it in items:
        total = total + it
    return total


def nc_d_guard_chain_falls_through(index, key):
    l = len(index)
    if l == 0:
        return 0
    if index[0] > key:
        return 0
    return l


def nc_e_one_guard_then_while(index, key):
    if len(index) == 0:
        return 0
    end = len(index) - 1
    while end > 0:
        end = end - 1
    return end


def nc_f_two_guards_then_while(index, key):
    l = len(index)
    if l == 0:
        return 0
    end = l - 1
    if index[0] > key:
        return 0
    while end > 0:
        end = end - 1
    return end
