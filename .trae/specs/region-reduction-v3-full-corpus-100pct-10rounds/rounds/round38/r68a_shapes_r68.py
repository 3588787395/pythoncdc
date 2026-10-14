"""R68 shape harness v2 (read-only, re-runnable):  python -X utf8 shapes_r68.py

Question: does ANY Python source shape (same names/statements, different nesting)
compile to a code object reproducing the ORIGINAL _process_cancel_order target
pattern, i.e. simultaneously
    (1) arm-B exit JUMP_FORWARD @1710 -> @1822  (the pure continue block, orig operand 0x37)
    (2) arm-A exit @1606 and the `business_type` false-exit @944 -> @1826 (the merge)
    (3) explicit continues -> @44 (loop-entry NOP) and body tail @2042 -> @46 (header)

Method: patch the region inside the REAL trade_live_brokerOK.py module text and
compile the WHOLE module.  Whole-module compile is mandatory: a module-level
`import time` makes the compiler emit LOAD_ATTR instead of LOAD_METHOD for
`time.sleep(...)` (-12 bytes), so an extracted snippet is not byte-comparable.
"""
import dis
import marshal
import sys
import types

PYC = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
       r"IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc")
OK = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/"
      r"IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py")
CO_NAME = "_process_cancel_order"
NL = chr(10)
LOG = open(r"D:/Temp/r68/report.txt", "w", encoding="utf-8")


def say(*a):
    s = " ".join(str(x) for x in a)
    LOG.write(s + NL)
    print(s)


def collect(root):
    out, stack = [], [root]
    while stack:
        c = stack.pop()
        for x in c.co_consts:
            if isinstance(x, types.CodeType):
                if x.co_name == CO_NAME:
                    out.append(x)
                stack.append(x)
    return out


# ------------------------------------------------------------------- source --
MODULE = open(OK, encoding="utf-8").read()
LINES = MODULE.splitlines()
# 1-based 551..571: business_type if + error_no chain + except [+ continue] + else arm + sleep
OLD_BLOCK = NL.join(LINES[550:571])
assert OLD_BLOCK.startswith(" " * 24 + "if self.business_type in"), OLD_BLOCK[:70]

I12, I16, I20, I24, I28, I32, I36 = [" " * n for n in (12, 16, 20, 24, 28, 32, 36)]
A = NL.join(LINES[552:561])                        # arm A body (1-based 553..561, indent 32)
EXC = LINES[565] + NL + LINES[566]                 # except BaseException: + body
ELSE_HDR = LINES[568]                               # `                else:`
ELSE_BODY = LINES[569]                              # `                    strategy_log.error(...)`
SLEEP = LINES[570]                                  # `            time.sleep(0.001)`
TAIL = LINES[567]                                   # `                    continue`
BTYPE = LINES[550]
assert TAIL == I20 + "continue" and SLEEP.startswith(I12)

TB = ("error_dict.get('error_no') == T2SDK_RTNPACK_EMPTY and "
      "self.broker.trade_account.node_type == '7'")
ERRC = "strategy_log.error(_('后端服务 撤单失败，错误原因：%s' % error_dict.get('error_info')))"
HEAD = I28 + "if error_dict.get('error_no') == 0:"


