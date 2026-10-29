# if 早返回 + 尾部语句整体丢失（`_validate_epoch` 形态，rr-v5r86）

状态：**已修复**（`core/cfg/region_analyzer.py` +12/−3、
`core/cfg/region_ast_generator.py` +17，均只增不破）。
真实案例：G2c REAL46-031（`packaging/version.py`）`_validate_epoch`——
修复后产物与源逐字一致（`msg` + `raise InvalidVersion(msg)` 均在）。

## 缺陷

源：
```python
def _validate_epoch(value, /):
    epoch = value or 0
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f"epoch must be non-negative integer, got {epoch}"
    raise InvalidVersion(msg)
```
HEAD 产物：
```python
    if isinstance(epoch, int) and epoch >= 0:
        pass
    return epoch
```
**尾部 `msg=...; raise` 整体消失**——负 epoch 不再抛异常（静默校验丢失）。
最小复现 `r31_repro.py`（`f(-1)` 原抛 ValueError、产物静默返回）。

## 触发边界（变体矩阵 `r31_variants.py` 实测）

前一条语句是 BoolOp 值赋值（`x = a or b`）且其 **merge 块与 if 条件入口是
同一块**、if 首操作数是**函数调用**（`isinstance(...)`）时触发；无 `or`
前缀（v2）、单条件（v3）、尾部非 raise（v4/v5）、or 条件（v6）均正确。

## 根因（两个独立阻断点，缺一不可）

区域级证据（修复后 region dump）：`BoolOpRegion@1 blocks=[1,2,3] merge=3`
（merge 兼成员）、`BoolOpRegion@3 blocks=[3,4] merge=6`、
`IfRegion@3 blocks=[3,5] merge=6`。

1. **识别端 allowlist 缺 `PRECALL`**（`region_analyzer.py` ~35996，
   `_value_merge_hosts_next_if`）：CPython 3.11 每个 CALL 前必有 `PRECALL n`
   （调用协议固定前缀，编译器伪指令，仓库 `_R20_NOISE_OPS` 同收录），但
   「操作数构造段」校验的 `_tail_ops` 白名单没有它 → 首操作数是调用的形态
   校验失败 → Round14-A1 双角色例外失效 → **IfRegion 从不创建**。
2. **生成端 R36 伪影过滤器误杀**（`region_ast_generator.py` ~1793）：
   IfRegion 创建后，其 entry ∈ 值上下文 BoolOpRegion.blocks 且
   `block_to_region[entry] is BoolOpRegion` → 被「嵌套伪影」过滤器判
   `is_contained` 永不派发 → 链成员/体/尾部块沦为孤儿块线性重建
   （尾部语句前移丢失）。实际是指令级分区的合法重叠（pre-STORE 归上游
   赋值区域、post-STORE 归 IfRegion），不是伪影。

## 修复（均只加不破坏）

1. `_tail_ops` 加 `'PRECALL'`（含 docstring 说明）；结构性判据不变
   （语句边界消费者 + 完整操作数构造段 + 块尾条件跳转 + 恰两后继）。
2. 过滤器内豁免：**复用识别端同一谓词** `_value_merge_hosts_next_if(r.entry,
   other)` 才 `continue`——识别端不放行时此处必不豁免，逐字节保持原过滤；
   豁免仅解除该一家 BoolOpRegion 的包含判定，不跳过全循环。无指令/偏移特例。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| repro 产物 | `if: pass` + 尾部消失，`f(-1)` 静默 | 与源逐字一致（含 f-string msg + raise），运行输出与原逐字一致 |
| 变体矩阵 v1–v6 | v1 坏 | v1 修复；v2–v6 与修复前正确形态逐字节相同 |
| REAL46-031 `_validate_epoch` | `if: pass`，raise 消失 | 与源逐字一致（163–168 行）；verdict 仍 DIFFERENT（剩余 R7×4=已登记注解丢失族，范围外；R7×112+R5×4 → R7×4） |
| 三元回归（rr-v5r84 族） | — | repro 仍真三元；`tern_variants.py` 5/5 preserved |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有 B01、BOUNDARY_02） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 闸门 | 基线 `semantic_shard{0,1,2}_v5r85.json` | 见下节 |

## 全量 1556 闸门（对 v5r85 基线，三分片 offset 0/519/1038）

| 指标 | v5r85 基线 | v5r86 |
|---|---|---|
| entries | 1556 | 1556 |
| verdicts | EQUAL 1132 / ERROR 424 | EQUAL 1132 / ERROR 424 |
| 总 verdict 变化 | — | **0** |
| 回归（EQUAL→non-EQUAL） | — | **0** |
| 改善 | — | 0（REAL46-031 在 G2c 46 空间非 J 空间） |

**1 条抖动已排除**：shard2 首跑 `JS-GENEXP-020` 记为 `NO_C4`
（`decompile_failed: TimeoutExpired 20s`）——该反编译独立计时仅 **5.7s
（当前树实测）**，系三闸门分片后台并发期间叠加其它探针的负载抖动；
以正确 space 单条复跑 verdict **ERROR**（`original artifact did not
load/execute`）与 v5r85 基线记录**逐字一致**（`genexp020_recheck.json`）。
最终读数：**0 回归 0 变化**。

产物：`semantic_shard{0,1,2}_v5r86.json` + `_report.json`；比对脚本
`compare_v5r86.py`（同前法，基线换 v5r85 三分片）。

## 附：REAL46-031 剩余 R7 定性（rr-v5r85 后 6 条）

`g2c_r7_detail.py` + `r31_consts.py` 实证分解：
- 模块 co_code len/sha 差 2 字节（非语义编码差）；
- `v[49]`（`_deprecated.decorator.wrapper`）consts 3→2 与 `v[62]`
  （`Version.__replace__`）consts 98→96：`*args: object, **kwargs: object`
  与 `**kwargs: Unpack[_VersionReplace]` 的**注解 const 丢失**（产品签名
  退化为无注解裸 `*args, **kwargs`）——已登记的注解丢失族，另一根因，
  未在本轮修；
- `v[49]/v[62]` 之外的 raise-尾部丢失即本 rr 修复（R5×4 全消）。

## 诚实边界

- REAL46-031 仍 DIFFERENT（注解丢失 R7×4 在案）；不宣称 G2c 通过
  （REAL46-004 use_args、022/046 观察层、13 条仅 R7 在案）；
  `product_complete` 仍 **NOT PASS**。
- 触发边界为「or 值赋值 merge 块 == if 条件入口 + 首操作数是调用」；
  更广的 if-尾部形态以变体矩阵 + 全量闸门零回归兜底。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `r31_repro.py` / `.pyc` / `r31_repro_decompiled.py` | 最小复现 + 修复后正确产物 |
| `r31_variants.py` + `v1_and_earlyret.py` / `v2_and_plain.py` | 触发边界变体矩阵 |
| `r31_dis.py` / `r31_region.py` | 字节码与 CFG/region dump 探针（含 v1/v2 对比法） |
| `r31_consts.py` / `g2c_r7_detail.py` | R7 const 丢失定位 / judge 全量 diffs 探针 |
| `fix_patch.diff` | 两文件修复完整 diff（含判据注释） |
