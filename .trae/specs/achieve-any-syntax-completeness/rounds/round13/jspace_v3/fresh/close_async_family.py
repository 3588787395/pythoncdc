#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Close the async-only family with a real sync driver over ``asyncio.run``.

The J v3 preparer deliberately emits no calls for ``async def`` because a bare
``eval('fn(...)')`` only creates a coroutine and cannot observe its result.
That leaves 62 entries with ``no_top_level_callable_with_constructible_arguments``.

This tool adds one *self-contained* call expression per async entrypoint.  Each
expression:

1. executes a fixed driver prelude in a private namespace (``_d``), so the
   module under test is not polluted with helper globals;
2. calls the module-level async function through ``globals()``;
3. drives it with ``_d['_asyncio'].run(...)`` (and ``_consume`` for async
   generators), which is exactly the callable-entrypoint semantics required by
   the spec.

The driver arguments are structural: ``g``/``h`` are async callables, ``ait``
is an async iterable, ``mgr`` is an async/sync context manager, ``io`` exposes
async methods, ``flag`` is exercised in both truth values, and ``xs``/``b`` are
small deterministic iterables.  No entry is marked covered here; only C4
``EQUAL`` records survive the checker.

Run from the repository root:

    python -X utf8 .../fresh/close_async_family.py
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import sys

TOOL_VERSION = "1.0.0"

DRIVER_SOURCE = r'''
import asyncio as _asyncio

class _AI:
    def __init__(self, xs):
        self._xs = list(xs)
        self._i = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self._i >= len(self._xs):
            raise StopAsyncIteration
        value = self._xs[self._i]
        self._i += 1
        return value

async def _g(x):
    return x + 1

async def _h(x):
    return x * 2

class _AMgr:
    async def __aenter__(self):
        return 10
    async def __aexit__(self, *exc):
        return False

class _CM:
    def __enter__(self):
        return 5
    def __exit__(self, *exc):
        return False

class _IO:
    async def a(self):
        return 1
    async def b(self):
        return 2

async def _consume(agen):
    return [item async for item in agen]
'''

