# Source Generated with Decompyle++ (Python version)
# File: minrepro_11.pyc (Python 3.11)

def for_loop_with_if_continue_no_else(items):
    output = []
    for item in items:
        if not item:
            continue
        output.append(item)
    return output
