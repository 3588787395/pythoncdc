# Round 65 · diag2 · FACTS — `site-packages/fly/data/quote.pyc` (官方 70/81)

All commands run from `D:/Temp/opencode/r65gate/diag2` with `python -X utf8`.
No repo file was modified (mirrors only, `h62.py build` writes to `mirr_*`).

## 0. landed 基线（可复放）

```
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl
landed quote.pyc  70/81
  [['build_current_period_df',115,108,5,12], ['check_frequency',121,120,1,21],
   ['check_limit',330,311,2,248], ['get_individual_data',312,311,1,156],
   ['get_price',230,188,0,227], ['get_real_from_zeromq',703,678,0,660],
   ['initImagedata',243,225,0,190], ['load_bars_from_hundsun',477,470,0,464],
   ['load_get_price',171,136,1,167], ['run_individual_transform',362,321,2,263],
   ['run_tick_socket',306,307,2,228]]
```
产物：`build_landed/fly__data__quoteOK.py`（1757 行）。
逐函数指令级对齐：`logs/align_<func>.txt`（`python -X utf8 align.py <pyc> build_landed/fly__data__quoteOK.py <func>`）。

> 指标说明：`h62.py` 第 4/5 列是 `len(jump_diffs)` / `len(true_diffs)`（位置比对下
> 不一致指令的条数），**不是** "missing"。`true_diffs` 巨大只说明从第一条偏差起
> 后面全部错位（典型 = 整段语句被吞），`jump_diffs` 是跳转目标编号差异条数。

## 1. 分类结论（指令级清单）

### 类 A —— 单三元 f-string 作为语句级调用的实参（**主要机制，8/11 函数**）

原始语句形如
`self.log.quote.debug(f'…{x[:10]}…{len(x) if isinstance(x, list) else 1}…{y}…')`
（块内含一条 `IfExp` 型 FormattedValue，且整串是某调用的唯一实参）。

反编译产物（landed）把它变成一条**裸 f-string 表达式语句**或 `return`，并且
**把该语句之后、同一个 merge_block 里的所有语句一起丢掉**：

```
get_price:655  ->  f'self调用函数get_price，参数为：stocks=securityNone{10!s}等{…}只代码,frequency=,start_date=,…'
   丢失指令 orig[45:67]（22 条）= 后续 4 条语句 `candle_period=None` /
   `self.check_datetime(start_date)` / `self.check_datetime(end_date)` /
   `self.check_frequency(frequency)` + `if fields is not None:` 的
   `LOAD_FAST fields; POP_JUMP_FORWARD_IF_NONE`
load_get_price:441 -> 同型；另丢 orig[42:59]（17 条）= `panel = self.load_bars_from_hundsun(…)`
   + `if len(panel.major_axis) != 0:` 的判定头
initImagedata:1476 -> 整条 debug 语句消失（orig[39:61] 22 条）
check_limit -> orig[55:77]（22 条）整条 debug 语句消失
get_real_from_zeromq -> orig[37:61]（24 条，同 A）+ orig[161:191]（30 条，见类 C）
load_bars_from_hundsun -> orig[1:41] 段 f-string 被压平（净 UNDER 7）
```

`align.py` 读数（`python -X utf8 align.py … get_price`）：
`orig=256 decomp=210 ratio=0.7811`，两个 delete/replace 簇分别对应
「f-string 被压平」与「merge 块后续语句被吞」。

**归因（落地字节行号，`core/cfg/region_ast_generator.py`）**：
`_generate_ternary()` 的 `elif merge_ctx == 'fstring':` 分支，L35898–L36018
（`grep -c "elif merge_ctx == 'fstring'" = 1`，L35898）。该分支：

1. L36008–L36014 用「merge_block 里**是否存在** RETURN_VALUE」决定
   `Return` 还是 `Expr`。由于 merge_block 通常一路走到函数尾，块尾的
   `RETURN_VALUE` 让分支误判为 `return f'…'`，并把 L36015/L36018 之后
   再无一条语句被发射（块在 L37871 被整体标记 `generated_blocks`）。
   ⇒ 类 A 的「整段语句没发射」（jumpdiff=0、true 巨大）。
