def case_or_tail_operand_reused(user_memory, max_memory_size):
    if user_memory is None:
        return -1
    elif 'GB' in user_memory or 'GiB' in user_memory:
        if float(max_memory_size) <= float(user_memory.replace('GB', '').replace('GiB', '')):
            return 1
    return 0


def control_real_and_chain_in_elif_body(user_memory, max_memory_size):
    if user_memory is None:
        return -1
    elif 'GB' in user_memory:
        if 'GiB' in user_memory and float(max_memory_size) > 0.0:
            return 1
    return 0


def control_or_chain_with_if_else(user_memory, max_memory_size):
    if user_memory is None:
        return -1
    elif 'GB' in user_memory or 'GiB' in user_memory:
        if float(max_memory_size) > 0.0:
            return 1
        else:
            return 2
    return 0
