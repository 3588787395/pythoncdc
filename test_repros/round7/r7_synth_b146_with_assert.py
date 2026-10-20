def s_b146_with_assert(path):
    with open(path) as fh:
        data = fh.read()
        assert data, "empty file"
    return data


def s_b146_with_assert2(path):
    with open(path) as fh:
        head = fh.readline()
        assert head
    return head