def suite(kind):
    """suite of `if self.business_type in ('future', 'rzrq'):` (all lines indent >= 28)."""
    elifB, elseC = I28 + "elif " + TB + ":", I28 + "else:"
    errC, contC = I32 + ERRC, I32 + "continue"
    innerB, innerNB, elseI = I32 + "if " + TB + ":", I32 + "if not (" + TB + "):", I32 + "else:"
    if kind == "cur":                       # if / elif: pass / else: error()
        return NL.join([HEAD, A, elifB, I32 + "pass", elseC, errC])
    if kind == "C_cont":                    # ... else: error(); continue        (E1 cand.)
        return NL.join([HEAD, A, elifB, I32 + "pass", elseC, errC, contC])
    if kind == "B_cont":                    # arm B written as continue
        return NL.join([HEAD, A, elifB, contC, elseC, errC, contC])
    if kind == "chain_tail":                # continue after the whole chain (indent 28)
        return NL.join([HEAD, A, elifB, I32 + "pass", elseC, errC, I28 + "continue"])
    if kind == "nested":                    # else: (if B: pass else: error); continue
        return NL.join([HEAD, A, elseC, innerB, I36 + "pass", elseI, I36 + ERRC, contC])
    if kind == "nested_err":                # else: (if B: pass else: error; continue)
        return NL.join([HEAD, A, elseC, innerB, I36 + "pass", elseI, I36 + ERRC, I36 + "continue"])
    if kind == "nested_not":                # else: if not (B): error ; continue
        return NL.join([HEAD, A, elseC, innerNB, I36 + ERRC, contC])
    if kind == "nested_not_noerr":          # else: if not (B): error   (continue outside)
        return NL.join([HEAD, A, elseC, innerNB, I36 + ERRC])
    if kind == "elif_not":                  # elif not (B): error; continue
        return NL.join([HEAD, A, I28 + "elif not (" + TB + "):", errC, contC])
    if kind == "neg_first":                 # if != 0: (if not B: error); continue / else: A
        a2 = NL.join((I32 + l[len(I32):]) if l.startswith(I32) else I32 + l.strip()
                     for l in A.splitlines())
        return NL.join([I28 + "if error_dict.get('error_no') != 0:", innerNB,
                        I36 + ERRC, contC, elseC, a2])
    if kind == "nested_after_err":          # else: (if B: pass) ; error ; continue
        return NL.join([HEAD, A, elseC, innerB, I36 + "pass", errC, contC])
    if kind == "neg_nested":                # if != 0: (if B: pass else: err); cont / else: A
        a2 = NL.join((I32 + l[len(I32):]) if l.startswith(I32) else I32 + l.strip()
                     for l in A.splitlines())
        return NL.join([I28 + "if error_dict.get('error_no') != 0:", innerB, I36 + "pass",
                        elseI, I36 + ERRC, contC, elseC, a2])
    raise AssertionError(kind)


def build(kind, tail_mode, else_mode):
    parts = [BTYPE, suite(kind), EXC]
    if tail_mode == "after_try":
        parts.append(TAIL)
    elif tail_mode == "try_else":
        parts += [I20 + "else:", I24 + "continue"]
    elif tail_mode == "except_cont":
        parts[-1] = EXC + NL + I24 + "continue"
    elif tail_mode != "none":
        raise AssertionError(tail_mode)
    parts.append(ELSE_HDR)
    parts.append(ELSE_BODY)
    if else_mode == "err_cont":
        parts.append(I20 + "continue")
    elif else_mode != "err":
        raise AssertionError(else_mode)
    parts.append(SLEEP)
    assert OLD_BLOCK in MODULE
    return MODULE.replace(OLD_BLOCK, NL.join(parts), 1)


# ------------------------------------------------------------------ compare --
def jump_list(co):
    out = []
    for i in dis.get_instructions(co):
        if i.opname.startswith(("JUMP", "POP_JUMP", "FOR_ITER", "SEND", "BRANCH")):
            out.append((i.offset, i.opname, i.argval if isinstance(i.argval, int) else -1))
    return out


def decode(co, bytoff):
    want = bytoff - (bytoff % 2)
    for i in dis.get_instructions(co):
        if i.offset == want:
            return "@%d %s arg=%s -> @%s" % (i.offset, i.opname, i.arg,
                                             i.argval if isinstance(i.argval, int) else "?")
    return "@%d ?" % want


def pattern(co):
    """(armB target, tail target) using structure, not fixed offsets:
       tail = last JUMP_BACKWARD in the code; armB = the JUMP_FORWARD that immediately
       follows a POP_JUMP_FORWARD_IF_FALSE pair from the elif test.  Reported offsets
       are informational."""
    j = jump_list(co)
    backs = [t for o, op, t in j if op == "JUMP_BACKWARD"]
    tail = backs[-1] if backs else None
    arm_b = None
    for k, (o, op, t) in enumerate(j):
        if op == "JUMP_FORWARD" and k + 1 < len(j) and j[k + 1][1] == "JUMP_FORWARD":
            pass
    # arm-B jump = the JUMP_FORWARD emitted just before a continue block whose
    # block is entered by exactly the two predecessors (fall-through + this jump)
    return tail, j


