def jump_forward_backward_mismatch(data, threshold):
    if data is None:
        return 0
    elif len(data) > threshold:
        return len(data)
    result = sum(data)
    return result
