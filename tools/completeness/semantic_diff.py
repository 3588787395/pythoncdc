#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semantic differential comparator (attack-completeness-claims Task 9.1).

Runs the original artifact and the regenerated product in two isolated child
processes with identical arguments, seeded files, cwd, environment and RNG
seed.  Compares R1 return/outcome, R2 stdout, R3 stderr, R4 ordered events,
R5 side effects, R6 exceptions and R7 metadata.  Structural equality is never
treated as semantic equality; missing evidence is INCONCLUSIVE, not EQUAL.

CLI:
    python -X utf8 tools/completeness/semantic_diff.py --case case.json
    python -X utf8 tools/completeness/semantic_diff.py --cases cases.jsonl \
        --out results.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import builtins
import hashlib
import importlib.machinery
import importlib.util
import inspect
import io
import json
import math
import os
import random
import re
import reprlib
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import types
from typing import Any

TOOL_VERSION = "1.0.0"
EQUAL, DIFFERENT, INCONCLUSIVE, ERROR = "EQUAL", "DIFFERENT", "INCONCLUSIVE", "ERROR"
DEFAULT_TIMEOUT_S = 8.0
MAX_DEPTH = 40
MAX_ITEMS = 2000
MAX_GLOBALS = 200
DEFAULT_METADATA_IGNORE = (
    "metadata.code.co_filename",
    "metadata.code.co_firstlineno",
    "metadata.code.co_linetable",
)
# R7 blocking (achieve-any-syntax-completeness Task 1.2): code-object fields whose
# differences must always yield DIFFERENT.  They can never be silenced through
# tolerance.ignore_metadata_fields; see TOLERANCE_REGISTRY.md in the spec root.
PROTECTED_METADATA_FIELDS = ("co_code", "co_consts", "co_exceptiontable")
CO_FIELDS = (
    "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals",
    "co_stacksize", "co_flags", "co_names", "co_varnames", "co_freevars",
    "co_cellvars", "co_code", "co_consts", "co_filename", "co_firstlineno",
    "co_linetable", "co_exceptiontable", "co_qualname",
)
_ADDR_RE = re.compile(r"0x[0-9a-fA-F]+")
_REPR = reprlib.Repr()
_REPR.maxstring = 400
_REPR.maxother = 400
_REPR.maxlevel = 12
_REPR.maxlist = 80
_REPR.maxtuple = 80
_REPR.maxdict = 80
_REPR.maxset = 80
_REPR.maxfrozenset = 80


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_repr(value: Any) -> str:
    try:
        text = _REPR.repr(value)
    except BaseException as exc:
        return "<repr-error:%s>" % type(exc).__name__
    text = _ADDR_RE.sub("0xADDR", text)
    return re.sub(r"_sd_[0-9a-f]{12}\.", "", text)


def _qualname(obj: Any) -> str:
    return getattr(obj, "__qualname__", "") or getattr(obj, "__name__", "") or ""


def _module_name(obj: Any) -> str:
    return getattr(obj, "__module__", "") or ""


def _type_name(obj: Any) -> str:
    module = _module_name(obj)
    qualname = _qualname(obj)
    if module.startswith("_sd_"):
        return qualname
    return "%s.%s" % (module, qualname) if module else qualname


def _scalar(value: Any, type_name: str) -> dict:
    return {"t": type_name, "v": value}


def _code_mini(code: types.CodeType) -> dict:
    return {
        "t": "code",
        "name": code.co_name,
        "qualname": getattr(code, "co_qualname", code.co_name),
        "code_sha": _sha_bytes(code.co_code),
        "consts_len": len(code.co_consts),
    }


