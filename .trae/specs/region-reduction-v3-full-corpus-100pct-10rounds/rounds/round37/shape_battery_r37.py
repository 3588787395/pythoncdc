"""Resident shape battery for the while/try/ternary emission families (round 37).

For each small source shape we: compile it to a .pyc with THIS interpreter, decompile that pyc with
a given set of pipeline sources, re-compile the emitted function, and compare the instruction table
against the original. That is a real round-trip: the .pyc is produced from a hand-written source and
the decompiler must recover it; the assertion is about the decompiler's output, not about my source.

Readings ACTUALLY obtained on the gate-36 landed bytes (verdict = scripts/pyc_verify.py single,
the same verifier the gate uses; each module has 3 units and in all four rows the two outer units
are green, so the rig has a built-in positive control and the failure is always the target `h`):

  A_while_true_nested_if_merge     2/3  Different control flow  -- NOT a clean probe of the gate-36
      criterion. Its `h` is mangled by a DIFFERENT mechanism: the arm `if trade_status == STOP:
      bus.publish(2); return None` comes back as `elif trade_status == STOP: continue` with
      `bus.publish(2)` hoisted to AFTER the loop and `return None` replaced by `break`, and the
      `if/else` after it becomes `if/elif/else`. So row A is a minimal, fast repro of the
      return-None-vs-break terminator family (see memory pythoncdc-return-none-vs-break-terminator-
      family), which is why it stays red even though the real victim `_trade_status_handle` is 0/0.
      Do not read row A as a regression of gate 36; a clean probe of that criterion needs arms that
      do not end in `return None`.
  B_exclusive_continue_else_arm    2/3  DIFFER, len 35 vs 34, first diff at @2 is a polarity change
      (POP_JUMP_FORWARD_IF_FALSE -> POP_JUMP_FORWARD_IF_TRUE) = the repro arm for R21-36.
  C_try_body_ends_in_continue      2/3  len 53 vs 53 with exactly ONE positional diff: the original
      `JUMP_BACKWARD` (continue inside the try body) replaced by `JUMP_FORWARD` = the cleanest
      possible repro of R21-35, and its single-diff shape matches the corpus unit's delta=-1.
  D_ternary_as_call_argument       2/3  len 27 vs 25, the call's tail lost at the arm boundary = the
      repro arm for R21-37.

A candidate that lands must turn its own row green without turning any other row red; row A is
expected to stay red until the terminator family is separately closed.

usage: python -X utf8 shape_battery_r37.py <pipeline_root>            # e.g. the repo or a mirror
"""
import dis
import marshal
import os
import py_compile
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = type(compile('', '', 'exec'))
NOISE = ('RESUME', 'CACHE')

SHAPES = {}

SHAPES['A_while_true_nested_if_merge'] = '''
class T:
    def h(self, engine, trade_status):
        engine.set_engine(engine)
        while True:
            self.trade_info = get_trade_status(self.trade_id, return_trade_info=True)
            trade_status = self.trade_info[2]
            if self.trade_status != trade_status:
                self.trade_status = trade_status
                if trade_status == PAUSE:
                    bus.publish(1)
                    continue
                if trade_status == STOP:
                    bus.publish(2)
                    return None
                else:
                    bus.publish(3)
            else:
                time.sleep(0.5)
'''

SHAPES['B_exclusive_continue_else_arm'] = '''
class T:
    def h(self, message):
        while True:
            if message:
                stocks = list(message.keys())[0]
                data = message.get(stocks)
                if data:
                    handle(data)
            else:
                log.warning('empty')
                continue
'''

SHAPES['C_try_body_ends_in_continue'] = '''
class T:
    def h(self, order):
        while True:
            try:
                ed = call(order)
                if ed.get('error_no') == 0:
                    log.info('ok')
                else:
                    log.error('bad')
                continue
            except BaseException:
                log.error('exc')
            time.sleep(0.001)
'''

SHAPES['D_ternary_as_call_argument'] = '''
class T:
    def h(self, order):
        side_txt = 'BUY' if order.side == 'OPEN' else 'SELL'
        broker.submit(order, side_txt, order.amount, note='x' if order.flag else 'y')
'''


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


def pick(codes, name):
    hits = [c for c in codes if c.co_name == name]
    return max(hits, key=lambda k: len(k.co_code)) if hits else None


def table(code):
    out = []
    for i in dis.get_instructions(code):
        if i.opname in NOISE:
            continue
        arg = i.argrepr
        if i.opname == 'LOAD_CONST' and isinstance(i.argval, CO):
            arg = '<code>'
        out.append((i.opname, arg))
    return out


def run(root):
    root = os.path.abspath(root)
    work = os.path.join(os.environ['TEMP'], 'r37_battery')
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    print('pipeline root: %s' % root)
    rows = []
    for name, src in sorted(SHAPES.items()):
        py = os.path.join(work, name + '.py')
        pyc = os.path.join(work, name + '.pyc')
        outp = os.path.join(work, name + 'OK.py')
        with open(py, 'w', encoding='utf-8') as fh:
            fh.write(src.lstrip('\n'))
        py_compile.compile(py, cfile=pyc, doraise=True)
        if os.path.exists(outp):
            os.remove(outp)
        r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', outp],
                           cwd=root, capture_output=True, text=True, timeout=200)
        if not os.path.exists(outp) or os.path.getsize(outp) < 40:
            rows.append((name, 'NO_PRODUCT', 'rc=%d %s' % (r.returncode, (r.stderr or '')[-80:])))
            continue
        # Verdict comes from the SAME verifier the gate uses; my own instruction-table compare is
        # diagnostics only - it flags jump-target VALUE changes that the authoritative judge treats
        # as equivalent CFG layout, so it must never be the ruler here.
        v = subprocess.run([sys.executable, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', pyc,
                            '--source', outp], cwd=root, capture_output=True, text=True, timeout=200)
        vl = [l.strip() for l in (v.stdout or '').splitlines() if 'units=' in l]
        verdict = vl[-1] if vl else 'rc=%d %s' % (v.returncode, (v.stderr or '')[-90:])
        detail = ''
        orig_code = marshal.loads(open(pyc, 'rb').read()[16:])
        acc = []
        gather(orig_code, acc)
        o = pick(acc, 'h') or pick(acc, '<module>')
        emitted = open(outp, encoding='utf-8-sig').read()
        try:
            mod = compile(emitted, '<b>', 'exec')
        except SyntaxError as e:
            rows.append((name, 'SYNTAX_ERROR', str(e)))
            continue
        acc2 = []
        gather(mod, acc2)
        p = pick(acc2, 'h')
        if p is not None:
            to, tp = table(o), table(p)
            diffs = [(k, a, b) for k, (a, b) in enumerate(zip(to, tp)) if a != b]
            detail = 'len %d/%d, %d positional diffs%s' % (len(to), len(tp), len(diffs),
                                                           ('; first@%d %s->%s' % (diffs[0][0],
                                                            diffs[0][1][1], diffs[0][2][1])) if diffs else '')
        rows.append((name, 'VERIFY ' + verdict, detail))
    for name, verdict, detail in rows:
        print('  %-32s %-58s %s' % (name, verdict, detail))
    return dict((n, v) for n, v, _ in rows)


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else HERE)