def cmp_(name, co, orig):
    o, n = orig.co_code, co.co_code
    ndiff = sum(1 for a, b in zip(o, n) if a != b) + abs(len(o) - len(n))
    first = next((k for k in range(min(len(o), len(n))) if o[k] != n[k]), None)
    jx, jy = jump_list(orig), jump_list(co)
    jeq, exc = jx == jy, orig.co_exceptiontable == co.co_exceptiontable
    arm_b = next((t for off, op, t in jy if op == "JUMP_FORWARD" and off == 1710), None)
    tail = jump_list(co)[-1] if jy else None
    backs = [t for off, op, t in jy if op == "JUMP_BACKWARD"]
    tl = backs[-1] if backs else None          # body-tail back edge = last JUMP_BACKWARD
    tl_nop2 = backs[-2] if len(backs) > 1 else None
    say("%-27s len=%4d/%4d diffs=%-4d first=%-5s exc=%-2s jmp=%-2s armB@1710->@%-5s tail->@%-5s %s" % (
        name, len(o), len(n), ndiff, first, "EQ" if exc else "NE", "EQ" if jeq else "NE",
        arm_b, "%s(hdrtgt=%s)" % (tl, tl_nop2),
        "" if first is None else "|| orig[%d]=%02x prod[%d]=%02x : ORIG %s  PROD %s" % (
            first, o[first], first, n[first], decode(orig, first), decode(co, first))))
    return ndiff, not jeq, not exc, (first if first is not None else -1), name


SHAPES = [
    # label,                              chain kind,           tail mode,     else mode
    ("S00_current_OKpy",                   "cur",                "after_try",   "err"),
    ("S01_Ccont(E1 brief cand.)",          "C_cont",             "none",        "err"),
    ("S02_Ccont+else_cont",                "C_cont",             "none",        "err_cont"),
    ("S03_Ccont+tail+else_cont",           "C_cont",             "after_try",   "err_cont"),
    ("S04_chain_tail+else_cont",           "chain_tail",         "none",        "err_cont"),
    ("S05_nested+else_cont",               "nested",             "none",        "err_cont"),
    ("S06_nested_err+else_cont",           "nested_err",         "none",        "err_cont"),
    ("S07_nested_not+else_cont",           "nested_not",         "none",        "err_cont"),
    ("S08_nested+else_cont+tail",          "nested",             "after_try",   "err_cont"),
    ("S09_nested_not+else+tail",           "nested_not",         "after_try",   "err_cont"),
    ("S10_B_cont+else_cont",               "B_cont",             "none",        "err_cont"),
    ("S11_elif_not+else_cont",             "elif_not",           "none",        "err_cont"),
    ("S12_neg_first+else_cont",            "neg_first",          "none",        "err_cont"),
    ("S13_nested_no_cont+else_cont",       "nested_not_noerr",   "none",        "err_cont"),
    ("S14_nested+try_else",                "nested",             "try_else",    "err_cont"),
    ("S15_nested+except_cont",             "nested",             "except_cont", "err"),
    ("S16_Ccont+try_else",                 "C_cont",             "try_else",    "err_cont"),
    ("S17_Ccont+except_cont",              "C_cont",             "except_cont", "err"),
    ("S18_nested_not+except_cont",         "nested_not",         "except_cont", "err"),
    ("S19_cur+else_cont",                  "cur",                "none",        "err_cont"),
    ("S20_nested+else_cont+err_only",      "nested",             "none",        "err"),
    ("S21_nested_pass_then_err",           "nested_after_err",   "none",        "err_cont"),
    ("S22_neg_nested+else_cont",           "neg_nested",         "none",        "err_cont"),
    ("S23_nested+try_else_cont",           "nested",             "try_else",    "err"),
    ("S24_nested+after_try+err_only",      "nested",             "after_try",   "err"),
]


