# Round 63 batch 1 — ANALYSIS (trade_live_broker / fly.data.quote / quote_handler)

工作区 `D:/Temp/opencode/r63gate/diag1`，HEAD=96a5f310，生成器 sha b9778ee0130865d55888。
靶：`IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` 的 `fund_transfer(-35)`。

## 1. 最小合成复现（已落地，可复用）

- `F:/Downloads/pythoncdc-main/test_repros/round63_b1/r63_ft.py` + `.pyc`（本地 3.11.7 编译，
  与靶 pyc 同族：`if cond: obj.m(f'...三元...{call}'); return False` / else 对称）。
- `F:/Downloads/pythoncdc-main/test_repros/round63_b1/r63_ft2.py` + `.pyc`：加上 elif 链外层，
  复现「orelse 整体消失」（见 §5）。
- `F:/Downloads/pythoncdc-main/test_repros/round63_b1/r63_ft4.py` + `.pyc`：同块调用后还有后续
  语句（`merge_context` 非 'fstring'）的**未修**边界，见 §9。
  跑法同 r63_ft，把 `--list` 换成 `dump/repro4.txt`（内容即该 pyc 绝对路径）。

跑法（非侵入，产物只落 diag1/build_<arm>/）：
```
cd D:/Temp/opencode/r63gate/diag1
echo "F:/Downloads/pythoncdc-main/test_repros/round63_b1/r63_ft.pyc" > dump/repro.txt
python -X utf8 h62.py run --arm=landed --list=dump/repro.txt --out=dump/repro_landed.jsonl --budget=200
python -X utf8 h62.py run --arm=c2     --list=dump/repro.txt --out=dump/repro_c2.jsonl     --budget=200
```
逐函数元组 [orig, decomp, jumpdiff, truediff]：
| arm | r63_ft.fund_transfer_case | r63_ft2.t2 | r63_ft4.t4(未修) | 靶 fund_transfer |
|---|---|---|---|---|
| landed | 65/48/1/57 | 109/74/1/57 | 31/22/1/23 | 123/88/1/57 |
| c2     | 65/65/0/6  | 109/84/0/30 | 31/22/1/23 | 123/98/0/30 |

r63_ft 与靶同缺陷（元组比例一致），r63_ft2 连剩余缺口（-25 orelse）都与靶一致 → 复现成立。

## 2. 实测到的真实归属/区域转储（靶 fund_transfer，摘自 R62 探针 + 本轮 dis 复核）

CFG 21 块；`IfRegion@184(IF_THEN_ELSE)` 的 then 臂＝`TernaryRegion@300 blocks=[300,334,338,340]`，
其 merge 340 又是 `TernaryRegion@340 blocks=[340,356,360,362]` 的 entry；else 臂对称
（430→470→492）。全部 21 块都被标 generated（语句却没发出来 → 不是「没进去」，是「进去后丢东西」）。

字节码（`logs` 里 dis 复核，见 R62 `trade_live_broker__fund_transfer.dis.txt`）：
```
300 LOAD_GLOBAL NULL+strategy_log ; 312 LOAD_ATTR error      # 被调对象压栈，跨块待定
322..332 trans_direction=='0' ; POP_JUMP → 334/338           # 三元1
340 FORMAT_VALUE ; 342 LOAD_CONST '极速' ; ... POP_JUMP       # 三元2 的 cond 与 merge 同块
362 FORMAT_VALUE ; 364 LOAD_CONST '失败，错误原因：'
366 LOAD_FAST error_dict ; LOAD_METHOD get ; 390 LOAD_CONST 'error_info' ; PRECALL ; CALL
406 FORMAT_VALUE ; 408 BUILD_STRING 5 ; 410 PRECALL ; 414 CALL ; 424 POP_TOP
426 LOAD_CONST False ; 428 RETURN_VALUE
```
即：f-string 的第 3 个插值段操作数**本身是 CALL**，且整条 f-string 是那个跨块待定 callee 的实参。

## 3. 生效机制（探针证实，非推断）

探针 `logs/r63_probe_recon.py`（monkeypatch `ExpressionReconstructor.reconstruct`，只读）显示：
链式三元归约**根本没有**对 merge 段之后的指令做过任何 reconstruct —— 缺陷不在表达式重建器，
而在 `_try_build_ternary_chained_container` 的 `merge_ctx == 'fstring'` 手写扫描器
（`core/cfg/region_ast_generator.py` 原 L41029-41079）：

1. 末段扫描只认 `FORMAT_VALUE`/`LOAD_CONST`/`BUILD_STRING` 三种操作码，
   于是 `{error_dict.get('error_info')}` 段里的 `LOAD_CONST 'error_info'`（CALL 的实参！）
   被当成 f-string 字面量收进 parts，操作数（CALL 及被格式化的值）整体丢失 → 输出裸 `error_info`；
