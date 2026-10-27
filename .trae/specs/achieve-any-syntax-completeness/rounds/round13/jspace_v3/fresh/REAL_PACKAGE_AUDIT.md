# Real-package exclusions: 376 entries, 7 pycs (audit, rr-v5r76)

## Scope and result

The official J v3 space still has **376 excluded entries**:

| Reading | Value |
|---|---:|
| `J_total` | 1556 |
| `covered_5tuple` | 1180 |
| `excluded` | 376 |
| `uncovered` | 376 |
| `semantic_failures` | 0 |
| `green` | 1180 |
| `coverage_pct` | 75.84% |
| Judge SHA256 | `dbcb1e246dd549f2c66a1d779f31eba0506f9c99364db02a679523dde84d8174` |

This audit answers whether any of the 376 can be honestly moved into the
numerator **without** changing the judgment space, synthesising a wrapper
source, or treating a module import as semantic coverage.

**Result: 0 of 376 can be honestly closed in the current Windows environment.**
The audit does not change the space, the evidence, or the readings.  G1 remains
**FAIL/BLOCKED**.

Evidence:

- `REAL_PACKAGE_AUDIT.json` — machine-readable inventory, probe results, all
  376 per-entry reasons, and the unchanged readings.
- `audit_real_packages.py` — regenerates the JSON (deterministic without
  `--run-probes` once the probe block is archived).
- `probe_real_package_module.py` — dependency-triage probe only; **not** a
  coverage witness.

## Inventory

The 376 entries map to only **7 real-package pycs**:

| pyc | entries | bytes | SHA256 | probe |
|---|---:|---:|---|---|
| `site-packages/IQCommon/util/trade_info_utils.pyc` | 203 | 83014 | `5419f2a32c808d9bb23969dfb559e455609cd0408e6d65a0f43984cce7dc2595` | FAIL |
| `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 42 | 212327 | `34dbb235b6372e67d3098273006bb1ec1428b868252106d6faa19499c9f329d7` | FAIL |
| `site-packages/IQEngine/utils/scheduler.pyc` | 39 | 41237 | `9d6abeaad7a3e4aa517f3c7933e30523164c778cd8cff0ba2fdb62f5697db018` | FAIL |
| `site-packages/fly/data/quote_handler.pyc` | 28 | 73417 | `1bfaa1f6e75cc34e38d2558d92e0552dfaa4e94fc2aabc17a16223b0044e5aeb` | FAIL |
| `site-packages/IQEngine/plugins/plugin_system_trade/function.pyc` | 27 | 92306 | `b67c0b5dfb1e681d0999055add7b7843af6462c09c83f4eb6653e84a183f0e9b` | FAIL |
| `site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc` | 25 | 21828 | `59cb762398a9ed5289dff9f5c3def994d8a1dbd80024f3119f3800a640f0ca4e` | FAIL |
| `site-packages/fly/common/aes_encrypt.pyc` | 12 | 6883 | `f8901bc60109b49bc2a27baad5a2658e94696fe99e7ed0c3488fb5b551759412` | **OK** |

Entry counts by host:

| host | entries |
|---|---:|
| `if-arm` | 61 |
| `function-body` | 45 |
| `loop-body` | 44 |
| `else-arm` | 38 |
| `try-body` | 34 |
| `except-handler` | 29 |
| `call-arg` | 25 |
| `subscript-index` | 24 |
| `assign-rhs` | 22 |
| `with-body` | 19 |
| `module-level` | 10 |
| `return-value-expr` | 7 |
| `boolop-operand` | 6 |
| `class-body` | 6 |
| `decorator-expr` | 4 |
| `else-of-try` | 2 |

**364 entries** carry a registered “专属见证探针” note (`tiu`, `tlb`, `sched`,
`qh`, `fn`, `live`).  Those probes are **byte-identical staged copies** of the
same real pyc used by `pyc_verify`; they are not call witnesses.  The remaining
**12 entries** (`aes_encrypt.pyc`) explicitly say “本单元尚无专属探针 … 需新造专属探针”.

## Probe method and results

The probe executes the real module body with the repository `site-packages` and
the optional dependency directory on `sys.path`, in a temporary working
directory:

```powershell
python -X utf8 .../fresh/probe_real_package_module.py `
  --root . --deps D:\temp\opencode\j3deps `
  --pyc site-packages/<path>.pyc `
  --name <dotted.module.name>
```

Environment: CPython **3.11.7** (Windows, 64-bit).  Extra dependency directory
`D:\temp\opencode\j3deps` contains `logbook 1.10.1`, `typing_extensions 4.16.0`,
`tornado 6.6`, `pyzmq 27.2.0`, `jsonpickle 4.1.4`; the system interpreter also
provides `six 1.17.0`, `pandas 3.0.3`, `numpy 2.4.4`, `pytz 2026.2`.

