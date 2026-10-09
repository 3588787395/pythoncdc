"""Run the whole round gate chain in ONE background invocation, so the landing costs a few polls
instead of one turn per stage.

gate_round.py refuses `--stage all` (each stage's internal subprocess cap is 250 s, and the 300 s
per-command rule forbids chaining them in the foreground), so previously every stage was its own
launch + its own poll. This wrapper is pure orchestration: it shells out to gate_round.py stage by
stage, appends everything to one log, and stops at the first stage that does not report success.
No judgement logic lives here — the sole judge stays scripts/pyc_verify.py.

usage:
  python -X utf8 gate_chain.py <label> <before-label>            # run the chain
  python -X utf8 gate_chain.py <label> <before-label> --dry      # print the plan only
  stages: regen -> verify -> report -> checks  (pass "--only report,checks" to re-run a tail)
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STAGES = ["regen", "verify", "report", "checks"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("before")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--timeout", type=int, default=5400,
                    help="per-stage wall cap; must exceed gate_round's own per-subprocess cap")
    a = ap.parse_args()

    todo = [s for s in STAGES if not a.only or s in [x.strip() for x in a.only.split(",")]]
    cmds = [["python", "-X", "utf8", os.path.join(HERE, "gate_round.py"), a.label, a.before,
             "--stage", s] for s in todo]
    if a.dry:
        for s, c in zip(todo, cmds):
            print("PLAN %s: cd %s && %s" % (s, ROOT, " ".join(c)))
        print("PLAN stages=%s label=%s before=%s" % (",".join(todo), a.label, a.before))
        return 0

    log = os.path.join(os.environ.get("TEMP", "D:/Temp"),
                       "gate_chain_%s_%s.log" % (a.label, time.strftime("%H%M%S")))
    with open(log, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("#### chain label=%s before=%s stages=%s\n" % (a.label, a.before, ",".join(todo)))
        fh.flush()
        for s, c in zip(todo, cmds):
            t0 = time.time()
            fh.write("\n==== STAGE_START %s ====\n" % s)
            fh.flush()
            try:
                p = subprocess.run(c, cwd=ROOT, stdout=fh, stderr=fh, text=True,
                                   encoding="utf-8", errors="replace", timeout=a.timeout)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                rc = 124
                fh.write("[TIMEOUT] stage %s exceeded %ds\n" % (s, a.timeout))
            dur = int(time.time() - t0)
            fh.write("==== STAGE_END %s rc=%d %ds ====\n" % (s, rc, dur))
            fh.flush()
            print("STAGE %-7s rc=%-3d %5ds  log=%s" % (s, rc, dur, log), flush=True)
            if rc != 0:
                print("CHAIN ABORTED at %s (rc=%d)" % (s, rc), flush=True)
                return rc
    print("CHAIN_DONE label=%s log=%s" % (a.label, log), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
