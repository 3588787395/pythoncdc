# Round 28 取证与取舍（arm-design）

## 探针：站点是怎么定出来的

`core/` 全程未改；三份镜像由 `D:/Temp/r27self/r27.py build --spec=… --dst=probe|cand*` 生成，
`build()` 每次先断言 pristine `mirr_head` 与工作树核**逐字节相同**，再按锚点唯一性打补丁。

探针 `logs/probe28_spec.json` 在两处打戳（都只在目标块上打印，stderr）：

* `P1` —— `_discover_predicate_and_chain` 反向收集循环里、三条既有守卫都通过之后的候选接受点；
* `P2` —— 链返回点（J2 守卫之前）。

单文件跑 `site-packages/fly/common/custom_tools.pyc`（`run --arm=probe`）⇒

```
[R28P1] p=254 cur=262 curcond=None gen=True pure=True elifcond=[]
        own=[('BoolOpRegion', None, [246, 420], [254, 246]), ('Region', None, [254, None], [254])]
[R28P2] chain=[254, 262] gen=[False, False] pure=[True, True]
[R28P2b] tail=262 head=254
```

`P2` 的 `gen=[False, False]` 是探针自身的口径缺陷（那里按 offset 查 `generated_blocks`，
而该集合存的是块对象）；块对象口径在 `P1`：`gen=True`。结论只取对象口径那一处。
`full log: logs/probe_stderr.txt`。

## 三个变体的实测对照（同一 402 文件 A/B，head 为 pristine 镜像）

| 变体 | 判据 | 靶子 | 402 读数 | 结论 |
|---|---|---|---|---|
| a（宽） | `p in self.generated_blocks` | `6/6` | `SAME=400 IMPROVED=1 MOVED=1 REGRESSION=0` | 否 |
| b（窄） | p 属另一区域的 `blocks` 成员 | `6/6` | 与 a **完全相同**（同一 MOVED） | 否 |
| c（采纳） | 上式 **且** `_chain_block_is_pure(p)` | `6/6` | `SAME=401 IMPROVED=1 MOVED=0 REGRESSION=0` | **落地 = R28-A** |

a 与 b 读数逐条相同，说明 `quote.pyc` 那处误伤块同时满足两种认领描述，宽窄之分在此不起作用；
起作用的是**纯性**。规格文件：`logs/cand28a_spec.json`、`logs/cand28b_spec.json`、
`logs/cand28c_spec.json`；落地文本（加注释＋docstring 计数）：`logs/cand28final_spec.json`。
正式镜像产物与 c 在 402 个文件上 `sha` 差异 0 条。

## c 的否决证据（为什么纯性必须是合取项）

带打戳的 c 在 `quote.pyc` 上恰好一次：

```
[R28C] suppressed p=144 cur=332 pure=False chain=[332]
```

块 144 已登记在 `generated_blocks`（它的日志语句先被发射过），但它**自带前导语句**，
正是本回退 docstring 里「链首允许前缀语句，提升为 pre_stmts 是程序序保真的」那一类；
a/b 在此放弃整条链，连带丢掉那条 f-string 与合取支 `os.path.exists(...)`，
`load_bars_from_hundsun` 由 `477/470` 变 `477/446`。

## 线 A（异常尾声）否证留档

三份抑制型候选与它们的 17 文件金丝雀读数在 `D:/Temp/r28diagA/`
（`spec_r28a/b/c.json`、`ab_head_w17.jsonl`、`ab_r28b_w17.jsonl`、`ab_r28c_w17.jsonl`、
`strict_w1_head.txt`、`NOTES` 类）。要点：靶子 `14/15→15/15` 与合成复现 `6/7→7/7` 都成立，
但 `files fully matched a=10 b=4`，全量同样回退 12 个文件；
真实缺口是产物侧少了一份 `POP_EXCEPT; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE` 内联副本
（`orig[302:305]`），属发射侧，不是抑制侧。
