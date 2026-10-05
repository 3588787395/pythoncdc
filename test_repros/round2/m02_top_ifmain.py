"""m02: top-level if-main with deep body."""
import sys


def _run(n):
    total = 0
    for i in range(n):
        try:
            if i % 2:
                total += i
            else:
                total -= i
        finally:
            total = total
    return total


def _main(argv):
    with (open(argv[0]) if argv else sys.stdin) as fh:
        data = fh
    return data if data else None


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for k in range(3):
            while k:
                try:
                    _run(k)
                except ValueError:
                    break
                finally:
                    k -= 1
    else:
        _main([])
