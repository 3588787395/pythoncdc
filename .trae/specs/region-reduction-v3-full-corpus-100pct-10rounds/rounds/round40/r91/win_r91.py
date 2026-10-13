"""Print every aligned diff window of one unit: original pyc code object vs a regenerated product.

usage: python -X utf8 win_r91.py <pyc-abs> <unit> <prod>
"""
import difflib
import dis
import marshal
import sys

pyc, unit, prod = sys.argv[1], sys.argv[2], sys.argv[3]
code = marshal.loads(open(pyc, "rb").read()[16:])


def find(c, name, path=""):
    for const in c.co_consts:
        if hasattr(const, "co_code"):
            full = (path + "." if path else "") + const.co_name
            if const.co_name == name:
                return const
            got = find(const, name, full)
            if got is not None:
                return got
    return None


def find_in_compiled(node, name):
    for const in node.co_consts:
        if hasattr(const, "co_code"):
            if const.co_name == name:
                return const
            got = find_in_compiled(const, name)
            if got is not None:
                return got
    return None


tgt = find(code, unit)
comp = compile(open(prod, encoding="utf-8-sig").read(), "<p>", "exec")
cp = find_in_compiled(comp, unit)
oi = [(i.offset, i.opname, i.argrepr) for i in dis.get_instructions(tgt)]
pi = [(i.offset, i.opname, i.argrepr) for i in dis.get_instructions(cp)]
ok = [o[1] for o in oi]   # align on opcode name only; jump operands reported separately
pk = [o[1] for o in pi]
print("orig instrs=%d prod instrs=%d delta=%d" % (len(ok), len(pk), len(pk) - len(ok)))
sm = difflib.SequenceMatcher(None, ok, pk, autojunk=False)
n = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    n += 1
    print("\n== #%d %s orig[@%d..@%d] prod[@%d..@%d] del=%d ins=%d" % (
        n, tag, oi[i1][0], oi[i2 - 1][0], pi[j1][0] if j2 else -1, oi[min(i2, len(oi) - 1)][0], i2 - i1, j2 - j1))
    for k in range(i1, i2):
        print("   - @%-6d %-34s line? %s" % (oi[k][0], ok[k], ""))
    for k in range(j1, j2):
        print("   + @%-6d %-34s" % (pi[k][0], pk[k]))
print("\nwindows=%d" % n)