DRIVER_SHA = hashlib.sha256(DRIVER_SOURCE.encode("utf-8")).hexdigest()


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def dump(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def _has(fn: ast.AST, kinds) -> bool:
    return any(isinstance(node, kinds) for node in ast.walk(fn))


def _wrap(fn_name: str, args: list[str], consume: bool) -> str:
    call = "globals()[%r](%s)" % (fn_name, ", ".join(args))
    if consume:
        call = "_d['_consume'](%s)" % call
    return ("(lambda _d: (exec(%r, _d), _d['_asyncio'].run(%s))[1])({})"
            % (DRIVER_SOURCE, call))


def async_calls(tree: ast.Module) -> tuple[list[str], list[str], list[str]]:
    """Return ``(calls, used_functions, skipped)`` for top-level async defs."""
    calls: list[str] = []
    used: list[str] = []
    skipped: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if node.args.vararg or node.args.kwarg:
            skipped.append("%s: vararg/kwarg" % node.name)
            continue
        positional = list(node.args.posonlyargs) + list(node.args.args)
        kwonly = [arg.arg for arg in node.args.kwonlyargs]
        tuple_ait = _has(node, ast.AsyncFor) and any(
            isinstance(item, ast.AsyncFor) and isinstance(item.target, (ast.Tuple, ast.List))
            for item in ast.walk(node))
        async_with = _has(node, ast.AsyncWith)
        consume = _has(node, (ast.Yield, ast.YieldFrom))
        variants: list[dict[str, str]] = [{}]
        ok = True
        for arg in positional:
            name = arg.arg
            if name == "flag":
                variants = [dict(item, flag=value) for item in variants for value in ("True", "False")]
                continue
            if name == "g":
                expr = "_d['_g']"
            elif name == "h":
                expr = "_d['_h']"
            elif name == "ait":
                expr = "_d['_AI']([(1, 2), (3, 4)])" if tuple_ait else "_d['_AI']([1, 2])"
            elif name == "mgr":
                expr = "_d['_AMgr']()" if async_with else "_d['_CM']()"
            elif name == "io":
                expr = "_d['_IO']()"
            elif name == "xs":
                expr = "[1, 2]"
            elif name == "b":
                expr = "[10, 20]"
            else:
                skipped.append("%s: unknown parameter %s" % (node.name, name))
                ok = False
                break
            variants = [dict(item, **{name: expr}) for item in variants]
        if not ok:
            continue
        for name in kwonly:
            skipped.append("%s: keyword-only parameter %s" % (node.name, name))
            ok = False
        if not ok:
            continue
        for variant in variants:
            args = [variant[arg.arg] for arg in positional]
            calls.append(_wrap(node.name, args, consume))
        used.append(node.name)
    return calls, used, skipped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", required=True)
    parser.add_argument("--out-space", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args(argv)

    space = load(args.space)
    entries = space.get("entries") or []
    selected = []
    report = {
        "tool": "close_async_family",
        "version": TOOL_VERSION,
        "driver_sha256": DRIVER_SHA,
        "model": "self-contained sync driver: exec(driver, _d); _d['_asyncio'].run(globals()[fn](args))",
        "entries": [],
        "skipped": [],
    }
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("derivation") != "no_top_level_callable_with_constructible_arguments":
            continue
        source = entry.get("p_j") or ""
        try:
            tree = ast.parse(open(source, "r", encoding="utf-8-sig").read())
        except (OSError, SyntaxError) as exc:
            report["skipped"].append({"id": entry.get("id"), "reason": "%s: %s" % (type(exc).__name__, exc)})
            continue
        top = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not top or any(isinstance(node, ast.FunctionDef) for node in top):
            report["skipped"].append({"id": entry.get("id"), "reason": "not async-only"})
            continue
        calls, used, skipped = async_calls(tree)
        if not calls:
            report["skipped"].append({"id": entry.get("id"), "reason": "no constructible async driver",
                                      "detail": skipped})
            continue
        entry = dict(entry)
        model = dict(entry.get("input_model") or {})
        model["kind"] = "module"
        model["calls"] = calls
        model["seed"] = model.get("seed") or 0
        model["note"] = (
            "J v3 async driver: each call is a self-contained expression that runs a fixed "
            "driver prelude in a private namespace and invokes the module-level async "
            "entrypoint through asyncio.run (async generators are consumed); the driver "
            "source hash is bound in call_static.async_driver.driver_sha256."
        )
        entry["input_model"] = model
        entry["excluded"] = []
        entry["status"] = "callable"
        entry["derivation"] = "async_driver"
        entry["call_static"] = {
            "async_driver": {
                "model": "asyncio.run over structural driver objects",
                "driver_sha256": DRIVER_SHA,
                "functions": used,
                "skipped": skipped,
            }
        }
        selected.append(entry)
        report["entries"].append({
            "id": entry.get("id"), "p_j": source, "functions": used,
            "calls": len(calls), "skipped": skipped,
        })
    out_space = dict(space)
    out_space["entries"] = entries
    out_space["async_family"] = {
        "tool": "close_async_family", "version": TOOL_VERSION,
        "driver_sha256": DRIVER_SHA, "selected": len(selected),
        "model": report["model"],
    }
    # Replace the selected entries in place, preserving the manifest order.
    by_id = {entry.get("id"): entry for entry in selected}
    out_space["entries"] = [by_id.get(entry.get("id"), entry) for entry in entries]
    manifest = dict(space)
    manifest["entries"] = selected
    manifest["async_family"] = out_space["async_family"]
    dump(args.out_space, out_space)
    dump(args.out_manifest, manifest)
    if args.report:
        dump(args.report, report)
    print("[async] selected=%d skipped=%d driver_sha256=%s"
          % (len(selected), len(report["skipped"]), DRIVER_SHA[:12]))
    for item in report["skipped"]:
        print("[async] skip %s: %s" % (item.get("id"), item.get("reason")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
