## Context

- **工具链已就位**：LLM Wiki 0.6.10 便携版（`F:\Downloads\LLM-Wiki-0.6.10-windows-x64-portable`）= 桌面应用（本地 API `127.0.0.1:19828/api/v1`）+ 已编译 MCP server（stdio，`dist/src/index.js`，node ≥ 20，本机 v24 ✓）；Obsidian 已安装。opencode 当前 MCP 仅注册了 playwright。
- **知识源**：仅反编译器代码 ≈ 221k 行——core/(150k)、parsers/(63k)、bytecode/(2.8k)、utils/(4k)、pycdc.py、pycdas.py。明确排除 tests/、.trae/(11,586 文件)、scripts/、tools/、docs/、site-packages/。
- **代码现状（种子页要回答的问题）**：三代 AST 生成谱系并存——region 系（`pycdc.py:84` → RegionASTGenerator 50k 行 → RegionAnalyzer 27k 行）、v2 系（ast_builder ×3 → generate_ast_v2 26k 行）、自包含首代（control_flow.py 64KB 零内部 import）；`core/cfg/__init__` eager import 全部；8,954 个补丁标记、平均方法长 150 行（见 `.quality_baseline.json`）。
- **约束**：本变更不修改任何反编译器源码；应用数据目录位置与页面 md 格式为待验事实（应用从未首启）。

## Goals / Non-Goals

**Goals:**

- 代码 → 知识库的单向管线：sources 白名单圈定、变更可重扫、页面可判 stale
- 四类页面（modules/classes/concepts/hotspots）+ 稳定 frontmatter，Obsidian 与 MCP 双端可消费
- opencode 经 MCP 可查询/重扫，编码前先查知识库
- 种子化三批次：谱系概念页 → 全量模块骨架页 → 补丁热点页
- 首批交付即可回答"哪套生成器活着、哪些文件是补丁热点"

**Non-Goals:**

- 不重构、不删除任何反编译器代码（本变更只建知识库，重构是知识库的**产出**而非内容）
- 不把现有 docs/ rules.md 等文档作为源 ingest（它们是声明，不是事实）
- 不处理 .trae/ tests/ 迭代现场
- 不自建提取脚本入库（首批骨架指标若 app 内置扫描不足，再立后续变更）
- 不做跨机器/团队分发（便携路径本机绑定，见 Risks）

## Decisions

**D1：两段式内容生成——机器骨架 + LLM 综述，而非 LLM 全量写页**
7 个核心文件含 1,450+ 函数，LLM 逐函数写页必然产生大量低质重复页且无法维护。骨架页（metrics/frontmatter）覆盖全部白名单文件，LLM 只写概念页与热点页。备选"LLM 全写"（质量/成本不可控）与"纯机器无综述"（回答不了'为什么三代并存'这类问题）均否决。

**D2：sources 用白名单而非整仓**
project 绑定仓库根、sources 仅勾 core/ parsers/ bytecode/ utils/ + 两个入口文件。若应用不支持目录级白名单，则 project path 直接指向受限文件集所在目录的交集或用排除规则（首启验证，见 Open Questions）。理由：11,586 个 .trae 文件与海量测试输出会淹没索引与向量检索。

