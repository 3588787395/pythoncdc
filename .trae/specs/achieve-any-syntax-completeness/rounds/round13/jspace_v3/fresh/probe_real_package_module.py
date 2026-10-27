#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Triage whether a real-package pyc can execute in the current interpreter.

This is **not** a J v3 coverage witness.  It only answers the dependency
question "does the module body import/execute here?" so that the 376
real-package entries can be audited.  It executes the real module body in the
current user context and a temporary working directory; it is not an OS
sandbox.  Do not feed its OK/FAIL result into the coverage numerator.

Run from the repository root:

    python -X utf8 .../fresh/probe_real_package_module.py \
      --root . --deps D:\\temp\\opencode\\j3deps \
      --pyc site-packages/fly/common/aes_encrypt.pyc \
      --name fly.common.aes_encrypt

Exit code 0: module body executed; 1: module body raised; 2: usage/read error.
"""

from __future__ import annotations

import argparse
import marshal
import os
import sys
import tempfile
import traceback
import types


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.getcwd(),
                        help="repository root (default: current directory)")
    parser.add_argument("--deps", default=os.environ.get("J3_DEPS", ""),
                        help="extra dependency directory (optional)")
    parser.add_argument("--pyc", required=True, help="path to the real-package pyc")
    parser.add_argument("--name", required=True, help="import name used by the loader")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    pyc = os.path.abspath(args.pyc)
    deps = os.path.abspath(args.deps) if args.deps else ""
    try:
        with open(pyc, "rb") as fh:
            data = fh.read()
        code = marshal.loads(data[16:])
    except (OSError, ValueError, EOFError) as exc:
        print("READ-FAIL %s %s: %s" % (args.name, type(exc).__name__, exc))
        return 2

    paths = [os.path.join(root, "site-packages"), root]
    if deps:
        paths.insert(0, deps)
    sys.path[:0] = [path for path in paths if os.path.isdir(path)]
    os.chdir(tempfile.mkdtemp(prefix="j3probe_"))

    class Loader:
        def get_code(self, fullname):
            return code

        def get_source(self, fullname):
            return None

    module = types.ModuleType(args.name)
    module.__file__ = pyc
    module.__loader__ = Loader()
    module.__package__ = args.name.rpartition(".")[0]
    module.__spec__ = None
    try:
        exec(code, module.__dict__)
        print("OK %s globals %d" % (args.name, len(module.__dict__)))
        return 0
    except BaseException as exc:  # noqa: BLE001 - triage must report every failure
        print("FAIL %s %s: %s" % (args.name, type(exc).__name__, exc))
        traceback.print_exc(limit=4)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
