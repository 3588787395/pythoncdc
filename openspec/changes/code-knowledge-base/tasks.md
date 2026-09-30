## 1. 首启与项目配置

- [x] 1.1 运行 `LLM Wiki.exe` 完成首启，记录应用数据目录实际路径（Open Questions #1）
  - 结论：应用数据 = `C:\Users\admin\AppData\Roaming\com.llmwiki.app\app-state.json`（全局配置：apiConfig/llmConfig/sourceWatchConfig/projectRegistry 等）；项目数据在项目目录内（`.llm-wiki/` + `wiki/` + `raw/` + `.obsidian/`）；WebView 缓存在 `AppData\Local\com.llmwiki.app`。本地 API `http://127.0.0.1:19828`（`/health` 免鉴权）。
- [x] 1.2 创建 project 绑定 `F:\Downloads\pythoncdc-main`，配置 sources：仅 core/ parsers/ bytecode/ utils/ pycdc.py pycdas.py
  - 落地：`raw/sources/` 下 4 个目录 junction（core/parsers/bytecode/utils）+ 2 个硬链文件（pycdc.py/pycdas.py）；`sourceWatchConfig.includeExtensions += py`、`excludeExtensions += pyc,pyo,pyd`；白名单内 `__pycache__` 已清（gitignored 可再生）。注意：junction 不被 `files?root=sources` API 遍历，但被 Knowledge → Raw Sources 索引遍历；`mklink /D` 需管理员，故用 junction。
- [x] 1.3 实测 sources 配置粒度（能否目录白名单），不支持时按 design D2 兜底方案收窄并记录结论（Open Questions #2）
  - 结论：Source Watch 根目录**固定为 `<项目>/raw/sources`**，不支持仓库相对目录白名单；粒度 = `includeExtensions` / `excludeDirs` / `excludeGlobs` / `maxFileSizeMb`（按项目存 app-state.json `sourceWatchConfig`）。按 D2 兜底：白名单代码经目录 junction 链入 `raw/sources/`（不复制），扩展名加 `py`；`tests/`、`.trae/` 不建链即天然排除。
- [x] 1.4 验证 spec `code-kb-sources` 场景：扫描结果中无 .trae/、tests/ 等白名单外派生内容
  - 实测：Knowledge → Raw Sources = 61 条，与白名单（61 个 .py）双向差集为空；无 tests/、.trae/、*.pyc。

## 2. MCP 注册与验证

- [x] 2.1 在 `~/.config/opencode/opencode.jsonc` 注册 MCP：local 类型，command 指向便携目录 `mcp-server\dist\src\index.js`（注释标注依赖路径与"应用须先运行"）
  - 备注：`app-state.json` → `apiConfig.mcpEnabled=true` 需手工置位（GUI 开关），`allowUnauthenticated=true`（本地免 token）
- [x] 2.2 验证 `llm_wiki_status` / `llm_wiki_projects` 返回正常（应用运行中）
  - stdio 直连验证通过，currentProject=pythoncdc-main；11 个工具全部注册
- [x] 2.3 验证应用停止时 MCP 工具连接失败可辨识（spec `code-kb-query` 降级场景）
  - 结果：`-32603: LLM Wiki API request failed. Is the desktop app running? fetch failed`

## 2.5 已修复缺陷（实施中发现）

- [x] `.llm-wiki/file-change-queue.json` 由 PowerShell 写入带 UTF-8 BOM，导致 File Sync 报 `Failed to parse …: expected value at line 1 column 1`；已去 BOM（`[IO.File]::WriteAllText` + `UTF8Encoding($false)`），Rescan 后错误清除。**规则：写入项目的 JSON/MD 一律无 BOM。**

## 3. Obsidian 接入

- [x] 3.1 用 Obsidian 打开应用数据目录注册为 vault
  - 实测：Obsidian 1.13.7（`d:\Program Files\Obsidian\Obsidian.exe`）；exe 传路径参数无效，直改 `%APPDATA%\obsidian\obsidian.json` 注册 vault（path=项目根, open=true）后启动即打开。vault = 整个仓库根（文件树含 site-packages 噪音，未处理）。
- [x] 3.2 实测页面是否纯 markdown + `[[wikilink]]` 兼容、frontmatter 是否可写自定义字段（Open Questions #3），记录结论
  - 结论：①纯 markdown ✓；②`[[index|Wiki Index]]` wikilink 可解析（反链面板识别）✓；③自定义 frontmatter 字段（`kind`/`patch_markers`/`file`）被识别为 properties 并可编辑，数字字段正常 ✓。属性面板读取= `.metadata-property`。
- [x] 3.3 验证反链面板：任一页可见其被引用者（spec `code-kb-query` Obsidian 场景）
  - 实测：在 overview 写入 `[[index|…]]` 后打开 index.md，执行 `backlink:toggle-backlinks-in-document`，面板显示 "1 条反向链接 → overview"。CDP：Obsidian 启动加 `--remote-debugging-port=9223`。

## 4. Schema 与索引

