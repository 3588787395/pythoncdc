## ADDED Requirements

### Requirement: 源范围白名单
知识库 SHALL 仅跟踪反编译器代码：`core/`、`parsers/`、`bytecode/`、`utils/`、`pycdc.py`、`pycdas.py`。其他内容（`tests/`、`test_repros/`、`.trae/`、`scripts/`、`tools/`、`docs/`、`patterns/`、`site-packages/`、`openspec/`）MUST 被排除在 sources 之外。

#### Scenario: 首次配置 sources
- **WHEN** 在 LLM Wiki 中为绑定 `F:\Downloads\pythoncdc-main` 的 project 配置 sources
- **THEN** 仅白名单目录与文件被登记为源，`.trae/`、`tests/` 等不在源列表中

#### Scenario: 非反编译器内容不入库
- **WHEN** 执行全量扫描/重扫描
- **THEN** 索引与检索结果中不出现白名单外文件派生的页面

### Requirement: 代码变更后可增量重扫描
系统 SHALL 在反编译器代码变更后，可通过 MCP 工具 `llm_wiki_rescan_sources`（或应用内等效操作）触发重扫描，且重扫描 MUST 在 LLM Wiki 应用运行、本地 API（默认 `127.0.0.1:19828`）可用时成功返回。

#### Scenario: 修改核心模块后重扫
- **WHEN** `core/cfg/region_analyzer.py` 被修改后调用 `llm_wiki_rescan_sources`
- **THEN** 该文件的变更被扫描进索引，工具返回成功

#### Scenario: 应用未运行时的失败可辨识
- **WHEN** LLM Wiki 应用未运行时调用 `llm_wiki_rescan_sources`
- **THEN** 调用以连接错误失败，agent 能据此降级为无知识库模式而非静默成功

### Requirement: 页面与源的可追溯绑定
每个由源文件派生的骨架页 SHALL 在 frontmatter 中记录其源文件路径与源内容摘要（`file` 与 `content_hash` 字段），使页面能否判定为 stale（源 hash 与页面记录不一致）。

#### Scenario: 源变更后可判定 stale
- **WHEN** 某源文件内容变化且其骨架页尚未更新
- **THEN** 页面 frontmatter 中记录的 `content_hash` 与当前源文件 hash 不一致，该页可被标记为 stale