def canon(value: Any, *, memo: dict[int, str] | None = None, path: str = "$",
          depth: int = 0, oid: list[int] | None = None) -> dict:
    memo = {} if memo is None else memo
    oid = [0] if oid is None else oid
    if value is None:
        return _scalar(None, "NoneType")
    if isinstance(value, bool):
        return _scalar(value, "bool")
    if isinstance(value, int):
        return _scalar(str(value), "int")
    if isinstance(value, float):
        return _scalar(repr(value), "float")
    if isinstance(value, complex):
        return _scalar(repr(value), "complex")
    if isinstance(value, str):
        return _scalar(value, "str")
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _scalar(bytes(value).hex(), "bytes")
    if isinstance(value, type):
        return {"t": "type", "v": _qualname(value)}
    if isinstance(value, types.ModuleType):
        return {"t": "module", "v": getattr(value, "__name__", "?")}
    if isinstance(value, types.FunctionType):
        return {"t": "function", "v": _qualname(value), "name": getattr(value, "__name__", "?")}
    if isinstance(value, (types.BuiltinFunctionType, types.MethodType)):
        return {"t": "builtin", "v": _qualname(value)}
    if isinstance(value, types.CodeType):
        return _code_mini(value)
    if depth >= MAX_DEPTH:
        return {"t": "truncated", "reason": "depth", "value_type": type(value).__name__}
    ident = id(value)
    if ident in memo:
        return {"t": "ref", "v": memo[ident]}
    memo[ident] = path
    if isinstance(value, BaseException):
        return {"t": "exception", "v": exception_info(value, depth=depth + 1, oid=oid)}
    if isinstance(value, dict):
        pairs = []
        for index, (key, item) in enumerate(value.items()):
            ck = canon(key, memo=memo, path="%s.k[%d]" % (path, index), depth=depth + 1, oid=oid)
            cv = canon(item, memo=memo, path="%s.v[%d]" % (path, index), depth=depth + 1, oid=oid)
            pairs.append([ck, cv])
        pairs.sort(key=lambda pair: json.dumps(pair[0], ensure_ascii=False, sort_keys=True))
        return {"t": "dict", "v": pairs, "len": len(pairs)}
    if isinstance(value, (list, tuple)):
        items = [canon(item, memo=memo, path="%s.v[%d]" % (path, index), depth=depth + 1, oid=oid)
                 for index, item in enumerate(value[:MAX_ITEMS])]
        return {"t": "list" if isinstance(value, list) else "tuple", "v": items,
                "len": len(value), "truncated": len(value) > MAX_ITEMS}
    if isinstance(value, (set, frozenset)):
        items = [canon(item, memo=memo, path="%s.v[%d]" % (path, index), depth=depth + 1, oid=oid)
                 for index, item in enumerate(list(value)[:MAX_ITEMS])]
        items.sort(key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
        return {"t": "set" if isinstance(value, set) else "frozenset", "v": items,
                "len": len(value), "truncated": len(value) > MAX_ITEMS}
    oid[0] += 1
    out = {"t": "object", "cls": _type_name(type(value)),
           "oid": oid[0], "repr": _safe_repr(value)}
    try:
        attrs = vars(value)
    except BaseException:
        attrs = None
    if isinstance(attrs, dict):
        out["dict"] = canon(attrs, memo=memo, path=path + ".dict", depth=depth + 1, oid=oid)
    return out


def code_metadata(code: types.CodeType) -> dict:
    out: dict[str, Any] = {}
    for name in CO_FIELDS:
        try:
            value = getattr(code, name)
        except BaseException:
            continue
        if name == "co_consts":
            out[name] = canon(value)
        elif isinstance(value, bytes):
            out[name] = {"len": len(value), "sha256": _sha_bytes(value)}
        else:
            out[name] = value
    return out


def exception_info(exc: BaseException, *, depth: int = 0, oid: list[int] | None = None) -> dict:
    if depth >= MAX_DEPTH:
        return {"type": "truncated", "message": "exception depth limit"}
    out = {"type": _type_name(type(exc)),
           "args": canon(exc.args, depth=depth + 1, oid=oid), "message": str(exc)}
    notes = getattr(exc, "__notes__", None)
    if notes:
        out["notes"] = canon(notes, depth=depth + 1, oid=oid)
    cause = getattr(exc, "__cause__", None)
    context = getattr(exc, "__context__", None)
    if isinstance(cause, BaseException):
        out["cause"] = exception_info(cause, depth=depth + 1, oid=oid)
    if isinstance(context, BaseException) and context is not cause:
        out["context"] = exception_info(context, depth=depth + 1, oid=oid)
    return out


def wrapper_chain(obj: Any) -> list[str]:
    chain, seen, current = [], set(), obj
    for _ in range(8):
        if not callable(current) or id(current) in seen:
            break
        seen.add(id(current))
        chain.append(_qualname(current))
        current = getattr(current, "__wrapped__", None)
        if current is None:
            break
    return chain


def function_metadata(fn: Any) -> dict:
    try:
        sig = str(inspect.signature(fn, follow_wrapped=False))
    except BaseException as exc:
        sig = None
        sig_error = "%s: %s" % (type(exc).__name__, exc)
    else:
        sig_error = None
    out = {
        "kind": "function", "name": getattr(fn, "__name__", None),
        "qualname": _qualname(fn), "doc": canon(getattr(fn, "__doc__", None)),
        "annotations": canon(getattr(fn, "__annotations__", None)),
        "signature": sig, "signature_error": sig_error,
        "defaults": canon(getattr(fn, "__defaults__", None)),
        "kwdefaults": canon(getattr(fn, "__kwdefaults__", None)),
        "dict": canon(getattr(fn, "__dict__", None)),
        "wrapper_chain": wrapper_chain(fn),
    }
    code = getattr(fn, "__code__", None)
    if isinstance(code, types.CodeType):
        out["code"] = code_metadata(code)
    return out


def class_metadata(cls: Any) -> dict:
    return {
        "kind": "class", "name": getattr(cls, "__name__", None),
        "qualname": _qualname(cls), "doc": canon(getattr(cls, "__doc__", None)),
        "annotations": canon(getattr(cls, "__annotations__", None)),
        "dict_keys": sorted(k for k in getattr(cls, "__dict__", {}) if not k.startswith("__")),
    }


def module_metadata(module: types.ModuleType) -> dict:
    return {"kind": "module", "doc": canon(getattr(module, "__doc__", None)),
            "all": canon(getattr(module, "__all__", None))}


def _global_names(module: types.ModuleType, declared: list[str] | None) -> tuple[list[str], bool]:
    if not declared:
        return [], False
    if "*" in declared:
        names = sorted(name for name, value in vars(module).items()
                       if not name.startswith("__") and not isinstance(value, types.ModuleType))
        return names[:MAX_GLOBALS], len(names) > MAX_GLOBALS
    return [name for name in declared if name in vars(module)], False


def module_values(module: types.ModuleType, declared: list[str] | None) -> dict:
    names, _ = _global_names(module, declared)
    return {name: canon(vars(module)[name]) for name in names}


def alias_groups(module: types.ModuleType, declared: list[str] | None) -> list[list[str]]:
    groups: dict[int, list[str]] = {}
    names, _ = _global_names(module, declared)
    for name in names:
        groups.setdefault(id(vars(module)[name]), []).append(name)
    return sorted(sorted(group) for group in groups.values() if len(group) > 1)


def compare_canon(a: Any, b: Any, path: str, tolerance: dict, ignored: set[str],
                  diffs: list[dict], tolerated: list[str]) -> None:
    if path in ignored:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        ta, tb = a.get("t"), b.get("t")
        if ta != tb:
            diffs.append({"path": path, "kind": "type", "original": ta, "product": tb})
            return
        if ta == "float":
            try:
                fa, fb = float(a.get("v")), float(b.get("v"))
            except (TypeError, ValueError):
                pass
            else:
                if math.isnan(fa) and math.isnan(fb):
                    return
                if fa == fb:
                    return
                abs_tol = float(tolerance.get("float_abs_tol", 0.0))
                rel_tol = float(tolerance.get("float_rel_tol", 0.0))
                if abs(fa - fb) <= abs_tol + rel_tol * max(abs(fa), abs(fb)):
                    tolerated.append(path)
                    return
        if ta == "ref":
            if a.get("v") != b.get("v"):
                diffs.append({"path": path, "kind": "alias", "original": a.get("v"), "product": b.get("v")})
            return
        if ta in ("object", "exception"):
            for key in ("cls", "oid", "repr"):
                if a.get(key) != b.get(key):
                    diffs.append({"path": path + "." + key, "kind": "value",
                                  "original": a.get(key), "product": b.get(key)})
                    return
        for key in sorted(set(a) | set(b)):
            if key == "v" and ta == "dict":
                va, vb = a.get("v"), b.get("v")
                if not isinstance(va, list) or not isinstance(vb, list):
                    diffs.append({"path": path + ".v", "kind": "shape", "original": va, "product": vb})
                    continue
                if len(va) != len(vb):
                    diffs.append({"path": path + ".v", "kind": "length", "original": len(va), "product": len(vb)})
                for index in range(min(len(va), len(vb))):
                    compare_canon(va[index], vb[index], "%s.v[%d]" % (path, index),
                                  tolerance, ignored, diffs, tolerated)
                continue
            compare_canon(a.get(key), b.get(key), path + "." + key,
                          tolerance, ignored, diffs, tolerated)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append({"path": path, "kind": "length", "original": len(a), "product": len(b)})
        for index in range(min(len(a), len(b))):
            compare_canon(a[index], b[index], "%s[%d]" % (path, index),
                          tolerance, ignored, diffs, tolerated)
        return
    if a != b:
        diffs.append({"path": path, "kind": "value", "original": a, "product": b})


def _ignore_set(fields: list[str]) -> set[str]:
    out = set()
    for field in fields:
        field = field.strip()
        if not field:
            continue
        out.add(field if field.startswith("$.") else "$.metadata." + field.removeprefix("metadata."))
    return out


def _call_events(events: list[dict], index: int) -> list[dict]:
    return [event for event in events if event.get("call") == index]


def _stream_text(events: list[dict], index: int, kind: str) -> str:
    return "".join(str(event.get("text", "")) for event in events
                   if event.get("call") == index and event.get("kind") == kind)


class _Stream:
    def __init__(self, name: str, target: io.StringIO, events: list[dict], state: dict):
        self.name, self.target, self.events, self.state = name, target, events, state

    def write(self, text: Any) -> int:
        if not isinstance(text, str):
            text = str(text)
        self.target.write(text)
        self.events.append({"call": self.state["call"], "kind": self.name, "text": text})
        return len(text)

    def flush(self) -> None:
        return None

    def isatty(self) -> bool:
        return False

    @property
    def encoding(self) -> str:
        return "utf-8"

    @property
    def errors(self) -> str:
        return "strict"

    def writable(self) -> bool:
        return True

    def readable(self) -> bool:
        return False

    def fileno(self) -> int:
        raise OSError("stream has no fileno")


def _record_fs(workdir: str, events: list[dict], state: dict, path: Any, op: str) -> None:
    if not isinstance(path, (str, bytes, os.PathLike)):
        return
    try:
        relative = os.path.relpath(os.path.abspath(os.fspath(path)), workdir)
    except (TypeError, ValueError, OSError):
        return
    if relative == ".." or relative.startswith(".." + os.sep):
        return
    events.append({"call": state["call"], "kind": "fs", "op": op,
                   "path": relative.replace(os.sep, "/")})


def _install_fs_trace(workdir: str, events: list[dict], state: dict):
    original = (builtins.open, io.open, os.remove, os.unlink, os.rename, os.replace)

    def open_wrap(file, mode="r", *args, **kwargs):
        _record_fs(workdir, events, state, file, "open:" + str(mode))
        return original[0](file, mode, *args, **kwargs)

    def io_open_wrap(file, mode="r", *args, **kwargs):
        _record_fs(workdir, events, state, file, "open:" + str(mode))
        return original[1](file, mode, *args, **kwargs)

    def remove_wrap(path, *args, **kwargs):
        _record_fs(workdir, events, state, path, "remove")
        return original[2](path, *args, **kwargs)

    def unlink_wrap(path, *args, **kwargs):
        _record_fs(workdir, events, state, path, "unlink")
        return original[3](path, *args, **kwargs)

    def rename_wrap(src, dst, *args, **kwargs):
        _record_fs(workdir, events, state, src, "rename-src")
        _record_fs(workdir, events, state, dst, "rename-dst")
        return original[4](src, dst, *args, **kwargs)

    def replace_wrap(src, dst, *args, **kwargs):
        _record_fs(workdir, events, state, src, "replace-src")
        _record_fs(workdir, events, state, dst, "replace-dst")
        return original[5](src, dst, *args, **kwargs)

    builtins.open, io.open = open_wrap, io_open_wrap
    os.remove, os.unlink, os.rename, os.replace = remove_wrap, unlink_wrap, rename_wrap, replace_wrap

    def restore() -> None:
        builtins.open, io.open, os.remove, os.unlink, os.rename, os.replace = original

    return restore
def snapshot_tree(root: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in ("__pycache__", ".tmp"))
        for filename in sorted(filenames):
            path = os.path.join(dirpath, filename)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            try:
                out[rel] = {"size": os.path.getsize(path), "sha256": _sha_file(path)}
            except OSError:
                continue
    return out


def _seed_files(root: str, files: dict | None) -> None:
    for rel, content in (files or {}).items():
        clean = str(rel).replace("\\", "/").lstrip("/")
        if not clean or ".." in clean.split("/"):
            raise ValueError("unsafe sandbox file path: %r" % rel)
        path = os.path.join(root, clean)
        os.makedirs(os.path.dirname(path) or root, exist_ok=True)
        if isinstance(content, dict) and "base64" in content:
            data = base64.b64decode(content["base64"])
        else:
            data = str(content).encode("utf-8")
        with open(path, "wb") as fh:
            fh.write(data)


def _scrub(value: Any, replacements: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        for old, new in replacements:
            if old:
                value = value.replace(old, new).replace(old.replace("\\", "/"), new)
        return value
    if isinstance(value, list):
        return [_scrub(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item, replacements) for item in value)
    if isinstance(value, dict):
        return {_scrub(key, replacements): _scrub(item, replacements) for key, item in value.items()}
    return value


def _load_target(target: dict) -> tuple[types.ModuleType, Any, str]:
    path = os.path.abspath(target["path"])
    kind = target["kind"]
    module_name = target.get("module_name") or ("_sd_" + _sha_bytes(path.encode("utf-8"))[:12])
    if target.get("package_root"):
        sys.path.insert(0, os.path.abspath(target["package_root"]))
    if kind == "source":
        loader = importlib.machinery.SourceFileLoader(module_name, path)
    elif kind == "pyc":
        loader = importlib.machinery.SourcelessFileLoader(module_name, path)
    else:
        raise ValueError("unknown target kind: %r" % kind)
    spec = importlib.util.spec_from_file_location(module_name, path, loader=loader)
    if spec is None:
        raise ImportError("cannot create module spec for %s" % path)
    if os.path.basename(path).startswith("__init__."):
        spec.submodule_search_locations = [os.path.dirname(path)]
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, spec.loader, module_name


def _entrypoint(module: types.ModuleType, spec: str | None) -> tuple[str, Any]:
    if not spec or spec == "module":
        return "module", module
    kind, name = spec.split(":", 1) if ":" in spec else ("function", spec)
    obj: Any = module
    for part in name.split("."):
        obj = getattr(obj, part)
    return kind, obj


def _codes_for(target: Any, kind: str) -> set[types.CodeType]:
    codes: set[types.CodeType] = set()
    if kind == "class" and inspect.isclass(target):
        for name in ("__init__", "__new__"):
            code = getattr(getattr(target, name, None), "__code__", None)
            if isinstance(code, types.CodeType):
                codes.add(code)
        return codes
    if kind == "module":
        return codes
    current, seen = target, set()
    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        code = getattr(current, "__code__", None)
        if isinstance(code, types.CodeType):
            codes.add(code)
        current = getattr(current, "__wrapped__", None)
        if current is None:
            break
    return codes


def _invoke(target: Any, kind: str, args: list, kwargs: dict) -> Any:
    if kind == "class" and inspect.isclass(target):
        return target(*args, **kwargs)
    if inspect.iscoroutinefunction(target):
        return asyncio.run(target(*args, **kwargs))
    if inspect.isasyncgenfunction(target):
        async def consume() -> list:
            return [item async for item in target(*args, **kwargs)]
        return asyncio.run(consume())
    if inspect.isgeneratorfunction(target):
        return list(target(*args, **kwargs))
    return target(*args, **kwargs)


def _bindings(target: Any, kind: str, calls: list[dict]) -> tuple[bool | None, list[dict]]:
    if kind == "module":
        return None, []
    try:
        sig = inspect.signature(target, follow_wrapped=False)
    except BaseException as exc:
        return None, [{"ok": None, "error": "%s: %s" % (type(exc).__name__, exc)}]
    rows, all_ok = [], True
    for call in calls:
        try:
            sig.bind(*call.get("args", []), **call.get("kwargs", {}))
            rows.append({"ok": True})
        except BaseException as exc:
            all_ok = False
            rows.append({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)})
    return all_ok, rows


def _run_worker(payload_path: str) -> int:
    with open(payload_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    workdir = os.path.abspath(payload["workdir"])
    result_path = payload["result_path"]
    os.makedirs(workdir, exist_ok=True)
    os.chdir(workdir)
    os.makedirs(os.path.join(workdir, ".tmp"), exist_ok=True)
    _seed_files(workdir, payload.get("files"))
    events: list[dict] = []
    state = {"call": -1}
    stdout, stderr = io.StringIO(), io.StringIO()
    original_stdout, original_stderr = sys.stdout, sys.stderr
    result: dict[str, Any] = {
        "tool": "semantic_diff", "version": TOOL_VERSION, "side": payload.get("side"),
        "ok": False, "phase": "load", "events": events, "call_results": [],
        "files_initial": snapshot_tree(workdir), "files_final": {},
        "module_values": {}, "aliases": [], "metadata": None,
        "signature_binding": None, "signature_bindings": [], "body_reached": False,
        "error": None, "harness_error": False,
    }
    restore_fs = None
    try:
        random.seed(payload.get("seed", 0))
        sys.stdout = _Stream("stdout", stdout, events, state)
        sys.stderr = _Stream("stderr", stderr, events, state)
        restore_fs = _install_fs_trace(workdir, events, state)
        module, loader, module_name = _load_target(payload["target"])
        try:
            kind, entry = _entrypoint(module, payload.get("entrypoint"))
        except BaseException as exc:
            result["phase"] = "entrypoint"
            raise exc
        calls = payload.get("calls")
        if calls is None:
            calls = [{"args": payload.get("args", []), "kwargs": payload.get("kwargs", {}),
                      "label": payload.get("label", "call0")}]
        binding, bindings = _bindings(entry, kind, calls)
        result["signature_binding"] = binding
        result["signature_bindings"] = bindings
        result["phase"] = "call"
        codes = _codes_for(entry, kind)
        hit = {"value": False}

        def tracer(frame, event, arg):
            if event == "call" and frame.f_code in codes:
                hit["value"] = True
            return tracer

        old_trace = sys.gettrace()
        sys.settrace(tracer)
        call_exprs = [str(expr) for expr in (payload.get("call_exprs") or [])
                      if isinstance(expr, str) and expr.strip()]
        try:
            if kind == "module":
                hit["value"] = True
                result["ok"] = True
                # input_model.calls (Task 1.1): call expressions evaluated in the
                # module namespace so R1-R6 observe real invocations instead of a
                # module-only import.
                for index, expr in enumerate(call_exprs):
                    state["call"] = index
                    row = {
                        "index": index, "label": expr, "expr": expr,
                        "input_before": None, "input_after": None,
                        "ok": False, "return": None,
                        "exception": None, "stdout": "", "stderr": "", "events": [],
                    }
                    try:
                        returned = eval(compile(expr, "<call_expr:%d>" % index, "eval"),
                                        vars(module))
                        row["ok"] = True
                        row["return"] = canon(returned)
                    except BaseException as exc:
                        row["exception"] = exception_info(exc)
                    row["stdout"] = _stream_text(events, index, "stdout")
                    row["stderr"] = _stream_text(events, index, "stderr")
                    row["events"] = _call_events(events, index)
                    result["call_results"].append(row)
            else:
                for index, call in enumerate(calls):
                    state["call"] = index
                    args = call.get("args", [])
                    kwargs = call.get("kwargs", {})
                    row = {
                        "index": index, "label": call.get("label", "call%d" % index),
                        "args": [canon(arg) for arg in args], "kwargs": canon(kwargs),
                        "input_before": {"args": canon(args), "kwargs": canon(kwargs)},
                        "input_after": None, "ok": False, "return": None,
                        "exception": None, "stdout": "", "stderr": "", "events": [],
                    }
                    try:
                        returned = _invoke(entry, kind, args, kwargs)
                        row["ok"] = True
                        row["return"] = canon(returned)
                        if kind == "class" and inspect.isclass(entry):
                            hit["value"] = True
                    except BaseException as exc:
                        row["exception"] = exception_info(exc)
                    row["input_after"] = {"args": canon(args), "kwargs": canon(kwargs)}
                    row["stdout"] = _stream_text(events, index, "stdout")
                    row["stderr"] = _stream_text(events, index, "stderr")
                    row["events"] = _call_events(events, index)
                    result["call_results"].append(row)
                result["ok"] = True
        finally:
            sys.settrace(old_trace)
        result["body_reached"] = bool(hit["value"])
        if kind == "module":
            metadata = module_metadata(module)
            try:
                metadata["code"] = code_metadata(loader.get_code(module_name))
            except BaseException as exc:
                metadata["code_error"] = "%s: %s" % (type(exc).__name__, exc)
            result["metadata"] = metadata
        elif isinstance(entry, type):
            result["metadata"] = class_metadata(entry)
        else:
            result["metadata"] = function_metadata(entry)
        declared = payload.get("observe_globals")
        if declared is None:
            declared = ["*"]
        _, globals_truncated = _global_names(module, declared)
        result["globals_truncated"] = globals_truncated
        result["module_values"] = module_values(module, declared)
        result["aliases"] = alias_groups(module, declared)
        result["files_final"] = snapshot_tree(workdir)
        result["import_events"] = _call_events(events, -1)
        result["import_stdout"] = _stream_text(events, -1, "stdout")
        result["import_stderr"] = _stream_text(events, -1, "stderr")
    except BaseException as exc:
        result["error"] = exception_info(exc)
        result["traceback"] = traceback.format_exc(limit=8)
        if not isinstance(exc, (ImportError, AttributeError, NameError, TypeError, ValueError,
                                RuntimeError, SyntaxError, OSError)):
            result["harness_error"] = True
    finally:
        if restore_fs is not None:
            restore_fs()
        sys.stdout, sys.stderr = original_stdout, original_stderr
        if not result.get("files_final"):
            try:
                result["files_final"] = snapshot_tree(workdir)
            except BaseException:
                pass
        result["stdout"] = stdout.getvalue()
        result["stderr"] = stderr.getvalue()
        result = _scrub(result, [
            (workdir, "<cwd>"), (os.path.realpath(workdir), "<cwd>"),
            (os.path.dirname(os.path.abspath(result_path)), "<harness>"),
        ])
        with open(result_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    return 0


def _run_side(case: dict, side: str, sandbox: str, harness: str) -> dict:
    target = case[side]
    if not target.get("path"):
        return {"side": side, "ok": False, "harness_error": True,
                "error": {"message": "missing target path"}}
    payload = {
        "side": side, "target": target, "entrypoint": case.get("entrypoint"),
        "calls": case.get("calls"), "args": case.get("args", []),
        "kwargs": case.get("kwargs", {}), "observe_globals": case.get("observe_globals"),
        "files": case.get("files"), "workdir": sandbox, "seed": case.get("seed", 0),
        "call_exprs": case.get("call_exprs"),
    }
    payload_path = os.path.join(harness, "payload-%s.json" % side)
    result_path = os.path.join(harness, "result-%s.json" % side)
    payload["result_path"] = result_path
    with open(payload_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    _seed_files(sandbox, case.get("files"))
    env = os.environ.copy()
    env.update({
        "PYTHONHASHSEED": str(case.get("seed", 0)), "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8", "TZ": "UTC",
        "TMPDIR": os.path.join(sandbox, ".tmp"), "TEMP": os.path.join(sandbox, ".tmp"),
        "TMP": os.path.join(sandbox, ".tmp"),
    })
    command = [sys.executable, "-B", "-X", "utf8", os.path.abspath(__file__),
               "--worker", payload_path]
    timeout = float(case.get("timeout_s", DEFAULT_TIMEOUT_S))
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=sandbox, env=env, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {"side": side, "ok": False, "timeout": True,
                "elapsed_s": round(time.monotonic() - started, 4),
                "stdout": exc.stdout or "", "stderr": exc.stderr or "",
                "harness_error": False}
    if not os.path.isfile(result_path):
        return {"side": side, "ok": False, "harness_error": True,
                "returncode": completed.returncode, "stdout": completed.stdout,
                "stderr": completed.stderr,
                "error": {"message": "worker produced no result", "returncode": completed.returncode},
                "elapsed_s": round(time.monotonic() - started, 4)}
    with open(result_path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    result["returncode"] = completed.returncode
    result["elapsed_s"] = round(time.monotonic() - started, 4)
    return result


def _resolve_case_paths(case: dict, base: str) -> dict:
    resolved = dict(case)
    for side in ("original", "product"):
        target = resolved.get(side)
        if not isinstance(target, dict):
            continue
        target = dict(target)
        for key in ("path", "source", "pyc", "package_root"):
            if target.get(key) and not os.path.isabs(target[key]):
                target[key] = os.path.abspath(os.path.join(base, target[key]))
        if target.get("pyc") and not target.get("path"):
            target["path"], target["kind"] = target["pyc"], "pyc"
        elif target.get("source") and not target.get("path"):
            target["path"], target["kind"] = target["source"], "source"
        if target.get("path") and not target.get("kind"):
            target["kind"] = "pyc" if str(target["path"]).lower().endswith(".pyc") else "source"
        resolved[side] = target
    return resolved


def _add_diff(diffs: list[dict], dimension: str, message: str, detail: Any = None) -> None:
    item = {"dimension": dimension, "message": message}
    if detail is not None:
        item["detail"] = detail
    diffs.append(item)


def _mark(diffs: list[dict], start: int, dimension: str) -> None:
    for item in diffs[start:]:
        item["dimension"] = dimension


def _unregistered_r7_ignores(fields: list[str]) -> list[str]:
    """Fields whose ignore path would silence a protected code-object comparison.

    A path is rejected when it names a protected field at any depth or when it
    is an ancestor of one (e.g. `$.metadata.code`, `$.metadata`, `$`).
    """
    bad: list[str] = []
    for field in fields:
        text = str(field).strip()
        if not text:
            continue
        path = text if text.startswith("$.") else "$.metadata." + text.removeprefix("metadata.")
        if any(segment in PROTECTED_METADATA_FIELDS for segment in path.split(".")):
            bad.append(text)
            continue
        for protected in PROTECTED_METADATA_FIELDS:
            full = "$.metadata.code." + protected
            if path == full or path.startswith(full + ".") or full.startswith(path + "."):
                bad.append(text)
                break
    return bad


def judge_case(case: dict, original: dict, product: dict, include_observations: bool = False) -> dict:
    tolerance = dict(case.get("tolerance") or {})
    custom_ignores = [str(field) for field in (tolerance.get("ignore_metadata_fields") or [])]
    unregistered = _unregistered_r7_ignores(custom_ignores)
    if unregistered:
        return _result(case, ERROR, [], [], [], original, product, include_observations,
                       errors=["unregistered R7 tolerance (protected code-object fields): "
                               + ", ".join(sorted(unregistered))])
    applied_ignores = _ignore_set(custom_ignores)
    ignored = _ignore_set(list(DEFAULT_METADATA_IGNORE)) | applied_ignores
    tolerated: list[str] = []
    diffs: list[dict] = []
    inconclusive: list[str] = []
    errors: list[str] = []

    # Task 1.3: a timeout on either side is INCONCLUSIVE, never EQUAL/DIFFERENT
    # and never coverage.
    if original.get("timeout"):
        inconclusive.append("original execution timed out")
        return _result(case, INCONCLUSIVE, diffs, inconclusive, tolerated, original, product,
                       include_observations, applied_ignores=applied_ignores)
    if not original.get("ok"):
        if original.get("harness_error"):
            errors.append("original worker/harness error")
        else:
            errors.append("original artifact did not load/execute")
    if errors:
        return _result(case, ERROR, diffs, inconclusive, tolerated, original, product,
                       include_observations, errors, applied_ignores=applied_ignores)

    if product.get("timeout"):
        inconclusive.append("product execution timed out")
        return _result(case, INCONCLUSIVE, diffs, inconclusive, tolerated, original, product,
                       include_observations, applied_ignores=applied_ignores)
    if not product.get("ok"):
        if product.get("harness_error"):
            errors.append("product worker/harness error")
        else:
            _add_diff(diffs, "LOAD", "product failed to load/execute", product.get("error"))
    orig_binding, prod_binding = original.get("signature_binding"), product.get("signature_binding")
    if orig_binding is False:
        inconclusive.append("original signature binding failed")
    if prod_binding is False and orig_binding is not False:
        _add_diff(diffs, "R7", "product signature cannot bind documented input",
                  {"bindings": product.get("signature_bindings")})
    if not original.get("body_reached"):
        inconclusive.append("original body not reached")
    if not product.get("body_reached") and original.get("body_reached"):
        _add_diff(diffs, "R0", "product entrypoint body not reached")
    if original.get("globals_truncated") or product.get("globals_truncated"):
        inconclusive.append("module globals exceeded observation limit")

    if original.get("metadata") is not None and product.get("metadata") is not None:
        start = len(diffs)
        compare_canon(original["metadata"], product["metadata"], "$.metadata",
                      tolerance, ignored, diffs, tolerated)
        _mark(diffs, start, "R7")
    start = len(diffs)
    compare_canon(original.get("module_values"), product.get("module_values"),
                  "$.module_values", tolerance, set(), diffs, tolerated)
    compare_canon(original.get("aliases"), product.get("aliases"),
                  "$.aliases", tolerance, set(), diffs, tolerated)
    _mark(diffs, start, "R5")

    ocalls, pcalls = original.get("call_results") or [], product.get("call_results") or []
    if len(ocalls) != len(pcalls):
        _add_diff(diffs, "R0", "call count differs",
                  {"original": len(ocalls), "product": len(pcalls)})
    for index in range(min(len(ocalls), len(pcalls))):
        ocall, pcall = ocalls[index], pcalls[index]
        if ocall.get("ok") and pcall.get("ok"):
            start = len(diffs)
            compare_canon(ocall.get("return"), pcall.get("return"),
                          "$.call[%d].return" % index, tolerance, set(), diffs, tolerated)
            _mark(diffs, start, "R1")
        elif ocall.get("ok") != pcall.get("ok"):
            _add_diff(diffs, "R6", "one side raised while the other returned",
                      {"original_exception": ocall.get("exception"),
                       "product_exception": pcall.get("exception")})
        else:
            start = len(diffs)
            compare_canon(ocall.get("exception"), pcall.get("exception"),
                          "$.call[%d].exception" % index, tolerance, set(), diffs, tolerated)
            _mark(diffs, start, "R6")
        if ocall.get("stdout") != pcall.get("stdout"):
            _add_diff(diffs, "R2", "stdout differs",
                      {"call": index, "original": ocall.get("stdout"), "product": pcall.get("stdout")})
        if ocall.get("stderr") != pcall.get("stderr"):
            _add_diff(diffs, "R3", "stderr differs",
                      {"call": index, "original": ocall.get("stderr"), "product": pcall.get("stderr")})
        if ocall.get("events") != pcall.get("events"):
            _add_diff(diffs, "R4", "ordered events differ", {"call": index})
        start = len(diffs)
        compare_canon(ocall.get("input_after"), pcall.get("input_after"),
                      "$.call[%d].input_after" % index, tolerance, set(), diffs, tolerated)
        _mark(diffs, start, "R5")

    if original.get("import_stdout") != product.get("import_stdout"):
        _add_diff(diffs, "R2", "import stdout differs",
                  {"original": original.get("import_stdout"), "product": product.get("import_stdout")})
    if original.get("import_stderr") != product.get("import_stderr"):
        _add_diff(diffs, "R3", "import stderr differs",
                  {"original": original.get("import_stderr"), "product": product.get("import_stderr")})
    if original.get("import_events") != product.get("import_events"):
        _add_diff(diffs, "R4", "import events differ")
    if (original.get("files_initial") or {}) != (product.get("files_initial") or {}):
        _add_diff(diffs, "R0", "sandbox seed state differs")
    if (original.get("files_final") or {}) != (product.get("files_final") or {}):
        start = len(diffs)
        compare_canon(original.get("files_final"), product.get("files_final"),
                      "$.files", tolerance, set(), diffs, tolerated)
        _mark(diffs, start, "R5")

    if errors:
        return _result(case, ERROR, diffs, inconclusive, tolerated, original, product,
                       include_observations, errors, applied_ignores=applied_ignores)
    if diffs:
        return _result(case, DIFFERENT, diffs, inconclusive, tolerated, original, product,
                       include_observations, applied_ignores=applied_ignores)
    if inconclusive:
        return _result(case, INCONCLUSIVE, diffs, inconclusive, tolerated, original, product,
                       include_observations, applied_ignores=applied_ignores)
    return _result(case, EQUAL, diffs, inconclusive, tolerated, original, product,
                   include_observations, applied_ignores=applied_ignores)


def _result(case: dict, status: str, diffs: list[dict], inconclusive: list[str],
            tolerated: list[str], original: dict, product: dict, include_observations: bool,
            errors: list[str] | None = None, applied_ignores: set[str] | None = None) -> dict:
    out = {
        "case_id": case.get("case_id") or case.get("id") or "case", "status": status,
        "diffs": diffs, "inconclusive": inconclusive, "errors": errors or [],
        "tolerances": sorted(set(tolerated) | _ignore_set(list(DEFAULT_METADATA_IGNORE))
                             | (applied_ignores or set())),
    }
    if include_observations:
        out["observations"] = {"original": original, "product": product}
    return out


def compare_case(case: dict, include_observations: bool = False) -> dict:
    base = case.get("_base") or os.getcwd()
    case = _resolve_case_paths(case, base)
    missing = [side for side in ("original", "product") if not case.get(side, {}).get("path")]
    if missing:
        return {"case_id": case.get("case_id", "case"), "status": ERROR,
                "errors": ["missing target: " + ",".join(missing)], "diffs": [],
                "inconclusive": [], "tolerances": []}
    for side in ("original", "product"):
        path = case[side]["path"]
        if not os.path.isfile(path):
            return {"case_id": case.get("case_id", "case"), "status": ERROR,
                    "errors": ["target not found: " + path], "diffs": [],
                    "inconclusive": [], "tolerances": []}
    temporary = tempfile.mkdtemp(prefix="semantic_diff_")
    try:
        original_dir = os.path.join(temporary, "original")
        product_dir = os.path.join(temporary, "product")
        harness = os.path.join(temporary, "harness")
        for path in (original_dir, product_dir, harness):
            os.makedirs(path, exist_ok=True)
        original = _run_side(case, "original", original_dir, harness)
        product = _run_side(case, "product", product_dir, harness)
        return judge_case(case, original, product, include_observations)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def load_cases(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as fh:
        text = fh.read()
    if path.lower().endswith(".jsonl"):
        cases = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
        cases = data if isinstance(data, list) else [data]
    base = os.path.dirname(os.path.abspath(path))
    for case in cases:
        case["_base"] = base
    return cases


def _summary(results: list[dict]) -> dict:
    counts = {status: 0 for status in (EQUAL, DIFFERENT, INCONCLUSIVE, ERROR)}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {"total": len(results), **counts}


def _exit_code(results: list[dict]) -> int:
    if any(result["status"] == ERROR for result in results):
        return 3
    if any(result["status"] == INCONCLUSIVE for result in results):
        return 2
    if any(result["status"] == DIFFERENT for result in results):
        return 1
    return 0


def _write_results(path: str, results: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    if path.lower().endswith(".jsonl"):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            for result in results:
                fh.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    else:
        payload = {"tool": "semantic_diff", "version": TOOL_VERSION,
                   "summary": _summary(results), "results": results}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
            fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--case", help="single case JSON file")
    parser.add_argument("--cases", help="case JSON/JSONL file")
    parser.add_argument("--out", help="result JSON/JSONL path")
    parser.add_argument("--include-observations", action="store_true")
    parser.add_argument("--allow-non-equal", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    if args.worker:
        return _run_worker(args.worker)
    if bool(args.case) == bool(args.cases):
        parser.error("provide exactly one of --case or --cases")
    cases = load_cases(args.case or args.cases)
    results = [compare_case(case, args.include_observations) for case in cases]
    if args.out:
        _write_results(args.out, results)
        print(json.dumps({"tool": "semantic_diff", "summary": _summary(results)},
                         ensure_ascii=False))
    elif len(results) == 1 and cases and "case_id" not in cases[0]:
        print(json.dumps(results[0], ensure_ascii=False, indent=1))
    else:
        print(json.dumps({"tool": "semantic_diff", "version": TOOL_VERSION,
                          "summary": _summary(results), "results": results},
                         ensure_ascii=False, indent=1))
    return 0 if args.allow_non_equal else _exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