- [x] 4.1 将四类页面分类学 + frontmatter 必填字段（file/content_hash/kind/lines/patch_markers/method_count/sources）写入知识库 schema 约定（应用内 schema/AGENTS 等效位置），命名 kebab-case 英文（spec `code-kb-pages`）
- 补记4.1：（已写入 schema.md：四类分类学 + 必填 frontmatter + kebab 命名 + 无 BOM 约定）
- [x] 4.2 创建总索引页 index.md，四类分节并可达任一已有页面
- 补记4.2：（index.md 四类分节，Modules 节含 61 个模块页链接、Concepts 节含种子概念页，均一跳可达）

## 5. 种子化三批次

- [x] 5.1 批次1：创建概念页 `ast-generation-lineages`——三代谱系 import 图 + 三胞胎 ast_builder，含 `pycdc.py:84` 等 file:line 锚点（spec `code-kb-query` 谱系场景）
- 补记5.1：（wiki/concepts/ast-generation-lineages.md：三代谱系，锚点 pycdc.py:18/:84/:121/:493，含谱系对比表与重构含义）
- [x] 5.2 批次2：生成白名单全部源文件的模块骨架页，验证与白名单差集为空（spec 覆盖场景）
- 补记5.2：（61 个骨架页生成于 wiki/modules/，校验 whitelist↔pages 双向差集为空、无 BOM；页含 file/content_hash/lines/patch_markers/method_count；生成器 d:/Temp/opencode/gen_modules.py）
- [x] 5.3 批次3：聚类补丁标记创建热点页，链接对应模块页，并验证 Dataview 查询 `kind = "module" AND patch_markers > 100` 可产出重构清单（spec `code-kb-pages` Dataview 场景）
- 补记5.3：wiki/hotspots/patch-marker-hotspots.md（10 个 >100 模块 + 100 行窗口聚类）+ wiki/queries/hot-modules.md；Obsidian Dataview 0.5.67 查询实测返回 10 行且与热点清单一致。Dataview 经 Gitee 汉化组 release zip 安装（GitHub 被墙，npm 包非构建产物），插件开关 localStorage enable-plugin-<appId> 经 CDP setEnable(true) 打开。

## 6. 同步闭环与验收

- [x] 6.1 修改一个核心文件后调用 `llm_wiki_rescan_sources`，确认变更进索引（spec `code-kb-sources` 重扫场景）
- 补记6.1：（探针修改 utils/stack.py → POST /api/v1/projects/current/sources/rescan 返回 {ok:true}；UI 源过滤器 61 项含该文件；回滚后 md5 复原。限制：changedTasks 恒空、源内容不入 search、files 端点不遍历 junction → 无逐文件内容回执，已记 design.md Open Questions）
- [x] 6.2 确认源变更后骨架页 `content_hash` 不一致可判定 stale（spec stale 场景）
- 补记6.2：（d:/Temp/opencode/check_stale.py 按 frontmatter content_hash 对比源 md5：基线 61 检查 0 stale；实测捕获两次真实漂移——①并行 round74 改 region_*.py → 2 stale → 重新生成后 0；②stack.py 探针 → 1 stale → 回滚后 0）
- [x] 6.3 运行知识库 lint，断链 wikilink 被报告（spec `code-kb-pages` 断链场景）
- 补记6.3：（链接 lint：67 页 150 个 wikilink 断链 0；含 index 一跳可达补链 log/queries/hotspots；执行方式=本地 lint 脚本，可经 MCP read_file/search 复核）
- [x] 6.4 走查三个 spec 的全部场景，逐条确认通过并记录遗留 Open Questions 结论
- 补记6.4：（三 spec 走查全过：code-kb-sources=首导 61/排除测试与 pyc、rescan ok、app 未运行报错可识别(2.3)、stale 判定实测；code-kb-pages=新增 .py 探针→骨架页 62/62 差集空→清理回 61、概念页 sources 注记、Dataview WHERE kind=module AND patch_markers>100 返回 10 行、断链 0、index 一跳可达 67 页；code-kb-query=MCP status/search(hybrid token+graph hits)/read_file/rescan 全通、停止时失败可识别、种子三批次齐、热点清单=查询结果。结论与限制已写入 design.md Open Questions 与「实施偏差」节）

## 补充批次（2026-09-28 收尾）

- [x] 7.1 类页批次：68 个核心类页（≥8 方法；全库 279 类），frontmatter 含 file/content_hash/class/defined_at/method_count/bases + 仓库内基类 override 推导；`wiki/classes/` 挂入 index。
- [x] 7.2 模块页内容增强：摘要（模块 docstring/类函数计数）+ 关键符号（类带类页链接、体长前 20 顶层函数带行号）；BOM 文件（region_ast_generator）method_count 修复（剥 U+FEFF 再解析）。
- [x] 7.3 生成脚本入库 `tools/kb/`（gen_modules/gen_classes/check_stale，design Non-Goal「脚本不入库」按既定条件解除——app 内置扫描不足已证实）。
- [x] 7.4 overview.md 重写为真实状态总览（规模表/首批结论/维护约定）。
- [x] 7.5 终检：135 页、563 wikilink 断链 0、module↔whitelist 差集空、class frontmatter 完整、stale 0、`openspec validate` 通过。
