# R101-Pattern-A-control: same shape WITHOUT try (does try trigger it?)


def pick(a, b):
    if a > 0:
        b = b + 1
    else:
        b = b - 1
    return True


def call(a, b):
    return pick(a, b)