def mini_probe():
    say(NL + "=== 4. mini probes: which shape makes the arm-B jump land on the continue block? ===")
    minis = {
        "m1_elif_pass_errcont": """
def _process_cancel_order(self, engine):
    while True:
        if q():
            try:
                if a():
                    A()
                elif b():
                    pass
                else:
                    C()
                    continue
            except BaseException:
                H()
        else:
            E()
            continue
        sleep()
""",
        "m2_nested_cont_sibling": """
def _process_cancel_order(self, engine):
    while True:
        if q():
            try:
                if a():
                    A()
                else:
                    if b():
                        pass
                    else:
                        C()
                    continue
            except BaseException:
                H()
        else:
            E()
            continue
        sleep()
""",
        "m3_nested_not_cont": """
def _process_cancel_order(self, engine):
    while True:
        if q():
            try:
                if a():
                    A()
                else:
                    if not b():
                        C()
                    continue
            except BaseException:
                H()
        else:
            E()
            continue
        sleep()
""",
        "m4_chain_tail_cont": """
def _process_cancel_order(self, engine):
    while True:
        if q():
            try:
                if a():
                    A()
                elif b():
                    pass
                else:
                    C()
                continue
            except BaseException:
                H()
        else:
            E()
            continue
        sleep()
""",
    }
    for name, src in minis.items():
        co = collect(compile(src, "<m>", "exec"))[0]
        ins = {i.offset: i for i in dis.get_instructions(co)}
        j = jump_list(co)
        fwd_on_cont = ["@%d->@%d" % (o, t) for o, op, t in j
                       if op == "JUMP_FORWARD" and t in ins
                       and ins[t].opname in ("JUMP_BACKWARD", "EXTENDED_ARG")]
        backs = ["@%d->@%d" % (o, t) for o, op, t in j if op == "JUMP_BACKWARD"]
        say("%-24s len=%-4d back=%-20s fwd_onto_continue_block=%s" % (
            name, len(co.co_code), ",".join(backs), fwd_on_cont or "none"))


def dump(co, orig, lo, hi):
    for tag, c in (("ORIG", orig), ("PROD", co)):
        say("--- %s %d..%d ---" % (tag, lo, hi))
        for i in dis.get_instructions(c):
            if lo <= i.offset <= hi:
                t = (" -> @%s" % i.argval) if i.opname.startswith(("JUMP", "POP_JUMP")) else ""
                say("  @%-5d %-32s %s%s" % (i.offset, i.opname, i.argval, t))


def deep(name, co, orig):
    keys = ["co_code", "co_exceptiontable", "co_consts", "co_names", "co_varnames",
            "co_freevars", "co_cellvars", "co_nlocals", "co_stacksize", "co_flags",
            "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_linetable"]
    say("deep attribute comparison for %s:" % name)
    for k in keys:
        a, b = getattr(orig, k), getattr(co, k)
        eq = a == b
        extra = ""
        if not eq and k == "co_consts":
            extra = "  (n=%d/%d, differing idx=%s)" % (
                len(a), len(b), [i for i in range(min(len(a), len(b))) if a[i] != b[i]])
        if not eq and k == "co_linetable":
            extra = "  (len %d/%d)" % (len(a), len(b))
        say("   %-22s %s%s" % (k, "EQ" if eq else "NE", extra))


