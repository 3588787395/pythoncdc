"""Per-unit instruction diff measurement tool (NOT a register).

The campaign's residual roster stays owned by residual_report.py; this tool only
measures one unit of one pyc against a product, with two distinct columns:
  content  = opcode+argrepr with jump operands blanked
  landing  = jump operand differences on the aligned equal-runs
Blanking uses {dis.opname[o] for o in list(dis.hasjrel)+list(dis.hasjabs)} because
dis.hasjrel/hasjabs are lists of OPCODE NUMBERS, not names — comparing opname
strings against them silently disables the split and mislabels every landing-only
unit as a content loss (found 2026-10-09; it had mis-shaped the residual census).

usage: python -X utf8 unit_diff.py <pyc-rel-or-abs> <unit-co-name> [--prod PATH] [--all]
  --all keeps small hunks too (default hides pure-length shifts under 3)
"""
import dis, difflib, marshal, os, re, sys, types

ROOT = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
DROP = ("NOP", "CACHE", "EXTENDED_ARG")
JR = {dis.opname[o] for o in (list(dis.hasjrel) + list(dis.hasjabs))
      if isinstance(o, int)}
CO_RE = re.compile(r"<code object ([^,]+) at 0x[0-9a-fA-F]+, file .*?line (\d+)>")


def dump(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname in DROP:
            continue
        arg = i.argrepr or ""
        m = CO_RE.match(arg)
        if m:
            arg = "<co %s>" % m.group(1)
        if i.opname in JR:
            arg = ""
        out.append("@%-7d %-30s %s" % (i.offset, i.opname, arg))
    return out


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            gather(cst, acc)


def pick(codes, name):
    c = [x for x in codes if x.co_name == name]
    if not c:
        raise SystemExit("unit %r not found (have %s)" % (
            name, sorted({x.co_name for x in codes})[:40]))
    return max(c, key=lambda k: len(k.co_code))


def main(pyc, unit, prod):
    orig = marshal.loads(open(pyc, "rb").read()[16:])
    comp = compile(open(prod, encoding="utf-8-sig").read(), "<p>", "exec")
    o, p = [], []
    gather(orig, o); gather(comp, p)
    ol, pl = dump(pick(o, unit)), dump(pick(p, unit))
    ok = [x.split(None, 1)[1].strip() for x in ol]
    pk = [x.split(None, 1)[1].strip() for x in pl]
    print("len orig=%d prod=%d delta=%d" % (len(ol), len(pl), len(pl) - len(ol)))
    sm = difflib.SequenceMatcher(None, ok, pk, autojunk=False)
    n = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        n += 1
        if min(i2 - i1, j2 - j1) == 0 and max(i2 - i1, j2 - j1) < 3:
            continue
        print("== %s orig[%d..%d @%s..@%s] prod[%d..%d] del=%d ins=%d" % (
            tag, i1, i2, ol[i1].split()[0] if i1 < len(ol) else "-",
            ol[i2 - 1].split()[0] if i2 > i1 else "-",
            j1, j2, i2 - i1, j2 - j1))
        for x in ol[i1:i2][:16]:
            print("   - " + x)
        for x in pl[j1:j2][:16]:
            print("   + " + x)
    print("hunks=%d" % n)


if __name__ == "__main__":
    a = sys.argv[1]
    pyc = a if os.path.isabs(a) else os.path.join(ROOT, "site-packages", a)
    prod = None
    if "--prod" in sys.argv:
        prod = sys.argv[sys.argv.index("--prod") + 1]
    if prod is None:
        prod = pyc[:-4] + "OK.py"
    main(pyc, sys.argv[2], prod)
