import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def extract(path, name):
    lines = io.open(path, encoding="utf-8").read().split("\n")
    start = None
    for i, l in enumerate(lines):
        if re.match(r"\s*def %s\(" % re.escape(name), l):
            start = i
            break
    if start is None:
        return None
    indent = len(lines[start]) - len(lines[start].lstrip())
    out = [lines[start]]
    for l in lines[start + 1:]:
        if l.strip() and (len(l) - len(l.lstrip())) <= indent and not l.lstrip().startswith("#") \
                and not l.lstrip().startswith(")"):
            break
        out.append(l)
    return out


a = sys.argv[1]
b = sys.argv[2]
names = sys.argv[3:]
for n in names:
    A = extract(a, n)
    B = extract(b, n)
    print("=" * 20, n, "A_lines", None if A is None else len(A),
          "B_lines", None if B is None else len(B))
    if A is None or B is None:
        continue
    import difflib
    d = list(difflib.unified_diff(A, B, "A", "B", lineterm="", n=3))
    if not d:
        print("  IDENTICAL")
    else:
        for l in d:
            print(l)