2. L35946–L35981 的前缀重建是**逐条 `LOAD_*` 独立压栈**的 ad-hoc 循环，
   只认 `LOAD_*`/`FORMAT_VALUE`/`LOAD_CONST`，因此
   `x[:10]`（BUILD_SLICE+BINARY_SUBSCR）、`len(x)`（PRECALL+CALL）、
   以及 callee 前缀 `LOAD_FAST self; LOAD_ATTR log; LOAD_ATTR quote;
   LOAD_METHOD debug` 全部不被识别：栈里留下 `Name(self)`/`Name(security)`
   这类**非 Constant、非 FormattedValue** 的裸节点，CodeGen 把它们当字面量
   打进串里 ⇒ 产物串首多出 `self`、插值退化为字面文本。
   L35989–L36003 的 merge 段同理，只处理 `LOAD_CONST`，所以 ternary 之后
   的 `{frequency}`/`{start_date}`/… 全部丢失。

R63 Fix1/Fix2 已经为此写过两个正确工具，但**只接在 chain 长度 ≥2 的
`_try_build_ternary_chained_container` 上**（L41331 `if len(ternary_chain) < 2: return None`）：
- `_fstring_parts_from_segment` L41034（段内单趟栈模拟，处理 CALL/下标/切片）
- `_try_wrap_fstring_pending_call` L41198（BUILD_STRING+PRECALL+CALL(1)+POP_TOP
  ⇒ `Expr(Call(callee,[JoinedStr]))` + `post_consumer_extra_stmts`）
- `_ternary_pending_callee` L41084（从 cond_block 前缀还原跨块待定 callee）
调用点分别在 L41676 / L41708。**单三元路径（L35898）一个都没接** —— 这就是
类 A 的根因，且是同层次结构身份（同一个 `TernaryRegion`、同一个
`merge_context=='fstring'` 分类），不是启发式。

### 合成复现（可复放）

```
python -X utf8 h62.py run --arm=landed --list=synth/list.txt  --out=dump/synth_landed.jsonl
  synth/fsrepro.pyc   6/7   [['m_b',39,19,0,37]]
python -X utf8 h62.py run --arm=landed --list=list2.txt       --out=dump/synth2_landed.jsonl
  synth/fs2.pyc      4/10   [['v1',13,11,0,3],['v3',15,11,0,14],['v4',19,11,0,18],
                             ['v6',15,11,0,5],['v7',24,18,1,19],['v8',33,14,0,32]]
```
`synth/fs2.py` 的 v1…v8 是最小复现矩阵（9 行源码即可复现）：
```
def v4(self, a, c, b):
    self.log.debug(f'p{a if c else b}q')   # 单三元 + 语句级调用实参
    x = 1
    return x
```
landed 产物：`def v4(...): return f'selfp{a if c else b}q'`（调用被吃、`x=1`/`return x` 被吃）。
对照组 `v5`（f-string 内**无**三元）14/14 完全正确 ⇒ 三元是唯一触发条件。

### 类 B —— 非 f-string 的整块语句丢失（run_individual_transform / get_individual_data / build_current_period_df）
（见 §3）

### 类 C —— OVER（run_tick_socket）
（见 §3）

## 2. 候选 C1（generator）：单三元 f-string 区域的消费点判定 + 后续语句拼接

`specs/c1_fstring_consumer_dispatch.json`，anchor = 落地字节 L36004–L36018
（`joined_str = {` … `results.append({'type':'Expr','value':joined_str})`，`count==1`）。

识别条件 / 归约方式 / AST 映射已写进替换代码块注释（三要素）。
只改「消费点判定 + 语句拼接」，**不改**前缀/尾部插值重建（那是 C2 的范围），
`BUILD_STRING` 不存在时完全退回既有行为，保证 `return f'{a if c else b}'`
这类既有正确产物逐字节不变。

### 实测
（进行中）
