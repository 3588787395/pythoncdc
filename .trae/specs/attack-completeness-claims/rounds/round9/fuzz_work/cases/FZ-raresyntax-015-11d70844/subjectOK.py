# Source Generated with Decompyle++ (Python version)
# File: subject.pyc (Python 3.11)

def main():
    data = [3, 4, 5, 6]
    first, *middle, last = data
    def call(a, b, c):
        return a + b + c
    return (first, middle, last, call(*data[:3]), {**{'k': last}})
