#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Differential fuzz driver for attack-completeness-claims Task 9.5.

Generates deterministic CPython 3.11 programs, compiles them, decompiles the
pyc with the project CLI, then compares the original pyc and regenerated
source through semantic_diff.py.  The generator imports no product code.

A bounded run is deliberately not a claim of the weekly 4-CPU-hour fuzz:
the report records the actual budget and the stopping reason.

CLI:
    python -X utf8 tools/completeness/fuzz_driver.py --seed 0 --cases 24 \
        --seconds 90 --json .trae/specs/.../rounds/round9/fuzz_report.jsonl
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import py_compile
import random
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import semantic_diff as sd

TOOL_VERSION = "1.0.0"
PYCDC = os.path.join(ROOT, "pycdc.py")
FAMILIES = ("rare_syntax", "deep_host", "semantic_trap")
FAILURE_STATUSES = ("DIFFERENT", "ERROR", "PRODUCT_COMPILE_ERROR", "DECOMPILE_ERROR",
                    "SOURCE_COMPILE_ERROR", "HARNESS_ERROR")

TEMPLATES = {
    "rare_syntax": [
        ("walrus-comp", """def main():
    n = @N@
    vals = [y for x in range(n) if (y := x * 2) > 2]
    return vals, y
"""),
        ("match-mapping", """def main():
    value = {"k": [@N@, @N@ + 1]}
    match value:
        case {"k": [a, b]} if a < b:
            return ("map", a, b)
        case [a, *rest]:
            return ("seq", a, len(rest))
        case _:
            return ("other",)
"""),
        ("except-star", """def main():
    out = []
    try:
        raise ExceptionGroup("g", [ValueError("v"), TypeError("t")])
    except* ValueError as exc:
        out.append(("v", len(exc.exceptions)))
    except* TypeError as exc:
        out.append(("t", len(exc.exceptions)))
    return out
"""),
        ("async-gen", """import asyncio

async def main():
    async def gen(n):
        for i in range(n):
            yield i
    out = []
    async for i in gen(@N@):
        out.append(i)
    return out
"""),
        ("nested-fstring", """def main():
    value = @N@.25
    width = 6
    return f"{value!r:>{width}}/{value:{width}.2f}"
"""),
        ("starred-unpack", """def main():
    data = [@N@, @N@ + 1, @N@ + 2, @N@ + 3]
    first, *middle, last = data
    def call(a, b, c):
        return a + b + c
    return first, middle, last, call(*data[:3]), {**{"k": last}}
"""),
        ("decorator-order", """def deco(tag):
    def wrap(fn):
        def inner(*args, **kwargs):
            return (tag, fn(*args, **kwargs))
        return inner
    return wrap

@deco("outer")
@deco("inner")
def main():
    return @N@ + 1
"""),
        ("annotations-posonly", """def main(x: int | None = None, /, *, y: "int" = @N@) -> int | None:
    return x if x is not None else y
"""),
    ],
    "deep_host": [
        ("try-match-finally", """def main():
    out = []
    for i in range(@N@):
        try:
            match i:
                case 0:
                    out.append("zero")
                case _ if i % 2:
                    out.append("odd")
                case _:
                    raise ValueError(i)
        except ValueError as exc:
            out.append(("err", exc.args[0]))
        finally:
            out.append(("fin", i))
    return out
"""),
        ("comp-in-try", """def main():
    out = []
    try:
        out = [x * x for x in range(@N@) if x % 2]
        out += [y for x in out for y in (x, x + 1)]
    except Exception as exc:
        out.append(type(exc).__name__)
    finally:
        out.append("done")
    return out
"""),
        ("with-for-context", """class Ctx:
    def __init__(self, tag, events):
        self.tag = tag
        self.events = events
    def __enter__(self):
        self.events.append(("enter", self.tag))
        return self
    def __exit__(self, exc_type, exc, tb):
        self.events.append(("exit", self.tag, exc_type.__name__ if exc_type else None))
        return False

def main():
    events = []
    with Ctx("a", events):
        for i in range(@N@):
            with Ctx("b", events):
                events.append(("body", i))
    return events
"""),
        ("closure-default", """def main():
    fns = []
    for i in range(@N@):
        def f(x, i=i):
            return x + i
        fns.append(f)
    return [f(10) for f in fns]
"""),
        ("except-star-with", """class Ctx:
    def __init__(self, events):
        self.events = events
    def __enter__(self):
        self.events.append("enter")
        return self
    def __exit__(self, exc_type, exc, tb):
        self.events.append("exit")
        return False

def main():
    out = []
    with Ctx(out):
        try:
            raise ExceptionGroup("g", [ValueError("v"), OSError("o")])
        except* ValueError as exc:
            out.append(("v", len(exc.exceptions)))
        except* OSError as exc:
            out.append(("o", len(exc.exceptions)))
    return out
"""),
        ("lambda-comp", """def main():
    n = @N@
    first = [(lambda x, y=n: x * y)(i) for i in range(n)]
    second = [x for x in range(n) if (lambda y: y % 2)(x)]
    return first, second
"""),
        ("loop-else-break", """def main():
    out = []
    for i in range(@N@):
        for j in range(@N@ + 1):
            if j == i:
                break
        else:
            out.append(("none", i))
            continue
        out.append(("break", i, j))
    return out
"""),
        ("nested-class", """class Outer:
    class Inner:
        def __init__(self, value):
            self.value = value
        def bump(self, n):
            return self.value + n

def main():
    obj = Outer.Inner(@N@)
    return obj.bump(2), Outer.Inner.__qualname__
"""),
    ],
    "semantic_trap": [
        ("short-circuit", """def main():
    events = []
    def t(value):
        events.append(value)
        return value
    left = t(0) and t(1)
    right = t(2) or t(3)
    return left, right, events
"""),
        ("alias-mutation", """def main():
    a = [1, 2]
    b = a
    b.append(3)
    c = list(a)
    c.append(4)
    return a, b, c, a is b, a is c
"""),
        ("late-binding", """def main():
    fns = [lambda: i for i in range(@N@)]
    return [f() for f in fns]
"""),
        ("decorator-effects", """def main():
    out = []
    def outer(tag):
        def inner(fn):
            def wrapped(*args, **kwargs):
                out.append(tag)
                return fn(*args, **kwargs)
            return wrapped
        return inner
    @outer("a")
    @outer("b")
    def f(x):
        return x + 1
    return f(@N@), out
"""),
        ("exception-context", """def main():
    try:
        try:
            1 / 0
        except ZeroDivisionError as first:
            raise ValueError("wrapped") from first
    except ValueError as second:
        return type(second.__cause__).__name__, second.__context__ is second.__cause__
"""),
        ("float-edges", """def main():
    values = [0.0, -0.0, float("nan"), float("inf")]
    return [(str(v), v == 0.0) for v in values], values[0] == values[1], values[2] == values[2]
"""),
        ("generator-send", """def main():
    events = []
    def gen(n):
        try:
            value = yield 0
            while value < n:
                value = yield value + 1
        finally:
            events.append("closed")
    g = gen(@N@)
    out = [next(g)]
    out.append(g.send(1))
    out.append(g.send(2))
    g.close()
    return out, events
"""),
        ("finally-return", """events = []

def main():
    global events
    try:
        for i in range(@N@):
            try:
                if i == 1:
                    return ("ret", i)
            finally:
                events.append(("fin", i))
    finally:
        events.append("outer")
    return events
"""),
    ],
}


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def materialize(template: str, rng: random.Random) -> str:
    return template.replace("@N@", str(rng.randint(2, 5)))