def main():
    say("python %s" % sys.version.replace(NL, " "))
    hdr = open(PYC, "rb").read()[:16]
    say("pyc magic=%s (0x0da7 = 3.11) flags=%s ; interpreter 3.%d -> %s" % (
        hdr[:4].hex(), hdr[4:8].hex(), sys.version_info.minor,
        "SAME minor version: byte compare is exact" if hdr[:2] == b"\xa7\x0d" else "DIFFERENT"))
    orig = max(collect(marshal.loads(open(PYC, "rb").read()[16:])),
               key=lambda c: len(c.co_code))
    say("orig co_code len=%d ; byte@1710=0x%02x (JUMP_FORWARD) operand @1711=0x%02x -> @%d" % (
        len(orig.co_code), orig.co_code[1710], orig.co_code[1711],
        1710 + 2 + orig.co_code[1711] * 2))
    ins = {i.offset: i for i in dis.get_instructions(orig)}
    say("verify: @44=%s @46=%s @1822=%s @1824=%s->@%s @1826=%s->@%s @2042=%s->@%s" % (
        ins[44].opname, ins[46].opname, ins[1822].opname, ins[1824].opname, ins[1824].argval,
        ins[1826].opname, ins[1826].argval, ins[2042].opname, ins[2042].argval))
    jl = jump_list(orig)
    say("orig backward edges : %s" % ["@%d->@%d" % (o, t) for o, op, t in jl if op == "JUMP_BACKWARD"])
    say("orig enters @1822   : %s" % ["@%d %s" % (o, op) for o, op, t in jl if t == 1822])
    say("orig enters @1826   : %s" % ["@%d %s" % (o, op) for o, op, t in jl if t == 1826])
    say("orig exc table      : %s" % orig.co_exceptiontable.hex())
    say(NL + "=== 3. shape family (whole-module compile, %d shapes) ===" % len(SHAPES))
    res = []
    for name, kind, tail, elsem in SHAPES:
        try:
            co = max(collect(compile(build(kind, tail, elsem), "<shape>", "exec")),
                     key=lambda c: len(c.co_code))
        except SyntaxError as e:
            say("%-27s SYNTAX ERROR %s" % (name, e))
            continue
        res.append((cmp_(name, co, orig), name, kind, tail, elsem))
    mini_probe()
    res.sort(key=lambda r: r[0])
    say(NL + "=== ranking (fewest co_code diffs first) ===")
    for key, name, kind, tail, elsem in res:
        say("%-27s diffs=%-4d jumps_eq=%-5s exc_eq=%-5s first_diff=%s" % (
            name, key[0], not key[1], not key[2], key[3]))
    key, name, kind, tail, elsem = res[0]
    say(NL + "BEST = %s  (chain=%s tail=%s else=%s) diffs=%d" % (name, kind, tail, elsem, key[0]))
    say(NL + "the winning region text:")
    win = build(kind, tail, elsem)
    wl = win.splitlines()
    for i in range(550, min(573, len(wl))):
        say("   %4d | %s" % (i + 1, wl[i]))
    deep(name, max(collect(compile(win, "<shape>", "exec")), key=lambda c: len(c.co_code)), orig)
    for key2, name2, kind2, tail2, elsem2 in res[1:3]:
        deep(name2, max(collect(compile(build(kind2, tail2, elsem2), "<shape>", "exec")),
                        key=lambda c: len(c.co_code)), orig)
    co = max(collect(compile(build(kind, tail, elsem), "<shape>", "exec")),
             key=lambda c: len(c.co_code))
    d = [k for k in range(min(len(orig.co_code), len(co.co_code)))
         if orig.co_code[k] != co.co_code[k]]
    say("len orig=%d prod=%d ; diff offsets (n=%d): %s" % (
        len(orig.co_code), len(co.co_code), len(d), d[:40]))
    import hashlib
    say("sha256 co_code orig=%s" % hashlib.sha256(orig.co_code).hexdigest())
    say("sha256 co_code prod=%s" % hashlib.sha256(co.co_code).hexdigest())
    say("exc orig=%s" % orig.co_exceptiontable.hex())
    say("exc prod=%s" % co.co_exceptiontable.hex())
    jx, jy = jump_list(orig), jump_list(co)
    say("jumps equal: %s ; count %d vs %d" % (jx == jy, len(jx), len(jy)))
    if len(jx) == len(jy):
        for a, b in zip(jx, jy):
            if a != b:
                say("   jump-diff: orig %s  prod %s" % (a, b))
    dump(co, orig, 1600, 1720)
    dump(co, orig, 1810, 2044)
    LOG.close()


if __name__ == "__main__":
    main()
