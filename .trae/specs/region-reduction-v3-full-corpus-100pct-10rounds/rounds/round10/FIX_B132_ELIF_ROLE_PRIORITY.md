# Round 10 FIX 票 B132：`matcher.DefaultMatcher.match` elif 臂 —— 发射端三点协同修复

**范围**：只实现 DIAG_B131 判定的发射端机制；不改 `core/`，不改分析器角色；镜像施工，交付 patch。
**Mirror**：`D:/Temp/r132b/wt`（`core/ bytecode/ parsers/ utils/ scripts/ pycdc.py` 逐文件 sha256 对齐仓库）。
封表校验：`core/cfg/region_ast_generator.py = e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74` ✓
`core/cfg/region_analyzer.py = 38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e` ✓

## 0. 先裁决 DIAG 的内部矛盾（§三.3「修分析器」 vs §六.3「分析器惰性」）

在封表字节 `e9a8f65f…` 的 `core/cfg/region_ast_generator.py`（发射端）实测标识符读数（定义 vs 使用分开数）：

| 标识符 | 发射端引用数 | 说明 |
|---|---|---|
| `block_roles`（复数属性，直接读） | **0** | 发射端从不直接读分析器的 `block_roles` 字典 |
| `get_block_role(`（访问器调用） | 102 | 发射端通过访问器间接读角色（`get_block_role` 内部 = `self.block_roles.get(...)`） |
| `BlockRole`（枚举类引用） | 186 | 均为对 `get_block_role` 返回值的比较，非读 `block_roles` 字典 |
| `IF_ELIF_CONDITION`（§三.3 拟赋予的角色） | **0** | 发射端从不读这个具体角色 |

三个丢弃点（`:16140-16177`、`:19307-19324`、`:54886-54921`）实测 `get_block_role`/`block_role`/`BlockRole`
命中数均为 **0** —— 三条路径的判据全是「区域 entry 身份 / 块集成员 / 块末 opcode / 后继身份」，
一条都不查角色。

**结论**：`block_roles` 原始属性在发射端 0 读，且 §三.3 拟修正的那个角色 `IF_ELIF_CONDITION`
在发射端 0 读，三个丢弃点 0 角色读 ⇒ **§六.3 成立**：把臂入口身份修进分析器角色表对本缺陷产物零影响，
**惰性**。**§三.3 与 §五末句「单点=修 region_analyzer」作为落地判据作废**（角色优先级修正本身仍值得做，
属分析器可解释性改进，非本缺陷落地判据）。落地机制 = 下述三个发射端站点。据此把 §七 追加进 DIAG 文档。

## 1. 基线（镜像实测，HEAD 字节）

`python -X utf8 pycdc.py matcher.pyc -o prod/matcher.py` →
`pyc_verify single` = **`units=16/17 success_rate=94.12%`**，唯一失败单元 `<module>.DefaultMatcher.match: Failure: Different control flow`。
被吞语句 `if order.asset.symbol[:3] in ('688','689'):`（块 @2164，10 指令）应在 `else:`(产品 157 行) 体内、
与 `'300'` 链（产品 167 行）同缩进（28 空格）作兄弟语句出现。
