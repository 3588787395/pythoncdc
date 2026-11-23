# site-packages 第三方依赖 vendor 溯源（Task 122.12 / 122.13）

目的：J 空间 374 条 site-packages 语义 ERROR 的根因是原始 pyc 的模块级硬 import
第三方包，仓库与本机均无。本文件记录向仓库 `site-packages/` 补齐的每个包的
来源、版本、SHA256 与验证证据。wheel 原件留档于
`D:\temp\opencode\cl_layout\g4d\vendor_deps\`（不入库；以 SHA256 保证可复现）。
完整逐轮 provenance 参见同目录 `PROVENANCE.md`（r197 轮）与
`PROVENANCE_v3.md`（r198 轮，含 105 行 git status 全清单）。

- 解释器：D:\Python\python.exe（3.11.7 win64）
- PyPI 索引：mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
- 安装方式统一：`pip install --no-deps --no-compile --target <repo>/site-packages <wheel>`
- 既有 IQEngine/IQCommon/IQData/fly 零触碰（git tracked 零 M）

## 已 vendor（r197，2026-11-23）

| 包 | 版本 | wheel | SHA256 | 触发条目数 |
|---|---|---|---|---|
| logbook | 1.10.1 | logbook-1.10.1-cp311-cp311-win_amd64.whl（201,386 B） | `30272eab78a9acde4d9c4056d47b3fdd3dfe9cd91eb2901339a9dac819953103` | 20 条（IQEngine 10＋fly 10；链：IQEngine/utils→IQCommon/logger、flytools→IQCommon/exception→IQCommon/logger、flytools L39 直接） |
| tornado | 6.6.1 | tornado-6.6.1-cp311-abi3-win_amd64.whl（535,806 B） | `5cb82ca38596e1350fceaf994f287847f82f7b8436380d36ba0937a03107d0ee` | 10 条（IQCommon/trade_info_utils.py L48 直接） |

验证：全新进程 `import logbook, tornado` 解析到仓库路径；`logbook.Logger`/
`logbook.StreamHandler`/`tornado.web`/`tornado.ioloop` 全 OK；版本 1.10.1/6.6.1。
37 条样本复测：5 条翻转 EQUAL（JS-DECORATOR-001/002/005/006/007，fly/aes_encrypt
家族——其链止于 logbook），守卫四断言全 PASS（c3.sha256 37/37 逐字一致）。

## .pyd 提交口径

logbook/`_speedups.cp311-win_amd64.pyd` 与 tornado/`speedups.pyd` 被根 `.gitignore`
的 `*.pyd` 忽略，需 `git add -f` 提交（dist-info RECORD 引用它们；不提交则 RECORD
与内容不一致）。两包均有纯 Python 回退（logbook base.py:29-40 → `_fallback`；
tornado util.py:530 websocket_mask），但按 RECORD 完整性原则连 .pyd 一并入库。

## 依赖事实（如实）

- logbook 1.10.1 硬依赖 `typing-extensions>=4.14.0`（base.py L19 等模块级
  `from typing_extensions import deprecated`）：当前由宿主 D:\Python 的
  typing_extensions 4.15.0 满足 → 仓库 site-packages 对 logbook **非自包含**；
  换无 typing_extensions 的环境 import 将失败。已下载
  typing_extensions-4.16.0-py3-none-any.whl（45,571 B，SHA256
  `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8`）留档，
  随 pyzmq 一并 vendor（Task 122.13）以恢复自包含。
- tornado 6.6.1 零硬依赖（Requires-Python >= 3.11）。

## 已 vendor（r198，2026-11-23，Task 122.13）

| 包 | 版本 | wheel | SHA256 | 触发条目数 |
|---|---|---|---|---|
| pyzmq | 27.3.0 | pyzmq-27.3.0-cp311-cp311-win_amd64.whl（658,252 B） | `df98c790f86b6aa2378b4bb94dec7b85b0adb195b880b41e429a4990aed2a8c9` | 25 条样本残留 ERROR（v2 probe 27/27 `No module named 'zmq'`；含 2 条 t30-NO_C4 暂态） |
| typing_extensions | 4.16.0 | typing_extensions-4.16.0-py3-none-any.whl（45,571 B） | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | logbook 1.10.1 硬依赖 >=4.14.0；vendor 后仓库自包含（原由宿主 4.15.0 代付） |

验证：全新进程 `-X utf8`（sys.path.insert(0, repo site-packages)）：
`zmq.zmq_version()=4.3.5`（libzmq 原生装载成功，静态链入 `_zmq.pyd`）、
`zmq.__version__=27.3.0`、typing_extensions 解析到仓库 4.16.0（宿主 4.15.0 对照，
宿主确无 zmq ⇒ 非污染源）；logbook 1.10.1/tornado 6.6.1 既有路径不受影响。
METADATA：pyzmq Requires-Python >=3.9，Requires-Dist cffi 仅
`implementation_name=="pypy"`——CPython 无硬依赖，`--no-deps` 只装 pyzmq 即可
（probe 实测 27/27 越过 zmq 层）。

`.pyd` 提交口径（r198 延续 r197 先例）：`zmq/backend/cython/_zmq.cp311-win_amd64.pyd`
（1,075,200 B）被根 `.gitignore:5 *.pyd` 忽略，`git add -f` 入库。注意实测行号：
`*.pyd` 在第 5 行（第 7 行是 `*.so`）。

## 第四层收口结论（r198）：内部 Linux-only 扩展墙

pyzmq/typing_extensions vendor 后，27/27 残留从 `No module named 'zmq'` 前进到
`ModuleNotFoundError: No module named 'IQCommon.data.TickDataCache'`
（probe_underlying_v3.json，elapsed 3.5–21.8 s，链执行更深后死亡）。X＝公司内部
Cython 扩展，非 PyPI 发行版，pip 不可装：语料唯一制品
`site-packages\IQCommon\data\TickDataCache.cpython-311-x86_64-linux-gnu.so`
（2,753,976 B，ELF 魔数＝Linux x86_64）。Windows CPython
`EXTENSION_SUFFIXES=['.cp311-win_amd64.pyd','.pyd']`，`.so` 不在候选 ⇒ import
系统直接 ModuleNotFoundError。直接 traceback（co_filename 内嵌
`./fly_docker_py311/`）：`IQCommon/common/__init__.py L8` →
`IQCommon/common/main.py L92`（模块级 `from IQCommon.data.TickDataCache import
GetTickData`；mainOK.py 等价序列 L18）。

**import 链 vendor 路线到此收口**（预算消耗：追加 vendor 包 0/8、probe 迭代 1/6）：
语料内 Linux ELF `.so` 共 9 个（8× cpython-311-x86_64-linux-gnu ＋ fly pycrypto
cpython-35m），TickDataCache 是链抵达的第一个；剩余层不是 PyPI 可操作项——除非
换 Linux 宿主或取得内部扩展的 Windows 构建，超出仓库边界。27 条残留 ERROR 根因
定性＝**语料制品平台缺口**（Windows 宿主不可装载），非依赖缺失、非反编译缺陷。
后续处置走语义行「镜像异常等价」裁决路线（原始与产物两侧同异常 ⇒ 模块边界内
等价证据），另行登记。

37 条样本复测（sample_out_v3.json，exit 3 如实）：EQUAL 10 / ERROR 27，翻转表
`EQUAL→EQUAL 10 / ERROR→ERROR 27`，新增翻转 0、回退 0、**DIFFERENT 0**；守卫四断言
全 PASS（5 守卫 EQUAL 无 package_root 字段；c3.sha256 37/37 与 t30/前两轮样本
三重一致；根因 27/27 统一 TickDataCache）。5 条 r197 翻转（JS-DECORATOR-001/002/
005/006/007）保持 EQUAL 未回退。judge_sha256 与前轮相同（d31948b3…a9cc38）。

## probe 口径警示

`D:\temp\...\probe_semantic_error.py` 组 case **不注入 package_root**——其输出
是"无布线第一层失败"，不能用于 vendor 后的根因定位（已实证：tornado 已入库仍报
"No module named 'tornado'"）。布线态根因以 `probe_all_v2.py`（与 runner
make_record 同构，产物 probe_underlying_v2.json）为准。
