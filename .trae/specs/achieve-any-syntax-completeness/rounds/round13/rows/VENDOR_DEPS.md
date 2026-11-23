# site-packages 第三方依赖 vendor 溯源（Task 122.12 / 122.13）

目的：J 空间 374 条 site-packages 语义 ERROR 的根因是原始 pyc 的模块级硬 import
第三方包，仓库与本机均无。本文件记录向仓库 `site-packages/` 补齐的每个包的
来源、版本、SHA256 与验证证据。wheel 原件留档于
`D:\temp\opencode\cl_layout\g4d\vendor_deps\`（不入库；以 SHA256 保证可复现）。

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

## 第三层缺失（待 122.13 收口）

25 条样本残留 ERROR（＋2 条 t30-NO_C4 暂态 ERROR）全部同一异常
`ModuleNotFoundError: No module named 'zmq'`（27/27 布线 probe 实测，elapsed
2.0–3.7 s）：失败链汇聚 IQCommon/common/__init__ L8 → IQCommon/common/main.pyc
L57（模块级 `import zmq`；该模块 pyc-only 无源码，co_filename 内嵌
./fly_docker_py311/...）。源码侧 zmq import 全景：fly/common/commonOK.py:4、
fly/data/quoteOK.py:14、fly/dumpload/load_dailyOK.py:10、IQCommon/common/mainOK.py:10、
IQData/plugins/plugin_system_realquote/real_quoteOK.py:4（IQData 在 J 空间 0 条）。
宿主 D:\Python 同样无 zmq。→ Task 122.13：vendor pyzmq（＋typing_extensions），
再探 zmq 之后更深 import 层直至收口或非 import 卡点。

## probe 口径警示

`D:\temp\...\probe_semantic_error.py` 组 case **不注入 package_root**——其输出
是"无布线第一层失败"，不能用于 vendor 后的根因定位（已实证：tornado 已入库仍报
"No module named 'tornado'"）。布线态根因以 `probe_all_v2.py`（与 runner
make_record 同构，产物 probe_underlying_v2.json）为准。
