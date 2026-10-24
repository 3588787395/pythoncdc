# RELEASE_NOTES（rr-v5r01..r08）

产品（region 管线）修复：
- 折叠常量控制行头 NOP 族重构（游程解析 + 常量队列）与 try/finally 行位 NOP 再生
- B142 嵌套 finally 副本谱系（continue/break 穿双层 finally）
- docstring 保真（函数 + 模块级 `__doc__` 还原为字面量）
- starred-unpack 值段切分、generator send 值绑定、posonly `/` 签名链（提取→转换→AST→渲染）
- return-in-finally 无条件/条件臂归约、dict `**expr` 形保真、match 臂锚 NOP 剥离
- B214（except* 闩）尝试后按基线保护原则回退，登记 OPEN

度量与门禁（诚实口径）：
- fuzz 24/24 EQUAL；402 6617/6617；J 空间 c1/c2 missing=0、1556 全量 C1–C5、三类清单
- G1–G5 实测读数全部 FAIL 如实（BLOCKED）；G6 ASSURANCE_BLOCKED（无独立 custody）
- 判定产物集中在 attack-completeness-claims/rounds/round9/（g2b_402、g2c_46、g3_mutation、
  rule_traces、gate_report_v5r06）
