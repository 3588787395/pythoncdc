# MEASURED R19 —— 残余单元逐读（只读 `unit_diff.py`，绝对路径调用，产物取 site-packages 就地 `*OK.py`＝landed 字节）

| 单元 | 读数 | 该读数意味着什么 |
|---|---|---|
| `IQCommon/util/trade_info_utils.pyc::<module>.query_strategy_id` | `len orig=117 prod=116 delta=-1`；1 个真 hunk：`orig[108..109 @634] → prod[108..110]`，删 1 条 `JUMP_FORWARD`、插 2 条 `LOAD_CONST None / RETURN_VALUE` | 原字节码在 `@634` 处**跳向共用尾**，产物把汇合尾**内联**展开。与残余表 #15 登记一致，逐条复核成立。合形不复现（见 `repro_tail/README.md` 13/13 GREEN），只能整文件门 |
| `fly/data/quote.pyc::<module>.Quote.get_real_from_zeromq` | `len orig=782 prod=780 delta=-2`；hunks=5（本表只誊可读出的两条）：`orig[@3966 LOAD_FAST exc_tb]` 对 `prod[@3960 LOAD_GLOBAL exc_tb]`；`orig[@4044 LOAD_FAST exc_tb]` 对 `prod[@4048 LOAD_GLOBAL exc_tb]` | **不是**共用尾落点问题：产物把 except 处理器参数 `exc_tb` 读成**全局名**而非**局部名**（两条独立同形 hunk，偏移各差 6/4 字节＝上游长度差的影子）。⇒ 该单元应从 #15「共用尾」族改判为「处理器形参作用域」族；先前按共用尾开的票（#41 R15-11、#42 R15-12）都不会翻正它 |
| `IQCommon/logger/handlers.pyc::<module>.TWHThreadController._target` | `len orig=199 prod=197 delta=-2`；hunks=1，无成对插删可读出行 | 净 −2 且只有 1 个 hunk＝一对 `LOAD_CONST None / RETURN_VALUE` 整体未发（与 #15 登记一致）。该文件唯一失败单元 ⇒ 修好即整文件翻绿 |

## 施工提示（给下一张票，非本轮）
`exc_tb` 类读数的判据应在**异常处理器体的作用域**上：`except E as e:` 的形参在 3.11 里由
`STORE_NAME`/`DELETE_NAME` 管理但块内引用为 `LOAD_FAST`；产物发成 `LOAD_GLOBAL` 说明重建器
在该处丢了 local/global 判定（与 task #23「函数内 import 丢失」是同一作用域家族的两个面）。
两条 hunk 同形 ⇒ 一处判据可同时解两处，但 `get_real_from_zeromq` 仍有第 3~5 条 hunk 未誊出，
开票前先用 `unit_diff.py --all` 看全 5 条再定共要件。
