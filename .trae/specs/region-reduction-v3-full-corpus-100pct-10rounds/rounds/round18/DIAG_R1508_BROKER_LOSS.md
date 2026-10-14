# DIAG R15-08 — trade_live_broker 大缺失家族（_process_order / _process_cancel_order）首测

## 读数（修正口径：忽略 NOP/CACHE/EXTENDED_ARG，跳转目标单独统计）

| 单元 | orig 指令 | prod 指令 | 内容差 | 落点差 |
|---|---|---|---|---|
| `<module>.TradeLiveBroker._process_order` | 507 | 42 | 4 hunks | 2 |
| `<module>.TradeLiveBroker._process_cancel_order` | 333 | 40 | 3 hunks | 2 |
| `<module>.TradeLiveBroker._process_tick_order` | 182 | 182 | **0** | 1 |

⇒ 同文件同族：两个单元整段主体丢失（−465 / −293），第三个只差 1 处落点。

## _process_order 的实测形态（不是"块未被认领"）

orig 关键段（`dis` 口径，忽略 CACHE）：

```
@90  …len(self.open_orders) > 0
@94  POP_JUMP_FORWARD_IF_FALSE  to 3128     ← 假边跳到循环尾 3128
@98  LOAD_DEREF self; LOAD_ATTR lock; LOAD_METHOD acquire; CALL; POP_TOP
@148 self.open_orders.pop(0); UNPACK_SEQUENCE; account; order
…（循环体的全部内容，直到 @3126）
@3128 循环尾 / 回边
```

产物（`site-packages/.../trade_live_brokerOK.py:423` 起）：

```
while len(self.open_orders) > 0:
    if self.trade_status in (TRADE_STOP, TRADE_DELETE):
        system_log.debug(...)
        continue
    break                      # ← orig 的 @94 真边体被写成 break（假边落点 196）
    try:                       # ← 后续体被发射为 break 之后的死代码
        amount = order._amount
        …
```

即：**@94 的条件臂身份被颠倒** —— orig 里真边是循环体（`with self.lock: …`）、
假边是循环尾 3128；产物把真边发射成 `break`、把体留在 `break` 之后成为不可达代码，
因此重编译后 507 条只剩 42 条（缺失的 424 条在 orig @470..@3126 段）。

## 与既有票的关系

- 形状与 R14-05（or-run 未建立 BoolOpRegion ⇒ 父 IfRegion 臂入口/merge 身份错）
  同源：**臂入口与 merge 身份必须同时决定**（DIAG_R1405 §5），差别在本族里
  表现为"真边被认成循环出口"。
- 与本轮已回退的 T12-11（批量认领吞嵌套语句）不同：这里块都在区域内、
  都被发射，只是发射位置在 break 之后。

## 下一票的施工点（尚未验证，禁止在未复现前动手）

1. 用 5–8 行最小复现：`while L: if g: continue` + `if c: <with …: 体>` + 尾处理，
   检查识别端 ForRegion/WhileRegion 的 `exit_block`/`body_blocks` 与
   内部 IfRegion 的 `then/else/merge` 是否把 @94 型"真边=体、假边=循环尾"读反。
2. 判决只用 `pycdc.py --region` 产物 + `pyc_verify single`；先复现 −465 形态再谈改动。