def generate_cases(seed: int, limit: int, families=None, offset: int = 0) -> list[dict]:
    wanted = [f for f in (families or FAMILIES) if f in TEMPLATES]
    if not wanted:
        wanted = list(FAMILIES)
    rng = random.Random(seed)
    out = []
    for index in range(limit):
        family = wanted[(offset + index) % len(wanted)]
        name, template = TEMPLATES[family][(offset + index) // len(wanted) % len(TEMPLATES[family])]
        source = materialize(template, rng)
        try:
            ast.parse(source)
        except SyntaxError as exc:
            raise RuntimeError("generator produced invalid %s/%s: %s" % (family, name, exc))
        case_id = "FZ-%s-%03d-%s" % (family.replace("_", ""), index + offset,
                                     sha_text(source)[:8])
        out.append({
            "case_id": case_id, "family": family, "template": name,
            "source": source, "entrypoint": "main", "args": [], "kwargs": {},
        })
    return out


def _compile_source(source_path: str, pyc_path: str):
    try:
        py_compile.compile(source_path, cfile=pyc_path, doraise=True)
    except py_compile.PyCompileError as exc:
        return False, str(exc)
    except BaseException as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    return True, ""


def _decompile(pyc_path: str, product_path: str, decompiler: str, timeout: float):
    command = [sys.executable, "-X", "utf8", decompiler, pyc_path, "-o", product_path]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {"returncode": None, "timeout": True,
                "stdout": (exc.stdout or "")[-2000:], "stderr": (exc.stderr or "")[-2000:],
                "elapsed_s": round(time.monotonic() - started, 4)}
    return {"returncode": completed.returncode, "timeout": False,
            "stdout": (completed.stdout or "")[-2000:],
            "stderr": (completed.stderr or "")[-2000:],
            "elapsed_s": round(time.monotonic() - started, 4)}


def _product_compile(product_path: str):
    try:
        with open(product_path, "r", encoding="utf-8-sig", errors="replace") as fh:
            source = fh.read()
        compile(source, product_path, "exec")
    except BaseException as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    return True, ""


def evaluate_source(source: str, case_id: str, workdir: str, *, entrypoint: str = "main",
                    args=None, kwargs=None, seed: int = 0, decompiler: str = PYCDC,
                    timeout: float = 20.0) -> dict:
    started = time.monotonic()
    os.makedirs(workdir, exist_ok=True)
    source_path = os.path.join(workdir, "subject.py")
    pyc_path = os.path.join(workdir, "subject.pyc")
    product_path = os.path.join(workdir, "product.py")
    with open(source_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(source)
    record = {
        "case_id": case_id, "seed": seed, "entrypoint": entrypoint,
        "args": args or [], "kwargs": kwargs or {},
        "source_sha256": sha_text(source), "source_path": source_path,
        "pyc_path": pyc_path, "product_path": product_path,
        "status": "", "diffs": [], "errors": [], "inconclusive": [],
    }
    ok, error = _compile_source(source_path, pyc_path)
    if not ok:
        record.update(status="SOURCE_COMPILE_ERROR", errors=[error],
                      elapsed_s=round(time.monotonic() - started, 4))
        return record
    record["pyc_sha256"] = sha_file(pyc_path)
    dec = _decompile(pyc_path, product_path, decompiler, timeout)
    record["decompile"] = {k: dec[k] for k in ("returncode", "timeout", "elapsed_s")}
    if dec["stderr"]:
        record["decompile"]["stderr_tail"] = dec["stderr"][-500:]
    if dec["timeout"]:
        record.update(status="DECOMPILE_ERROR", errors=["decompiler timed out"],
                      elapsed_s=round(time.monotonic() - started, 4))
        return record
    if dec["returncode"] != 0 or not os.path.isfile(product_path):
        record.update(status="DECOMPILE_ERROR",
                      errors=["decompiler returncode=%r" % dec["returncode"]],
                      elapsed_s=round(time.monotonic() - started, 4))
        return record
    record["product_sha256"] = sha_file(product_path)
    ok, error = _product_compile(product_path)
    if not ok:
        record.update(status="PRODUCT_COMPILE_ERROR", errors=[error],
                      elapsed_s=round(time.monotonic() - started, 4))
        return record
    case = {
        "case_id": case_id + "-semantic", "entrypoint": entrypoint,
        "args": record["args"], "kwargs": record["kwargs"], "seed": seed,
        "original": {"path": pyc_path, "kind": "pyc"},
        "product": {"path": product_path, "kind": "source"},
        "timeout_s": max(2.0, min(timeout, 10.0)),
    }
    try:
        result = sd.compare_case(case)
    except BaseException as exc:
        record.update(status="HARNESS_ERROR",
                      errors=["%s: %s" % (type(exc).__name__, exc)],
                      elapsed_s=round(time.monotonic() - started, 4))
        return record
    record.update({
        "status": result.get("status", "HARNESS_ERROR"),
        "diffs": result.get("diffs") or [],
        "errors": result.get("errors") or [],
        "inconclusive": result.get("inconclusive") or [],
        "tolerances": result.get("tolerances") or [],
        "elapsed_s": round(time.monotonic() - started, 4),
    })
    return record


def write_jsonl(path: str, records: list[dict]) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _summary(records: list[dict], stopped: str, budget: float) -> dict:
    counts = {}
    for record in records:
        counts[record["status"]] = counts.get(record["status"], 0) + 1
    return {
        "tool": "fuzz_driver", "version": TOOL_VERSION,
        "total": len(records), "counts": counts,
        "failures": sum(1 for r in records if r["status"] in FAILURE_STATUSES),
        "budget_seconds": budget, "stopped": stopped,
        "new_diff": sum(1 for r in records if r["status"] == "DIFFERENT"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CPython 3.11 differential fuzzer")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cases", type=int, default=0,
                        help="0 = run until the time budget")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--hours", type=float, default=0.0)
    parser.add_argument("--json", default="logs/fuzz_report.jsonl")
    parser.add_argument("--summary", default="")
    parser.add_argument("--workdir", default="")
    parser.add_argument("--decompiler", default=PYCDC)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--families", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--keep-equal", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    budget = args.hours * 3600.0 if args.hours > 0 else args.seconds
    if budget <= 0 or args.cases < 0:
        print("[fuzz] no budget/cases", file=sys.stderr)
        return 2
    families = [part.strip() for part in args.families.split(",") if part.strip()] or None
    run_root = args.workdir or tempfile.mkdtemp(prefix="pycdc_fuzz_%d_" % args.seed)
    os.makedirs(run_root, exist_ok=True)
    started = time.monotonic()
    records = []
    stopped = "case_limit"
    work_root = os.path.join(run_root, "cases")
    offset = args.offset
    try:
        while True:
            if args.cases and offset - args.offset >= args.cases:
                break
            if time.monotonic() - started >= budget:
                stopped = "time_budget"
                break
            chunk_size = 100
            if args.cases:
                chunk_size = min(chunk_size, args.cases - (offset - args.offset))
            cases = generate_cases(args.seed, chunk_size, families, offset)
            if not cases:
                break
            for case in cases:
                if time.monotonic() - started >= budget:
                    stopped = "time_budget"
                    break
                case_dir = os.path.join(work_root, case["case_id"])
                record = evaluate_source(case["source"], case["case_id"], case_dir,
                                         entrypoint=case["entrypoint"], args=case["args"],
                                         kwargs=case["kwargs"], seed=args.seed,
                                         decompiler=args.decompiler, timeout=args.timeout)
                record["family"] = case["family"]
                record["template"] = case["template"]
                records.append(record)
                print("[fuzz] %-28s %-22s %s" % (case["case_id"], record["status"],
                                                 record.get("diffs", [{}])[0].get("dimension", "")
                                                 if record.get("diffs") else ""))
                if record["status"] == "EQUAL" and not args.keep_equal:
                    shutil.rmtree(case_dir, ignore_errors=True)
                    record["source_path"] = ""
                    record["product_path"] = ""
                    record["pyc_path"] = ""
            offset += len(cases)
            if stopped == "time_budget":
                break
    finally:
        summary = _summary(records, stopped, budget)
        write_jsonl(args.json, records)
        summary_path = args.summary or os.path.splitext(args.json)[0] + ".summary.json"
        with open(summary_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("[fuzz] total=%d failures=%d stopped=%s workdir=%s"
              % (summary["total"], summary["failures"], stopped, run_root))
    if summary["total"] == 0:
        return 2
    return 0 if summary["failures"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
