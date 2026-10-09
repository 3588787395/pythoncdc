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

SPEC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SPEC_DIR, '..', '..', '..'))
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
    """Resolve a unit. Accepts the judge's dotted qualname (`<module>.Strategy.tick_worker_thread`)
    and a bare co_name. A bare name that matches several code objects is reported AMBIG rather
    than silently paired, because the judge pairs by full qualname."""
    if "." in name:
        mods = [c for c in codes if c.co_name == "<module>"]
        if not mods:
            raise SystemExit("no <module> code object")
        node = mods[0]
        segs = name.split(".")[1:] if name.startswith("<module>.") else name.split(".")
        for seg in segs:
            nxt = [x for x in node.co_consts if isinstance(x, type(node)) and x.co_name == seg]
            if not nxt:
                raise SystemExit("qualname segment %r not found under %r" % (seg, node.co_name))
            node = max(nxt, key=lambda k: len(k.co_code))
        return node
    c = [x for x in codes if x.co_name == name]
    if not c:
        raise SystemExit("unit %r not found (have %s)" % (
            name, sorted({x.co_name for x in codes})[:40]))
    if len(c) > 1:
        print("AMBIG_NAMES=%d co_code_lens=%s (paired the largest; pass the dotted qualname)" % (
            len(c), sorted(len(x.co_code) for x in c)))
    return max(c, key=lambda k: len(k.co_code))


def dump_raw(co):
    """(offset, opname, resolved jump target as an INSTRUCTION INDEX) under the same DROP filter as
    dump(), so it aligns 1:1 with dump()'s blanked keys. dump() blanks jump operands by design, which
    makes a landing-only residual read `hunks=0` — the judge (pylingual compare_pyc: CFG equivalence
    then bytecode) still fails it. The landing column lives here, not in dump().

    The target is an index into this code object's own filtered instruction list, not a raw byte
    offset: one content diff early in a unit shifts every later offset by 2 bytes, and comparing
    offsets then invents ~100 false landing diffs (measured: handlers._target reported 127 "landings"
    where the real difference is 1 content hunk). Index space is shift-invariant."""
    import bisect
    ins = [i for i in dis.get_instructions(co) if i.opname not in DROP]
    offs = [i.offset for i in ins]
    pos = {o: k for k, o in enumerate(offs)}

    def to_idx(target):
        if target in pos:
            return pos[target]
        k = bisect.bisect_left(offs, target)
        return k if k < len(offs) else len(offs)

    out = []
    for i in ins:
        tgt = to_idx(i.argval) if i.opname in JR and isinstance(i.argval, int) else None
        out.append((i.offset, i.opname, tgt))
    return out


def main(pyc, unit, prod):
    orig = marshal.loads(open(pyc, "rb").read()[16:])
    comp = compile(open(prod, encoding="utf-8-sig").read(), "<p>", "exec")
    o, p = [], []
    gather(orig, o); gather(comp, p)
    co, cp = pick(o, unit), pick(p, unit)
    ol, pl = dump(co), dump(cp)
    ro, rp = dump_raw(co), dump_raw(cp)
    ok = [x.split(None, 1)[1].strip() for x in ol]
    pk = [x.split(None, 1)[1].strip() for x in pl]
    print("len orig=%d prod=%d delta=%d" % (len(ol), len(pl), len(pl) - len(ol)))
    sm = difflib.SequenceMatcher(None, ok, pk, autojunk=False)
    n = 0
    eq = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            eq.extend(zip(range(i1, i2), range(j1, j2)))
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
    # A landing diff is real only when the two sides' targets are *different instructions under the
    # alignment*, not merely different indices: a content diff earlier in the unit moves every later
    # target by the same amount in both index space and byte space, and comparing raw indices then
    # invents diffs (measured: handlers._target 127, klinedata 76, quote.check_frequency 24 all with
    # exactly one real change each). Map orig target -> prod target through the matched blocks.
    a2b = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            a2b[blk.a + k] = blk.b + k
    land = []
    for i, j in eq:
        ta, tb = ro[i][2], rp[j][2]
        if ta is None or tb is None:
            continue
        if a2b.get(ta, -1) != tb:
            land.append((i, j, ta, tb))
    for i, j, ta, tb in land[:16]:
        print("   ~ orig[%d] @%-6d %-26s ->idx%-6s | prod[%d] @%-6d %-26s ->idx%-6s" % (
            i, ro[i][0], ro[i][1], ta, j, rp[j][0], rp[j][1], tb))
    if len(land) > 16:
        print("   ~ ... %d further landing diffs" % (len(land) - 16))
    print("hunks=%d landings=%d judge_diff=%s" % (n, len(land), bool(n or land)))


if __name__ == "__main__":
    a = sys.argv[1]
    pyc = a if os.path.isabs(a) else os.path.join(ROOT, "site-packages", a)
    prod = None
    if "--prod" in sys.argv:
        prod = sys.argv[sys.argv.index("--prod") + 1]
    if prod is None:
        prod = pyc[:-4] + "OK.py"
    main(pyc, sys.argv[2], prod)
