def main():
    data = [3, 3 + 1, 3 + 2, 3 + 3]
    first, *middle, last = data
    def call(a, b, c):
        return a + b + c
    return first, middle, last, call(*data[:3]), {**{"k": last}}
