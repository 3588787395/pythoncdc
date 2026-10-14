# R21-41 / R68 — is the `_process_cancel_order` jump layout expressible?

**Verdict: EXPRESSIBLE.** One shape in the family is **byte-identical** to the original `co_code`
(2044/2044 bytes, SHA-256 equal), with `co_exceptiontable`, `co_consts`, `co_names`, `co_varnames`
all equal. It is `S05_nested+else_cont`.

Interpreter: `python 3.11.7`, pyc magic `a70d0d0a` (= 0x0da7, 3.11) → **same minor version**, so the
byte compare is exact, not indicative.

## 0. Original facts (all re-verified with `dis.get_instructions`, EXTENDED_ARG/CACHE kept visible)

| claim | measurement | status |
|---|---|---|
| `@44` = one `NOP`, single successor `@46` | `@44 NOP`, `@46 LOAD_GLOBAL len` | ✓ |
| explicit `continue`s → `@44` | `@416→@44`, `@924→@44`, `@1824→@44`, `@1998→@44` | ✓ |
| body tail → `@46` | `@2042 EXTENDED_ARG + JUMP_BACKWARD → @46` | ✓v |
| `@1822..@1824` = pure continue block | `@1822 EXTENDED_ARG(3)`, `@1824 JUMP_BACKWARD→@44` | ✓ |
| `@1710` operand | `0x6e 0x37` = `JUMP_FORWARD arg=55 → @1822` | ✓v |
| `@1826` = sleep jump | `@1826 JUMP_FORWARD → @2000`; **entered only by `@944 POP_JUMP_FORWARD_IF_FALSE`** (the `business_type in ('future','rzrq')` false exit) **and `@1606 JUMP_FORWARD`** (arm A exit) | ✓v |
| `@1822` predecessors | jump edge from `@1710` + fall-through from the block starting `@1712` | ✓ |
| exc table | `b133413e00c13e1b421903c312433b4e1200c70f47004e1200ce122d4f0203cf01014f0203` | — |

So in the original, **arm B (`pass`) and arm C both end in the same `continue`** (arm B by jump edge,
arm C by fall-through), while arm A exits to the merge `@1826`. Arm B therefore *skips* `time.sleep`
— the 1-byte candidate is a real semantic difference, not a cosmetic one.

## 1. Shape family (25 shapes, whole-module compile of a patched `trade_live_brokerOK.py`)

`armB@1710->` = target of the arm-B exit jump; `tail->` = last `JUMP_BACKWARD` target. Every shape
reproduces `tail→@46 / continues→@44`; only the arm-B target discriminates. Full raw output:
`DELIVER/report.txt`.

| shape | struct | len o/p | diffs | first diff | orig decode | prod decode | armB→ | exc | jumps |
|---|---|---|---|---|---|---|---|---|---|
| S00_current_OKpy | elif chain, cont after try | 2044/2040 | 85 | 95 | @94 PJF→@2000 | @94 PJF→@1996 | @1822 | NE | NE |
| S01_Ccont(E1 brief cand.) | elif chain, cont in arm C, else arm has no cont | 2044/2040 | 32 | 95 | @94→@2000 | @94→@1996 | @1826 | EQ | NE |
| S02_Ccont+else_cont | elif chain, cont in arm C + cont in `orders` else | 2044/2044 | **1** | 1711 | @1710 JF arg55→@1822 | @1710 JF arg57→@1826 | @1826 | EQ | NE |
| S03_Ccont+tail+else_cont | S02 + extra cont after try | 2044/2048 | 66 | 95 | — | — | @1826 | EQ | NE |
| S04_chain_tail+else_cont | elif chain + cont at chain tail | 2044/2044 | **1** | 1607 | @1606 JF→@1826 | @1606 JF→@1822 | @1822 | EQ | NE |
| **S05_nested+else_cont** | **else: (if B: pass else: err); continue** | **2044/2044** | **0** | **none** | — | — | **@1822** | **EQ** | **EQ** |
| S06_nested_err+else_cont | cont inside inner else | 2044/2044 | 1 | 1711 | @1710→@1822 | @1710→@1826 | @1826 | EQ | NE |
| S07_nested_not+else_cont | `else: if not (B): err; continue` | 2044/2042 | 177 | 95 | — | — | none | NE | NE |
| S08/S09 | S05/S07 + cont after try | 2044/2048, 2044/2046 | 65, 179 | 95 | — | — | @1822/- | EQ/NE | NE |
| S10_B_cont+else_cont | arm B written as `continue` | 2044/2046 | 178 | 95 | — | — | none | NE | NE |
| S11_elif_not+else_cont | `elif not (B): err; continue` | 2044/2042 | 177 | 95 | — | — | none | NE | NE |
| S12_neg_first+else_cont | `if error_no != 0:` + nested | 2044/2038 | 521 | 95 | — | — | none | NE | NE |
| S13_nested_no_cont+else_cont | nested, no continue | 2044/2038 | 189 | 95 | — | — | none | NE | NE |
| S14–S18 | S05/S01 `try/else` and `except: continue` wrappings | 2044/2046…2040 | 117–138 | 95 | — | — | @1822/@1826 | NE | NE |
| S19_cur+else_cont | elif chain, no cont at all | 2044/2040 | 115 | 95 | — | — | @1822 | NE | NE |
| S20_nested+else_cont+err_only | S05 minus the `orders`-else continue | 2044/2040 | 31 | 95 | — | — | @1822 | EQ | NE |
| S21_nested_pass_then_err | inner `if B: pass`, error as sibling | 2044/2044 | 2 | 1710 | @1710 JF | @1710 NOP | none | EQ | NE |
| S22_neg_nested+else_cont | `if error_no != 0` + nested | 2044/2040 | 493 | 95 | — | — | none | NE | NE |
| S23/S24 | S05 with try/else, after_try | 2044/2042, 2044/2044 | 115, 36 | 95, 331 | — | — | @1822 | NE/EQ | NE |

