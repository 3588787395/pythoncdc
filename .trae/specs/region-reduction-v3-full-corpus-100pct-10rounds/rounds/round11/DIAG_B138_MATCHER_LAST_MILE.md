# DIAG B138 — matcher.DefaultMatcher.match last mile (Round 11)

Scope: diagnosis only. No edits under `core/`, no git writes, no 402 gate.
Scratch: `D:/Temp/r138/`. Judge: `scripts/pyc_verify.py single … --source` (compare-only).
Baselines consumed (not redone): `rounds/10 DIAG_B131 §三.0–三.2/§六/§七`, `rounds/10 FIX_B132`
(3-site patch, archived `D:/Temp/r132b/b132.patch`, NOT landed), `rounds/11 DIAG_B134/B136/B137`,
`MEASURED_FLIPS §3/§4/§5/§6/§8/§9`, `TICKETS_ROUND11 §六/§七`.
Repo bytes at time of this run (measured): `core/cfg/region_ast_generator.py` sha256[:16]
`e9a8f65f6451bcc8` (sealed), `core/cfg/region_analyzer.py` `e926a54f17753b33` (**B133 landed** ⇒ all
analyzer lines below re-grepped against CURRENT bytes, none copied from B134/B137).

## Task 1 — reproduce (DONE)

Commands actually run (each < 300 s):
- `python -X utf8 pycdc.py site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc -o D:/Temp/r138/m_now.py`
- `python -X utf8 scripts/pyc_verify.py single site-packages/.../matcher.pyc --source D:/Temp/r138/m_now.py`
  ⇒ `***<module>.DefaultMatcher.match: Failure: Different control flow`, `status=failure units=16/17 success_rate=94.12%` — **brief confirmed**.
Default-product run (no `--source`, against sealed `matcherOK.py`) reads the same 16/17;
`diff` of sealed OK vs fresh product = same bytes (only line-ending normalization), so HEAD is stable.

Product `match` body, lines 127–176 (the failing region), printed with exact indents — see
`D:/Temp/r138/m_now.py`; the load-bearing segment:

```
152|<24sp>if order.asset.symbol[:3] not in ('300', '688', '689'):
153|<28sp>    if BUY and deal_price >= get_limit_up:        # 153-156 arm-1 chain, CORRECT
157|<24sp>else:
158|<28sp>    if not (order.asset.symbol[:3] == '300' and trading_date < gem_change_date):   # WRONG SHAPE
159|<32sp>        if order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
160-163|<36/40sp>  BUY/SELL continue chain                    # P∨Q rendered as ¬P∧Q  (hunk @1382)
164|<28sp>    stock_listed_date = order.asset.listed_date    # assignments OK
165|<28sp>    next_trading_date = ...
166|<28sp>    is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
167|<28sp>    if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date:
168|<32sp>        if is_first_five_trading_days or BUY and >=up:    # WRONG: guard folded into or (hunk @1910)
169|<36sp>            continue
170|<32sp>        elif SELL and <=down:
171|<36sp>            continue
172|<28sp>    if is_first_five_trading_days or BUY and >=up:        # this copy IS the swallowed block's body,
173-175|   ... elif SELL and <=down: continue                       # emitted WITHOUT its head test @2164
```

So the `('688','689')` test (block @2164) is **missing**, and its body is misrendered at 172–175
as an or-folded chain; TWO further independent misrenders exist at 158–159 and 168.

## Task 1bis — hunk list of the failing unit on HEAD bytes (own instrument, r10g7 口径)

`python -X utf8 D:/Temp/r138/hunk138.py <pyc> D:/Temp/r138/m_now.py` (log `D:/Temp/r138/hunk_head.txt`):

```
UNIT /<module>/DefaultMatcher/match  len 776/766 net=+10  hunks=25 real=1 reloc=24 deleted=34 inserted=24
```

Decomposition (measured): exactly **one content hunk** —
`delete orig[347:357]` = the 10-instruction head test @2164
(`LOAD_FAST order | LOAD_ATTR asset | LOAD_ATTR symbol | LOAD_CONST None | LOAD_CONST 3 | BUILD_SLICE |
BINARY_SUBSCR | LOAD_CONST ('688','689') | CONTAINS_OP | POP_JUMP_FORWARD_IF_FALSE ->@2464`).

Of the 24 target-only hunks, **20 are pure relocation artifacts** of that deletion (every target from
@2210-onward is uniformly −44 = 10 instrs × 4.4B; e.g. `->@2468` vs `->@2424`, `->@3210` vs `->@3166`):
they disappear automatically once the 10 instructions are restored. **4 are genuine**:

| hunk | orig | prod | meaning |
|---|---|---|---|
| @1322 | `JUMP_FORWARD ->@2464` | `->@3166` (=3210) | arm-1 tail must skip to the if/else **merge**, not past the LIMIT-`else` — artifact of the missing @2164 test (merge position moves) |
| @1382 | `POP_JUMP_FORWARD_IF_TRUE ->@1444` | `->@1696` | **or-chain fold**: `(P)∨(Q)` short-circuit-true landing rendered as skip |
| @1910 | `POP_JUMP_FORWARD_IF_TRUE ->@2164` | `->@2034` | **guard fold**: `… and not is_first_five` rendered as `is_first_five or …` (true→continue instead of true→next stmt) |
| @2210 | `POP_JUMP_FORWARD_IF_TRUE ->@2464` | `->@2290` | same guard fold on the 688/689 body copy |

