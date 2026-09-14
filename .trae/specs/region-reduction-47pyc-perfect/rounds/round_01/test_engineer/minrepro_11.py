def for_loop_with_if_continue_no_else(items):
    output = []
    for item in items:
        if not item:
            continue
        output.append(item)
    return output