Six of the seven pycs fail at the same import chain:

```text
ModuleNotFoundError: No module named 'IQCommon.data.TickDataCache'
  .../IQCommon/common/__init__.py line 8
  .../IQCommon/common/main.py line 92
  .../IQEngine/utils/scheduler.py line 17      (or the equivalent importer)
```

The missing modules are Linux-only extension files:

```text
site-packages/IQCommon/data/TickDataCache.cpython-311-x86_64-linux-gnu.so
site-packages/IQCommon/data/L2DataCache.cpython-311-x86_64-linux-gnu.so
site-packages/IQCommon/data/ReferenceCache.cpython-311-x86_64-linux-gnu.so
```

Windows CPython cannot load ELF `.so` files.  WSL is not installed (`wsl.exe
--status` exits 50 and prints the install help), and neither Docker nor podman is
available.  Installing a Linux runtime is outside this round; no `.pyd` or
Windows build of these proprietary modules is present.

`aes_encrypt.pyc` is the only module that executes: `OK fly.common.aes_encrypt
globals 22`.  It has no import-time side effect beyond defining its constants,
class, and two functions.

### Why stubbing is rejected

Pre-populating `IQCommon.data.TickDataCache` (or the other `.so` modules) with a
synthetic module would change the globals observed by the original module and by
the product source, and would bypass the safety gate that exists precisely
because these are pyc-only business modules with process/network/trading
surface.  A stub would not be a faithful original-vs-product witness and is not
used.

## The ten module-level entries

The module-code witness used for `m06`/`m08`/`m04` is valid only when the
`p_j` source actually contains the claimed top-level host/variant.  For the ten
real-package `module-level` entries the audit finds:

| id | pyc | variant | dedicated probe | `p_j` contains claimed host | reason |
|---|---|---|---:|---:|---|
| `JS-IMPORT-001` | `trade_info_utils.pyc` | `import-plain` | yes | yes (24 top-level imports) | `pyc_import_blocked` |
| `JS-IMPORT-021` | `trade_info_utils.pyc` | `import-from` | yes | yes (24 top-level imports) | `pyc_import_blocked` |
| `JS-IMPORT-029` | `trade_info_utils.pyc` | `import-from-as` | yes | yes (24 top-level imports) | `pyc_import_blocked` |
| `JS-IMPORT-015` | `trade_live_broker.pyc` | `import-as` | yes | yes (30 top-level imports) | `pyc_import_blocked` |
| `JS-DECORATOR-004` | `scheduler.pyc` | `deco-on-function` | yes | yes (4 top-level decorated functions) | `pyc_import_blocked` |
| `JS-DECORATOR-014` | `scheduler.pyc` | `deco-single` | yes | yes (4 top-level decorated functions) | `pyc_import_blocked` |
| `JS-DECORATOR-019` | `scheduler.pyc` | `deco-with-args` | yes | yes (4 top-level decorated functions) | `pyc_import_blocked` |
| `JS-TRY-020` | `live.pyc` | `try-with-handler` | yes | yes (1 top-level `try`) | `pyc_import_blocked` |
| `JS-TRY-057` | `live.pyc` | `try-handler-typed` | yes | yes (1 top-level `try`) | `pyc_import_blocked` |
| `JS-DECORATOR-009` | `aes_encrypt.pyc` | `deco-on-class` | **no** | **no** | `p_j_lacks_claimed_host` |

- **Nine entries** are structurally present in `p_j` but blocked by the Linux
  `.so` chain.  If a matching Linux runtime and an audited sandbox were
  available, the module-code witness would be the right model for these nine;
  it is not run here and they stay excluded.
- **`JS-DECORATOR-009`** is the only executable pyc, but the `p_j` source has
  **no class decorator**:
  - top-level `class DES_ENCRYPT` has `decorator_list == []`;
  - only the methods `encrypt` and `decrypt` have `@staticmethod`.
  Module execution would apply `@staticmethod` during class-body execution
  (a function decorator in a class body), not a `deco-on-class` at
  `module-level`.  Running the module and calling it `EQUAL` would be a false
  positive.  The entry’s own note says the cited path “仅证明该形态族在仓内存在
  … 不证明本单元的宿主/深度/变体组合；需新造专属探针”.  It stays excluded.

## The 366 non-module-level entries

A module-code witness re-executes the module body; it does not execute a
`function-body`, `if-arm`, `loop-body`, `except-handler`, `call-arg`, etc.
Those hosts require host-specific call expressions (and, for branches and
handlers, inputs that reach the host).  The audit therefore does not count
module execution for any of the 366.

