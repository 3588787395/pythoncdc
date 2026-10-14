# 在飞候选快照（主代理独立复测，未安装；仓库 core 始终 5066b1367b6de3c7 / 640d33a77dcb71c2）

镜像复测方法：把候选整文件装进**一次性 scratch 镜像**（`D:/Temp/r19t1x`、`D:/Temp/r19t4x`，
由当前 landed 树复制而来），在镜像里跑电池与 `pycdc.py --region` 产物 + `pyc_verify single`；
实时仓库与 site-packages 就地产物均未被写。

| 时刻(本地) | 来源 | 文件 | sha16 | 相对 landed 基线的改动 | 复测读数 |
|---|---|---|---|---|---|
| ~00:03 | r19t1（order_api） | `core/cfg/region_ast_generator.py` | `b5795b6be150324f` | 276 行（`+`/`<`/`>` 计数） | `repro_orderapi GREEN=2 RED=3`（与基线同分）；产物形态**变差**：IfExp 被展成 `if/else` 语句，`o5` 两条臂变成裸字符串字面量（`\"\"\"buy\"\"\"`）；`repro_arm GREEN=0 RED=3`、`repro_ccneg GREEN=3 RED=1` 均未动 |
| ~00:04 | r19t4（api_base/strategy） | `core/cfg/region_analyzer.py` | `dd49dc790c77de61` | 2087827 字节，mtime 23:58 | `api_base 27/28`、`strategy 26/27`、`klinedata 63/64` ⇒ 该快照**零翻正** |

判决口径：两份快照都不满足「先翻单元再谈落地」（fires-without-flips），故一律不装。
本表的作用是：①留档工程师中途状态，避免下一轮把同一实现再走一遍；
②证明主代理没有把「子代理自述」当读数——这里全部是自己跑的。