2. 包裹语句判据只看 `innermost_merge` 末条是否 `RETURN_VALUE`，于是
   `BUILD_STRING 之后的 PRECALL/CALL/POP_TOP/LOAD_CONST False/RETURN_VALUE` 被误读成
   `return <f-string>` → 真正的 `strategy_log.error(...)` 表达式语句与 `return False` 蒸发。

两处都是「把栈上当待定的操作数误判为字面量/把跨块调用的消费点误判成本区域的终结符」，
属**归属判据过宽**，不是缺逃逸口 —— 因此修法是收窄这两条判据，不新增跨层启发。

## 4. 候选 cand_fstail3（arm c2）——三个 edit，全在同一函数体内

`specs/cand_fstail3.json`（`core/cfg/region_ast_generator.py`，3 edits）：

- **Fix1**（锚 L41029-41046）：链尾 FORMAT_VALUE 的段边界归约。以 FORMAT_VALUE 为界把内层
  merge_block 切成若干段，逐段用**段内栈形态**归约（`_fstring_parts_from_segment`：正向单趟
  模拟，栈顶被 FORMAT_VALUE 消费、栈底连续 Constant 才是字面量段）。栈解释不了就整段
  退回既有扫描（保守，无新逃逸口）。→ 恢复 `{error_dict.get('error_info')}`。
- **Fix2a**（新私有 helper `_ternary_pending_callee`）：与既有 `is_call_pattern` 分支**同一判据**
  取跨块待定被调对象（LOAD_METHOD / PUSH_NULL+LOAD_* / LOAD_GLOBAL|NULL 标志）；靶的 pyc 用的是
  `LOAD_GLOBAL (NULL + name)` + `LOAD_ATTR` 形态（无独立 PUSH_NULL），故补该分支的属性链重建。
- **Fix2**（锚 L41051-41052 前插）：`_try_wrap_fstring_pending_call`。识别条件（纯栈形态）：
  BUILD_STRING 之后紧跟 PRECALL/KW_NAMES*+CALL、CALL 实参数==1、结果被 POP_TOP 丢弃；
  归约为 `Expr(Call(callee,[JoinedStr]))`，CALL 之后的剩余指令按「每块唯一归属」交既有约定
  `region.post_consumer_extra_stmts`（与同函数 STORE_SUBSCR 分支同一机制）→ `return False` 复原。
  任一条件不满足即返回 None，走既有 Assign/Return/Expr 判定（零改道）。

见证（实测）：`fund_transfer 123/88/1/57 → 123/98/0/30`（deficit -35→-25，jumpdiff 1→0，truediff 57→30）；
合成复现 `65/48/1/57 → 65/65/0/6`（长度与跳转全清，剩 6 处 `!s` 转换标志）。
`market_fund_transfer` 未动（67），它只有 1 个三元、`len(ternary_chain) < 2`，走的是单三元路径，
不同机制（见 §6）。quote/quote_handler 三行未动（get_price/check_limit/load_get_price/
run_individual_transform/get_kline_* 全等 landed）→ 本候选对它们 inert，不是它们的机制。

## 5. 剩余缺口 -25：elif 链内 IfRegion 的 orelse 丢失（**先于本候选存在**，未修）

对照实测：平坦形 `r63_ft`（`if/else` 两臂各含一条 f-string 调用）在 **landed** 下两臂都在
（只是被误判成两条 `return f"..."`），在 c2 下两臂全对 → 本候选不触碰 orelse 的存在性；
而 elif 套嵌的 `r63_ft2` 在 **landed** 下同样只剩 then 臂 → orelse 丢失是 elif 链构造的
**既有独立缺陷**，与本批判据无关（探针 `_generate_if` / `_generate_ternary` 在 t2 上均未被调用，
说明该 If 由另一条 arm 语句序列组装路径发射，定位到那儿即可 —— 见 §7.1）。

`r63_ft2`（elif 链里套 `if error_dict.get(...) != 0`）证实：then 臂修好后 else 臂（25 条）仍丢，
且该臂的 4 个块全部标 generated（`logs/probe2c.out`）。平坦版 `r63_ft`（无 elif 外层）两臂都发得出来，
所以丢失点在 **elif 链构造器对「臂以 Return 终结且无 merge」的 IfRegion 的 orelse 处理**，
与本批 f-string 判据无关，属下一条独立判据（见 §7 下一步）。

## 6. 已证伪 / 不成立假设

- R62 `cand_fstail2.json`（锚在「# Determine wrapping from innermost merge_block.」）：
  锚点落在 `is_call_pattern` 的 `_call_expr` 分支（L40936），而 f-string 走的是
  `merge_ctx == 'fstring'` 分支里**另一份同名注释**（L41051）；且该分支的
  `is_call_pattern` 被 `merge_ctx != 'fstring'` 显式互斥排除 → 改动对本族永不生效（INERT 复现）。