## Task 1ter — the true original shape, reconstructed from the pyc disassembly (`D:/Temp/r138/dis_match.txt`)

Edge-by-edge verified against `dis`: the failing region compiles as

```python
if order.asset.symbol[:3] not in ('300', '688', '689'):
    if BUY and deal_price >= get_limit_up(asset.symbol):
        continue
    elif SELL and deal_price <= get_limit_down(asset.symbol):
        continue
else:                                                     # @1040 if/else, merge @2464 (tail JF->@3210)
    if order.asset.symbol[:3] == '300' and trading_date < gem_change_date or order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
        if BUY …: continue / elif SELL …: continue        # @1324..@1384 P∨Q, both true → @1444
    stock_listed_date = order.asset.listed_date           # @1696 (P∨Q false exit == fallthrough == next stmt)
    next_trading_date = …
    is_first_five_trading_days = …
    if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date and not is_first_five_trading_days:
        if BUY …: continue / elif SELL …: continue        # @1836..@1910 four-and operands, false→@2164
    if order.asset.symbol[:3] in ('688', '689') and not is_first_five_trading_days:
        if BUY …: continue / elif SELL …: continue        # @2164..@2210, false→@2464
```

Key measured facts: `is_first_five_trading_days` is loaded **exactly twice** in the unit (@1908, @2208),
both as `POP_JUMP_FORWARD_IF_TRUE` to the *following statement* (2164 / 2464) ⇒ the guard is `and not
is_first_five_trading_days` (or equivalently nested `if not is_first_five:`, byte-identical), never an
`or` operand — the product's `if is_first_five or …: continue` inverts the guard polarity of the
short-circuit and lands true on `continue`. `if not (P): if Q: body` (product) vs `(P) or (Q): body`
(original) differ exactly on P-true landing (@1382): P-true must **enter** the body (short-circuit),
the product skips it.

## Task 2 — ORACLE VERDICT (measured; `D:/Temp/r138/mk_oracles.py` builds all variants from `m_now.py`)

| variant | edit applied | judge | residual hunks (all target-only, net 0 after the test is restored) |
|---|---|---|---|
| (ii) `m_or_ii.py` | wrap current 172–175 body under `if order.asset.symbol[:3] in ('688', '689'):` @28 | **16/17** | 4: @1322, @1382, @1910, @2210 |
| (i) `m_or_i.py` | statement @28 + nested flatten `if not is_first_five_trading_days:` + flat and-chain | **16/17** | 3: @1322, @1382, @1910 |
| (iii) `m_or_iii.py` | (i) + same flatten applied to the 167 arm (168 `is or` → 166 head `… and not is_first_five_trading_days:`) | **16/17** | 2: @1322, @1382 |
| **full `m_or_full.py`** | (iii) **+ E1**: lines 158–159 `if not (P): if Q:` → one or-chain `if P or Q:` | **17/17 status=success** | 0 |
| `m_or_full_flat.py` | full, 688 head as sibling `if … in ('688','689') and not is_first_five_trading_days:` | **17/17 status=success** | 0 (proves nested ≡ flat at bytecode level) |
| `m_or_full_elif.py` | full, 688 head as `elif` of 167 | 16/17 | falsifies "elif is interchangeable": an `elif` arm body sends its non-continue exits past @2164 to the chain merge, not to @2164 |

**Answer to task 2**: none of the three briefed candidates (i)/(ii)/(iii) reaches 17/17 — the last mile
is **three** folds, not one. The byte-correct product text (indent shown as spaces; from
`m_or_full.py:152–176`) is:

```python
                        if order.asset.symbol[:3] not in ('300', '688', '689'):
                            if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                continue
                            elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                continue
                        else:
                            if order.asset.symbol[:3] == '300' and trading_date < gem_change_date or order.asset.symbol[:3] == '300' and stock_listed_date_str < gem_change_date:
                                if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                    continue
                                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                    continue
                            stock_listed_date = order.asset.listed_date
                            next_trading_date = self._engine.data_proxy.get_next_trading_date(stock_listed_date, 5)
                            is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date
                            if order.asset.symbol[:3] == '300' and trading_date >= gem_change_date and stock_listed_date_str >= gem_change_date and not is_first_five_trading_days:
                                if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                    continue
                                elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                    continue
                            if order.asset.symbol[:3] in ('688', '689'):
                                if not is_first_five_trading_days:
                                    if order.entrust_direction == EntrustDirection.BUY and deal_price >= self._engine.data_cache.get_limit_up(asset.symbol):
                                        continue
                                    elif order.entrust_direction == EntrustDirection.SELL and deal_price <= self._engine.data_cache.get_limit_down(asset.symbol):
                                        continue
```

(The 688/689 arm may equivalently be the single line `if order.asset.symbol[:3] in ('688', '689') and not
is_first_five_trading_days:` + undoubled chain — both compile byte-identical, measured.)

**Falsified by this**: FIX_B132 §4's claim that the last mile is only `IfRegion@2208`'s body. Even a
byte-perfect @2164 statement+body (`m_or_iii`) still reads 16/17 because of **two more folds strictly
before @2164** — the arm-2 or-chain `(A∧B)∨(A∧C)` rendered as `if not (A∧B): if A∧C:` (@1382) and its
consequence on the arm-1 tail jump (@1322). And B132's "correct form of the @2164 body" is confirmed
(nested flatten = flat-and = 17/17 components), but their assumption that the 167-arm product lines
167–171 were fine is **false** — the same guard fold (`@1910`) is live there on HEAD.

(pending: family verdict, host lines, arms)