**D3：vault = 应用数据目录（仓库外），不建仓库内 .wiki/**
llmwiki 0.6.10 自管数据目录（README 明示"normal application data directory"），强行镜像进仓库会造成双写冲突。代价：知识库不进 git——接受，版本历史由应用自身承担；仓库保持零污染（本变更仓库内只有 openspec 目录）。

**D4：MCP 注册进 opencode（local 类型），指向便携目录绝对路径**
这是"护栏闭环"的前提：agent 改代码前 `llm_wiki_search`。备选"仅在 LLM Wiki 应用内 chat"被否决——那只服务人类不服务 agent。`LLM_WIKI_API_BASE_URL` 默认 `127.0.0.1:19828` 即可，不改。

**D5：种子化批次按信息密度排序**
1. `ast-generation-lineages` 概念页（已探明 import 图大半，一页即产生最大洞察）；2. 模块骨架页全量；3. 热点页 + Dataview 重构清单。备选"按目录顺序逐文件 ingest"被否决——先写 55 个平铺模块页再碰到谱系问题，首周无洞察产出。

**D6：页面命名 kebab-case 英文，正文中文**
仓库 docs/ 已出现中文文件名编码乱码先例；kebab-case 英文路径规避 Obsidian 链接与 Windows 编码问题，正文中文服务使用者。

## Risks / Trade-offs

- [应用数据目录/页面格式未知，可能非纯 markdown 或非 Obsidian 兼容] → 首启后第一件事实测：打开 vault 看一页；若不兼容，降级方案为"Obsidian 只浏览种子页副本/导出层"，回写仍走 app
- [MCP 依赖 LLM Wiki.exe 运行，未启动则查询失败] → 步骤清单将"起 app"置于 MCP 使用之前；opencode 中该 MCP 失败不阻塞其他任务（agent 检不到 wiki 时按无知识库模式工作并在回答中声明）
- [sources 可能不支持目录白名单，整仓 ingest 引入噪声] → 首启实测；不支持则用 app 的排除配置，仍不行则收窄 project path（Open Questions 兜底）
- [知识库漂移：代码改了页面没改] → frontmatter `content_hash` + 约定"大改后 rescan"；stale 检测列入 lint 约定
- [便携目录绝对路径硬编码进 opencode.jsonc，移动/删除即失效] → 接受（本机绑定）；条目加注释说明依赖路径
- [知识库本身成为新的文档债] → 骨架机器维护、综述按需增量（问题驱动 ingest），拒绝预先全量写完

## Migration Plan

1. 首启 `LLM Wiki.exe`，记录应用数据目录；建 project 绑定仓库根，配置 sources 白名单（实测粒度）
2. `opencode.jsonc` 注册 MCP（本地 `node .../dist/src/index.js`），验证 `llm_wiki_status`
3. Obsidian 新增 vault 指向应用数据目录，验证页面可读、反链可用
4. 种子化三批次（lineage → 骨架 → 热点），验证 `llm_wiki_search` 可命中
5. 回滚路径：删 opencode.jsonc 条目 + 删 Obsidian vault 记录 + 删 app 内 project——仓库无残留

## Open Questions（2026-09-28 已全部求解）

- ~~应用数据目录实际路径？~~ → 配置真源 `C:\Users\admin\AppData\Roaming\com.llmwiki.app\app-state.json`；项目数据在项目内 `.llm-wiki/`；WebView 缓存在 `AppData\Local\com.llmwiki.app`。
- ~~sources 配置粒度？~~ → Source Watch 根固定 `<项目>/raw/sources`，**无仓库相对白名单**；粒度只有 includeExtensions/excludeDirs/excludeGlobs/maxFileSizeMb。兜底=D2 变体：`raw/sources/` 下 4 个目录 junction（core/parsers/bytecode/utils）+ 2 个硬链入口文件，`includeExtensions += py`。
- ~~页面是否纯 markdown + wikilink？frontmatter 自定义字段？~~ → 是。`kind/patch_markers/file/content_hash` 等自定义字段被识别为 properties；`[[wikilink]]` 解析与反链面板正常。
- ~~rescan 增量粒度？~~ → `POST /api/v1/projects/{id}/sources/rescan` 即时返回 `{ok:true, changedTasks, queue}`；**已知限制**：`changedTasks` 对源文件修改恒为空（无逐文件回执），源码内容不入 search 索引（search 仅覆盖 wiki），`files?root=sources` 不遍历 junction——源侧"是否重扫"无 API 级内容证据，只能靠本地 `content_hash` 判 stale。
- ~~骨架指标 app 内置扫描是否够用？~~ → 不够（app 无 patch marker/metrics 输出）。采用外置生成器 `d:/Temp/opencode/gen_modules.py` 自算（ast 解析 method_count、正则 patch_markers、md5 content_hash）；是否入 repo 立为后续决策。

## 实施偏差（vs 原设计）

- **D3 被推翻**：知识库实际落在仓库内 `wiki/`（`schema.md`/`purpose.md` 同置），Obsidian vault = 仓库根——应用坚持 wiki 目录在项目内，"仓库零污染"不成立。缓解：`.gitignore` 屏蔽 `.obsidian/`、`.llm-wiki/`、`raw/`（junction 与本地状态不入库），`wiki/`、`schema.md`、`purpose.md` 允许提交。
- **D2 落地方式**为 junction 白名单（见上），白名单 61 文件与 `modules/` 页差集为空（含动态新增文件场景探针验证）。
- **patch_markers 口径自定义**：`#.*(修复|补丁|临时|workaround|hack|兼容|hardcode|硬编码)` 或 `def _(fix|merge|patch|fallback|hack|workaround|temp)_*` 计数（`.quality_baseline.json` 为 2026-04 旧口径且行数已漂移，不采用）。
- **Dataview 安装**：GitHub 被墙、npm 包非构建产物 → 采用 Gitee 汉化组 release zip（0.5.67）装入 `.obsidian/plugins/dataview/`；插件总开关在 `localStorage["enable-plugin-<appId>"]`，经 CDP `app.plugins.setEnable(true)` 打开；查询实测返回 10 行 = 热点清单。
- **生成脚本已入库**：`tools/kb/{gen_modules,gen_classes,check_stale}.py`（Non-Goal「不自建提取脚本入库」的既定解除条件"app 内置扫描不足"已证实）；`tools/` 不在 sources 白名单，不污染索引。
- **类页口径**：全库 279 类只收录 ≥8 方法的 68 个核心类（其余留模块页关键符号）；类页 slug = `<module-slug>--<class-kebab>`（缩写词按 ast-builder 风格断词），继承/override 仅能识别仓库内基类。
- **并行迭代风险**：round74 代理持续改 `core/cfg/region_*.py`，页面生成后即出现 stale——stale 检查器与"大改后 rescan"约定即为此设（6.2 实测捕获并复原）。