- 「先复现 f-string 操作数为 CALL 时 region_analyzer 的栈/归属状态」：探针否证——区域与归属
  都正确（全块标 generated、链正确），错的是**发射期的手写扫描**，不在分析层。
- 「`_ternary_nested_in_container_construction` 能覆盖本例」：否证。该判据要求栈底是
  BUILD_MAP/LIST/SET/TUPLE 开启的未闭合容器，本例栈底是被调对象，返回 False，不走容器路径。
- 「f-string 段丢是 ExpressionReconstructor 的 FORMAT_VALUE 语义缺陷」：否证，
  相关 reconstruct 调用一次都没发生（探针输出仅 17 条 RECON，无 merge 段之后的）。

## 7. 下一步判据方向（交给 R64）

1. orelse 丢失（`fund_transfer` 剩 -25 全部来自它）：先用 `logs/probe2.py`（已含
   `_generate_if` / `_generate_ternary` 包装，实测二者在 t2 上**零调用**）找真正的 elif 组装路径，
   再判该路径是否忽略 else 臂区域。同函数 `get_manage_mark` 的 elif/else 正常，
   差异在 arm 内含「被跨块待定调用消费的三元链」。
2. `market_fund_transfer(-27)`：单三元链走 `_generate_ternary` 非链路径，输出把 callee
   `strategy_log` 混成 f-string 字面量段 → 同一族判据需在该路径复制（Fix1/Fix2 的段归约
   目前是链专用）。
3. `conversion`：FORMAT_VALUE flag 低 2 位（靶用 `!s`→1）在链上三元 FV 与新增 FV 里都硬编码 0，
   是 r63_ft 剩 6 处 truediff 的唯一来源；改从 `_li.arg & 3` 取即可清，但要全量验（未做）。
4. quote.pyc 的 `get_price`：f-string 段整体错位（`stocks=securityNone{10!s}等...`），
   与 AssertRegion+多三元混排相关，非本批机制。

## 8. 门禁（实测，非推断）

3 靶（`dump/landed.jsonl` vs `dump/c2.jsonl`，`cmp_arms.py`）：
```
files=3 errors=0  landed: matched=229 -> c2: matched=229
MOVED  IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc 104/119 -> 104/119
   ~delta  fund_transfer  123->88 (-35) | 123->98 (-25)
TALLY landed->c2 : REGRESSION=0 IMPROVED=0 MOVED=1 SAME=2
```
（quote / quote_handler 两支产物逐字节相同 → 本候选对它们 inert，见 §6。）

全量 402（基线复用 R62 落地字节 dump `r62gate/dump/f4_402.jsonl`，arm f4 == 工作树 b9778ee0130865d55888；
候选分两片 `dump/c2_402.jsonl` + `dump/c2_402s1.jsonl`，逐文件 sha256 比较）：
```
compared 402  SAME-byte 401  IMPROVED 0  REGRESSION 0  MOVED 1  ERR 0
matched 函数数 5675 -> 5675   完全匹配文件 381 -> 381
唯一变化文件 = 靶 trade_live_broker（fund_transfer 逐函数 -35 -> -25）
```
候选字节自证：`python -X utf8 h62.py build --spec=specs/cand_fstail3.json --dst=c4`
产出与实测臂 mirr_c2 **逐字节相同**（sha256 前 20 位 90e1a8df8ff3d8fc7f5b、3 074 467 B、
UTF-8 BOM、纯 CRLF 49750、裸 LF 0、ast.parse OK）。仓库 `core/` 未被改动
（工作树仍 b9778ee0130865d55888 / 3 059 418 B，`git status --porcelain` 无跟踪文件修改）。

## 9. 追加实测（同族边界）

- `r63_ft4.py/.pyc`：then 臂的调用之后同块还有后续语句（`x = occur_balance`）——
  landed / c2 / c3 三臂**逐字节相同且都坏**（输出 `f"strategy_log{'转入' if ...}失败error_info"`），
  即本候选在该形态上完全不触发（该形态的 merge_context 不是 'fstring'，被分析层判成 store 族）。
  → 这是 `market_fund_transfer(-27)` 的同类边界，交下一批：判据方向 = 单三元（`len(chain)<2`）
  或 merge_context='store' 时，cond_block 的待定 callee 被手写扫描当字面量吞进 JoinedStr。
- 曾在 c3 上试过给 Fix2 加「剩余段必须以 RETURN/RAISE/YIELD 终结」的额外保守判据：
  r63_ft / r63_ft2 / r63_ft4 三例与 c2 **逐函数元组完全一致**（无任何可测效果），
  属无见证支撑的多余条件 → 已回退，交付的 spec 即 c2 字节态（cand_fstail3.json）。
