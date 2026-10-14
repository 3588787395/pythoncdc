# REGISTER R19 负极性（主代理自测自否，逐条带读数）

## N1 `[R3-Continue]` merge 同一性放宽 —— 主代理在一次性镜像里自测，零翻正 ⇒ 不落地
靶点来自 r19t3 诊断（唯一能动 `klinedata.get_kline_by_count_new` 那条臂尾跳动的支路）。
做法：把 `core/cfg/region_ast_generator.py:21381` 的
`region.merge_block is _current_loop.header_block`
放宽为「或 `is _current_loop.back_edge_block`」，并把 `:21391` 的
`_r3t_last.argval == region.merge_block.start_offset`
放宽为「`argval ∈ {merge.start_offset, header.start_offset}`」，
另加负门禁「臂尾块不得就是循环 `back_edge_block`」（r19t3 §7 第 5 条，保住已正确的三条臂）。
锚点命中数各 1；`py_compile` 通过；镜像 `D:/Temp/r19kx` sha16 `4e924319b183bfa0`
（pristine `5066b1367b6de3c7`）。**实时仓库未写**。

```
klinedata  63/64   （基线 63/64 ⇒ 零翻正，与 r19t3 预测一致：该单元还要第二处 @974/@978）
bar        85/85   matcher 17/17   api_base 27/28   （均与基线同 ⇒ 无回退也无收获）
```

⇒ 该放宽**单独不构成可落地改动**（fires-without-flips）。留在名册里，等 klinedata 第二处
（外层 BoolOp/elif 链 merge 身份，r19t4 所在轴）解出后再作为**共要件**同时施加。

## N2 面板比较脚本自己的列错位（登记以免误读）
用 `awk -F'units=' ... split($2)` 比对 `cur=` 与 `base=` 时，
一行里有 **三** 个 `units=` 分隔段，`$2` 只是 `63/64 base=`，
于是 `$2` 的第二段永远等于字面量 `base=` ⇒ 17 行**全部**被判 DIFF。
真实读数须看整行（`klinedata: cur=units=63/64 base=units=63/64` 逐行相同），
或用第三个字段。依 [[guard-vocabulary-self-check]]：比较器必须先在已知绿的日志上自证。

## N3 面板 rig 认证（正向证据，非负极性）
`rounds/round19/panel17.sh pristine_certify`：用 landed 代码**重新生成** 17 个面板文件的产物
（写到 `D:/Temp/panel17_pristine_certify/`，不碰 site-packages）再判决，
17/17 行 `cur == base`，与门 18 封盘逐字相同
⇒ ①rig 可用；②就地产物确为当前代码的产物（无「陈旧产物读绿」漂移）。
