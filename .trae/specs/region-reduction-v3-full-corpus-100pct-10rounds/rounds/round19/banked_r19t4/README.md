# R19-T4 镜像补丁存档（判决 FALSIFIED，未安装）

- `region_analyzer.py`：完整替换文件，sha16 `5ea802f2975b1f35`，32748 行，全 CRLF，`py_compile` 通过。
  实时仓库 `core/cfg/region_analyzer.py` 未被写过（仍为 `640d33a77dcb71c2`）。
- `FIX_T19-1b.md`：阶段读数；`banked_c1_only_inert.py`：已单独证明惰性的一个调用点臂。
- 面板**未跑**（阶段 3 未过，工程师自述不给面板数），故本存档无 collateral 主张。

## 读数（镜像，基线先复现：api_base 27/28、strategy 26/27、6 个电池全同）

```
api_base  27/28 -> 27/28   差形变化：hunks=0 landings=2 -> hunks=1 landings=3
          @1006 那条落点差**消失**，条件真的折叠成
          `if not include:` 套 `if A > B or lo < x <= hi:` 且带 @1040 臂体；
          但 @1098..@1198 的 elif/else 语句组**整组不再发射** => judge_diff 仍在
strategy  26/27 -> 26/27   与基线逐字节相同（该判据不触及它的走链；其卡点是 W14-A 尾钳方向）
```

## 本轮买到的两点结论（下一票的直接前提）

1. **Blocker B 已解，且主代理原先写的“run 发现顺序”前提在 pristine 字节上是错的。**
   独立进程逐 break 探测：真正断的是 pristine `:29977` 的 `if ft_succ in claimed: break`，
   `ft_succ = B@1008`，owner 是 `IfRegion(entry=1008, chained_compare_ops=2, blocks=[1024], merge=1040)`；
   根本没有任何判据在读 `block_to_region[B@996]`。⇒ 名册/票据里“兄弟 run 按偏移顺序发现”
   这一句作废，已在此更正。
2. **Blocker A 是唯一的门。** 父 `IfRegion entry=B@992` 的 then 收集**从子区入口 B@996 起步**，
   一路下沉进子区内部（B@1024/1034/1036）与子区臂体 B@1040，
   于是子区 merge B@1098 永远成不了父区的臂边界，elif/else 链无处发射。
   归处不在 `_collect_branch_blocks` 自身（其 docstring 禁止在此放归属逻辑），
   而在**调用方停止集**：`get_if_branch_boundary_stop` / `[R31-B]`（`:20366`、`:22744`）。
   `_main_inline_boolop_chain` 这条路对本形不可用（单一 `op` 的链 + `:19527-:19594` 的
   IF_FALSE/`argval==merge` 硬拒绝），除非同时动 `region_ast_generator.py`。