Mini probes (synthetic `while/if/try`, method step 4) confirm the same law independent of the corpus
file: only the *nested* shape and the chain-tail shape make a `JUMP_FORWARD` land on the continue
block (`m2: @120→@150`, `m4: @90→@150,@120→@150`); the plain elif chain (`m1`) never does.

## 2. Byte-identical proof for S05

```
sha256 co_code orig = b69a3df0465ee49dd9b9111f64c7ffe604dff88bb36894ccc5edc830b35b2342
sha256 co_code prod = b69a3df0465ee49dd9b9111f64c7ffe604dff88bb36894ccc5edc830b35b2342
diff byte offsets   = [] (n=0)      len 2044 vs 2044
co_exceptiontable EQ ; co_consts EQ ; co_names EQ ; co_varnames EQ ; co_freevars/co_cellvars EQ
co_nlocals/co_stacksize/co_flags/co_argcount EQ ; jump list EQ (31 vs 31)
co_linetable NE (1046 vs 1096)  -- line numbers, as for every other product unit; not a bytecode face
```
Independently re-measured in a second process from the written file `DELIVER/winner.py`
(`compile()` → `co_code` compared to `marshal.loads(pyc[16:])`, `cmp`-level equality).

## 3. The shape (region as it must be emitted)

```python
                        if self.business_type in ('future', 'rzrq'):
                            if error_dict.get('error_no') == 0:
                                <arm A>
                            else:                                              # NOT `elif`
                                if error_dict.get('error_no') == T2SDK_RTNPACK_EMPTY and self.broker.trade_account.node_type == '7':
                                    pass
                                else:
                                    strategy_log.error(_('后端服务 撤单失败，错误原因：%s' % error_dict.get('error_info')))
                                continue                                       # sibling of the inner if
                    except BaseException:
                        strategy_log.error('后端服务 撤单失败，错误信息：%s' % get_traceback_message())
                    # NO continue here
                else:
                    strategy_log.error(_('当前订单状态不支持撤单'))
                    continue                                                   # explicit, in the else arm
            time.sleep(0.001)
```

Three coupled facts, not one: (i) arm B/arm C form a **nested If/If**, not an elif chain; (ii) the
`Continue` is the **last statement of the outer if's `orelse`**, a sibling *after* the inner If;
(iii) the `try` has **no trailing `continue`**, and the `if order in self.orders:` **else arm ends in
an explicit `continue`** (its fall-through into the loop tail would otherwise save 4 bytes → S20, 31 diffs).

## 4. Minimal AST description for the generator

`Continue` must sit in the **`orelse` list of the `If(test=Compare(error_dict.get('error_no'), '==', 0))`
node, AFTER the nested `If`**, i.e. `orelse=[If(...), Continue]` — never inside either `If`'s `body`,
and never hoisted into the enclosing `Try` body after the `Try`:

```python
{'type': 'If', 'test': "self.business_type in ('future', 'rzrq')",
 'body': [{'type': 'If',
           'test': "error_dict.get('error_no') == 0",
           'body': [<arm A stmts>],
           'orelse': [                                     # <- orelse, NOT an elif continuation
               {'type': 'If',
                'test': "error_dict.get('error_no') == T2SDK_RTNPACK_EMPTY and self.broker.trade_account.node_type == '7'",
                'body': [{'type': 'Pass'}],
                'orelse': [{'type': 'Expr',
                            'value': "strategy_log.error(_('后端服务 撤单失败，错误原因：%s' % error_dict.get('error_info')))"},]},
               {'type': 'Continue'}]}],                    # <- last stmt of the outer orelse
 'orelse': []}
```
and in the enclosing `if order in self.orders`: `orelse=[Expr(error('当前订单状态不支持撤单')), Continue]`,
with the `Try`'s `finalbody`/post-`except` sequence carrying **no** `Continue`.

## 5. Why the elif-chain family is closed (proof, not sampling)

CPython emits one `end` label for a whole `if/elif/else` chain, so all arms' exit jumps take the
same target. The original needs **two different targets**: `@1826` for arm A (`@1606`) and `@1822`
for arm B (`@1710`), differing by exactly the size of the continue block. No `Continue` placement
inside an elif chain can split them — S02/S06 (chain or nested with the continue inside the inner
else) fix arm A and miss arm B by 4 bytes; S04 (chain with a chain-tail continue) fixes arm B and
breaks arm A at `@1607`. Hence the nested If/If + sibling `Continue` is the unique member of this
family, and it reproduces the code object exactly.

## 6. Method traps found (worth pinning to the campaign memory)

* **Harness must compile the WHOLE module.** A module-level `import time` changes `time.sleep(...)`
  from `LOAD_METHOD` (22 B) to `LOAD_ATTR` (10 B): an extracted-snippet compile gives 2124 B and
  invents ~80 phantom diffs. The corpus pyc uses `LOAD_ATTR` (`@2012`), so only the whole-module
  compile is comparable. (Measured: `import time` alone flips one call site; no other import does.)
* The in-repo `__pycache__/trade_live_brokerOK.cpython-311.pyc` is **stale** (787 diffs vs original);
  recompiled current `OK.py` = S00 = 85 diffs. The brief's 1-byte candidate is S02, and it
  reproduces exactly (`first=1711, 0x37 vs 0x39`), which validates this harness against your measurement.
* `dis.get_instructions` gives resolved jump targets; EXTENDED_ARG must be kept when computing the
  4-byte deltas (the `@1822` block is 2 code units and is *not* jump-threaded precisely because it
  carries an EXTENDED_ARG).
