# R14-05 镜像补丁存档（未落地）

- `region_analyzer.py`：子代理交付的完整替换文件（相对 core `+221 −5` 行）。
  新增 helper：`_r16_cc_cleanup_hop` / `_r16_boolop_cc_run_operand` /
  `_r16_cc_operand_success_edge`；接入点（相对当时 core 的行号）：
  merge 计算族 19675/19717/19757、臂归属 20680、`_boolop_resolve_merge` 27998、
  链走认领守卫与尾钳 29792/29975/29977/30010/30093、链末成员 30537。
- `patch_r16.py` / `patched_gate.log`：其施加器与门跑日志。

判决：`repro_arm/a01_not_and_or_cc`、`a02_not_and_or_cc_tailreturn`、
`a03_while_then_body` 在该补丁下仍 **1/2 红**（子代理自述 + 主代理两次独立复判
20:07、20:13 一致），且 api_base 回退 ⇒ **不安装**。存此避免下一轮重复实现同一 221 行。

下一手（诊断票）：在补丁已施加的镜像里追 trace，回答「起链在 a01/a02/a03 上
仍返回 None 的具体谓词与实测值」——即 `_r16_boolop_cc_run_operand` 的哪一项
在哪个块上为假；未拿到该读数前不再动 core。