Breakdown:

| group | entries | status |
|---|---:|---|
| 6 blocked pycs, dedicated probe registered | 355 | `pyc_import_blocked`; host-specific calls still required after a Linux runtime exists |
| `aes_encrypt.pyc` | 11 | no dedicated probe; all are `Decorator` structural placeholders; `p_j` has only method-level `@staticmethod` (host `class-body`); claimed `decorator-expr`/`function-body`/`call-arg` hosts absent |
| total | 366 | 0 closable now |

The 12 `aes_encrypt` entries are all `Decorator` entries; their `p_j`
(`aes_encrypt__eqsrc.py`) contains `class DES_ENCRYPT` with no class decorator
and two `@staticmethod` methods.  The only decorators are those method-level
`@staticmethod` expressions; the methods' host is `class-body`, not the claimed
`decorator-expr`/`function-body`/`call-arg` hosts.  There is no top-level
decorated function, no class decorator, and no `deco-stack`/`deco-with-args`
form.  The entries are family-existence placeholders, not dedicated witnesses.
A module run cannot establish their claimed host/depth/variant combinations
(the claimed `decorator-expr` host would require a FunctionDef/ClassDef node
inside a decorator list, which does not exist), and a call to
`code_encrypt_pyc`/`code_encrypt_so` would not exercise a decorator host.

## Rejected shortcuts

| shortcut | why rejected |
|---|---|
| Run `aes_encrypt` as a module witness for `JS-DECORATOR-009` | `p_j` has no class decorator; the run would not witness `deco-on-class` at `module-level`.  A false positive. |
| Stub `IQCommon.data.TickDataCache` / `L2DataCache` / `ReferenceCache` | Changes module globals and behavior; bypasses the real-package safety gate; not a faithful witness. |
| Load the Linux `.so` on Windows | ELF extension modules cannot be loaded by Windows CPython; no WSL/Docker/podman. |
| Replace `p_j`/`pyc` with a synthetic wrapper or a dedicated probe | Changes the J record’s source, pyc, and host label; that would move the target, not close it.  A new J entry is a different record. |
| Count `pyc_verify` unit success as coverage | `units_success` is decompilation/bytecode verification, not a call witness; it is already not in the coverage numerator. |
| Treat the 364 “专属见证探针” as call witnesses | They are byte-identical staged copies of the same pyc (SHA verified), not call expressions; they still cannot import. |

## Readings unchanged

The audit is evidence-only.  The official coverage run is still:

```text
[coverage] J_total=1556 covered_5tuple=1180 probe_only=0 unexecuted=0 n/a=0 inconclusive=0 excluded=376 uncovered=376 coverage=75.84%
[coverage] GATE FAIL: uncovered=376 (covered_5tuple is the only numerator)
```

`coverage_v3m_b275.json` totals were re-read by the audit and match the space
(`consistent: true`).  No J entry was edited; no `p_j`, `pyc`, or semantic
product changed.  G1 remains **FAIL/BLOCKED**.  This round makes **no** claim of
product completeness.

## Reproduce

From the repository root:

```powershell
# 1. Re-run the seven dependency probes and write the audit JSON.
python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/audit_real_packages.py `
  --run-probes --deps D:\temp\opencode\j3deps

# 2. Re-run without probes: reuses the archived probe block and is deterministic.
python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/audit_real_packages.py `
  --deps D:\temp\opencode\j3deps

# 3. One probe directly (triage only; not a coverage witness).
python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/probe_real_package_module.py `
  --root . --deps D:\temp\opencode\j3deps `
  --pyc site-packages/fly/common/aes_encrypt.pyc `
  --name fly.common.aes_encrypt
```

Expected summary:

```text
[audit] excluded=376 pyc=7 ok=1 blocked=6 module_level=10 claimed_host=9 closable=0
```

## Conditions to close (not met here)

1. **Nine module-level entries**: a Linux x86_64 CPython 3.11 runtime with the
   matching `TickDataCache`/`L2DataCache`/`ReferenceCache` `.so` files and an
   audited side-effect sandbox.  Then the module-code witness could be run and
   the nine entries could be considered.
2. **355 non-module-level entries**: host-specific call expressions that reach
   the recorded `function-body`/`if-arm`/… host, with the same original pyc and
   product source; module execution is insufficient.
3. **Twelve `aes_encrypt` entries**: dedicated probes for the claimed
   host/depth/variant combinations.  `JS-DECORATOR-009` cannot be closed by
   module execution because the source has no class decorator; the other eleven
   are not established by the current `p_j`.
4. G3 full mutation population, G4 `open=339`, and G6 independent custody remain
   separately blocked; this audit does not change them.
