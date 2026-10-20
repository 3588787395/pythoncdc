import sys

path = sys.argv[1]
pat = sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
end = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9
with open(path, encoding='utf-8', errors='replace') as f:
    lines = f.read().splitlines()
for i, line in enumerate(lines, 1):
    if start <= i <= end and pat in line:
        print(i, line)
