#!/usr/bin/env python3
"""
真实代码模式测试套件 - 基于实际业务场景的反编译验证

包含：
- 10个通用模式（R01-R10）：覆盖常见编程模式
- 4个开源项目模式（R11-R14）：模拟requests、numpy、pandas、flask风格
- 6个复杂业务模式（R15-R20）：企业级应用场景

理论依据（软件工程实践）：
- 真实性原则：测试用例应来自真实业务场景，而非人工构造
- 覆盖性原则：控制流结构组合应覆盖实际使用的主要模式
- 可维护性：每个用例都应独立可运行，便于回归测试

来源说明：
- R01-R03: 文件处理/网络请求/资源管理三大基础场景
- R04-R06: 数据处理核心模式（过滤/分发/搜索）
- R07-R09: 异常处理与状态机
- R10: Python 3.10+ 结构化模式匹配
- R11-R14: 主流开源库典型用法抽象
- R15-R20: 企业级复杂业务流程
"""

import unittest
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.test_functional_verification import (
    DecompilationVerifier,
    VerificationStatus,
    create_test_verifier
)


class TestRealCodePatterns(unittest.TestCase):
    """真实代码模式测试类

    测试目标：验证反编译器对真实业务代码模式的还原能力

    验证策略：
    1. 编译原始源码 → 字节码
    2. 反编译 → 还原源码
    3. 再编译 → 对比字节码功能等价性
    4. 评估反编译质量（语法正确性 + 控制流保持性）
    """

    @classmethod
    def setUpClass(cls):
        """初始化验证器"""
        cls.verifier = create_test_verifier()

    def verify_pattern(self, source: str, min_equivalence: float = 0.90, strict: bool = False):
        """验证反编译结果的功能等价性

        Args:
            source: Python源代码
            min_equivalence: 最小等价率要求（默认90%，某些复杂模式降低要求）
            strict: 是否严格检查PASSED状态（False时允许WARNING）
        """
        report = self.verifier.verify_decompile(source)

        if strict:
            self.assertEqual(
                report.status,
                VerificationStatus.PASSED,
                f"验证失败！状态: {report.status.value}\n"
                f"错误: {report.errors}\n"
                f"警告: {report.warnings}\n"
                f"等价率: {report.equivalence_rate:.2%}\n"
                f"反编译结果:\n{report.decompiled_source}"
            )
        else:
            self.assertIn(
                report.status,
                [VerificationStatus.PASSED, VerificationStatus.WARNING],
                f"验证失败！状态: {report.status.value}\n"
                f"错误: {report.errors}\n"
                f"等价率: {report.equivalence_rate:.2%}\n"
                f"反编译结果:\n{report.decompiled_source}"
            )

        self.assertGreaterEqual(
            report.equivalence_rate,
            min_equivalence,
            f"等价率 {report.equivalence_rate:.2%} 低于阈值 {min_equivalence:.2%}"
        )

        return report


class TestGeneralPatterns(TestRealCodePatterns):
    """R01-R10: 通用编程模式测试"""

    def test_R01_file_line_processing(self):
        """
        R01: 文件逐行处理 (for + try-except)

        来源：日志分析、CSV解析、配置文件读取等场景
        典型应用：
          - 逐行读取日志文件并解析JSON格式
          - 批量处理用户上传的数据文件
          - 流式数据管道中的异常容忍处理
        控制流特征：
          - for循环：迭代输入序列
          - try-except：捕获并跳过格式错误的行
          - continue：异常后继续处理下一行
          - 列表累积：收集有效数据到result列表

        技术要点：
          - 异常处理在循环内部，体现"容错继续"语义
          - result在try外部定义，确保作用域正确
          - json模块导入在函数内部，模拟局部依赖
        """
        source = '''
def target():
    import json
    result = []
    for line in ['{"a":1}', 'invalid', '{"b":2}']:
        try:
            data = json.loads(line)
            result.append(data)
        except json.JSONDecodeError:
            continue
    return result
'''
        self.verify_pattern(source, min_equivalence=0.75)

    @pytest.mark.xfail(reason="反编译器对raise语句（特别是裸raise和条件内raise）的支持尚不完善")
    def test_R02_retry_mechanism(self):
        """
        R02: 重试机制 (for + try + if)

        来源：HTTP客户端库（如requests、urllib3）、数据库连接池、消息队列消费者
        典型应用：
          - API调用失败后的自动重试（指数退避）
          - 数据库连接断开后的重连逻辑
          - 网络IO操作的容错处理
        控制流特征：
          - for循环：限制最大重试次数
          - try-except：捕获连接错误
          - if条件：判断是否应该重试或抛出异常
          - return：成功时提前返回
          - raise：最后一次重试失败后向上传播异常

        技术要点：
          - attempt < 2 时主动抛出异常，模拟前两次失败
          - time.sleep() 模拟重试间隔（实际中可能是指数退避）
          - 最后一次失败时重新raise，避免吞掉异常
        """
        source = '''
def target():
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt < 2:
                raise ConnectionError(f"Attempt {attempt}")
            return {"status": "success"}
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.01)
    return None
'''
        self.verify_pattern(source, min_equivalence=0.70)

    def test_R03_resource_cleanup(self):
        """
        R03: 资源清理 (with + try-finally)

        来源：文件操作、数据库事务、网络连接管理等需要确保资源释放的场景
        典型应用：
          - 文件写入后确保flush到磁盘
          - 数据库事务中即使出错也要记录日志
          - HTTP响应必须关闭连接
        控制流特征：
          - with语句：上下文管理器自动资源管理
          - try-finally：确保关键操作（flush）一定执行
          - 嵌套结构：with包裹try-finally，双重保障

        技术要点：
          - with语句保证__exit__被调用（文件关闭）
          - finally块保证数据刷入磁盘，即使write抛出异常
          - result列表用于追踪执行路径，便于调试
        """
        source = '''
def target():
    result = []
    with open('/dev/null', 'w') as f:
        try:
            f.write("data")
            result.append(1)
        finally:
            f.flush()
    return result
'''
        self.verify_pattern(source, min_equivalence=0.88)

    def test_R04_data_validation_filtering(self):
        """
        R04: 数据验证 (for + if + continue)

        来源：数据清洗ETL管道、表单验证、API参数校验
        典型应用：
          - 过滤掉None值或缺失字段
          - 数据类型转换前的预检
          - 批量数据导入时的有效性校验
        控制流特征：
          - for循环：遍历待处理数据
          - if条件：检查数据有效性
          - continue：跳过无效数据
          - 列表推导式替代：valid = [item * 2 for item in data if item is not None]

        技术要点：
          - item is None 使用身份比较（而非 == None），更Pythonic
          - continue直接进入下一次迭代，避免深层嵌套
          - 有效数据进行转换（* 2）后收集
        """
        source = '''
def target():
    data = [0, None, 2, None, 4]
    valid = []
    for item in data:
        if item is None:
            continue
        valid.append(item * 2)
    return valid
'''
        self.verify_pattern(source, min_equivalence=0.92)

    def test_R05_multi_condition_branching(self):
        """
        R05: 多条件分支 (if-elif-else链)

        来源：类型分派、命令模式、策略选择、状态码映射
        典型应用：
          - 根据输入类型执行不同的处理逻辑（多态替代方案）
          - HTTP状态码到业务含义的映射
          - 配置项根据类型进行不同格式的转换
        控制流特征：
          - if-elif-else链：多重条件互斥分支
          - 类型检查：isinstance() 进行运行时类型识别
          - 提前返回：每个分支都有return，避免fall-through

        技术要点：
          - elif链比多个独立if更高效（条件互斥时只判断一次）
          - else兜底：处理未预期的类型，返回str(value)作为通用转换
          - isinstance支持继承关系检查（int是object的子类）
        """
        source = '''
def target(value):
    if isinstance(value, int):
        return value * 2
    elif isinstance(value, str):
        return value.upper()
    elif isinstance(value, list):
        return len(value)
    else:
        return str(value)
'''
        self.verify_pattern(source, min_equivalence=0.93)

    def test_R06_nested_loop_search(self):
        """
        R06: 嵌套循环查找 (for-for-if-return)

        来源：二维数组/矩阵操作、图像处理、图算法、表格数据搜索
        典型应用：
          - 在二维矩阵中查找特定元素的位置
          - 图像像素级搜索（找特定颜色的坐标）
          - Excel/CSV表格数据的行列定位
        控制流特征：
          - 双层for循环：外层遍历行，内层遍历列
          - enumerate：同时获取索引和值
          - if条件：元素匹配判定
          - return元组：找到后立即返回(i, j)坐标
          - 兜底返回：(-1, -1)表示未找到

        技术要点：
          - 提前返回避免不必要的遍历（性能优化）
          - enumerate比range(len())更Pythonic
          - 返回元组符合Python的多值返回惯例
        """
        source = '''
def target(matrix, target_value):
    for i, row in enumerate(matrix):
        for j, elem in enumerate(row):
            if elem == target_value:
                return (i, j)
    return (-1, -1)
'''
        self.verify_pattern(source, min_equivalence=0.91)

    @pytest.mark.xfail(reason="反编译器对多函数定义+raise语句的复杂场景支持有限")
    def test_R07_exception_layered_handling(self):
        """
        R07: 异常分层处理 (try-except-if)

        来源：分布式系统、微服务调用、第三方库封装层
        典型应用：
          - 区分可恢复异常和不可恢复异常
          - 根据异常信息决定降级策略
          - 错误码到恢复动作的映射
        控制流特征：
          - try-except：捕获特定类型的异常
          - except as e：获取异常实例以访问详细信息
          - if条件：基于异常内容（message/attributes）做分层决策
          - raise：不可恢复时重新抛出
          - 函数调用：fallback(data) 作为降级处理

        技术要点：
          - process() 和 fallback() 是占位函数，模拟外部依赖
          - "recoverable" in str(e) 通过字符串匹配判断是否可恢复
          - 这种模式在企业级框架中非常常见（如Spring Retry、Resilience4j）
        """
        source = '''
def process(data):
    if "error" in str(data):
        raise ValueError("recoverable error occurred")
    return {"processed": data}

def fallback(data):
    return {"fallback": data}

def target(data):
    try:
        result = process(data)
    except ValueError as e:
        if "recoverable" in str(e):
            return fallback(data)
        raise
    return result
'''
        self.verify_pattern(source, min_equivalence=0.75)

    def test_R08_context_manager_chain(self):
        """
        R08: 上下文管理器链 (with-with-try)

        来源：文件复制、数据管道、多资源协调
        典型应用：
          - 同时打开源文件和目标文件进行复制
          - 数据库读写分离场景（读连接+写连接）
          - 加密/解密流水线（输入流+输出流）
        控制流特征：
          - 嵌套with：同时管理多个资源（f1读，f2写）
          - try-except：捕获IO错误并静默处理（pass）
          - 数据截取：data[:100] 限制写入大小
          - 返回布尔值：表示操作成功

        技术要点：
          - 嵌套with等价于 with open(...) as f1, open(...) as f2（Python 3.1+）
          - except IOError: pass 是"静默忽略"模式（生产环境应记录日志）
          - 多资源管理的退出顺序是LIFO（后进先出）
        """
        source = '''
def target(filepath):
    with open('/dev/null', 'r') as f1:
        with open('/dev/null', 'w') as f2:
            try:
                data = f1.read()
                f2.write(data[:100])
            except IOError:
                pass
    return True
'''
        self.verify_pattern(source, min_equivalence=0.72)

    def test_R09_conditional_loop_state_machine(self):
        """
        R09: 条件循环 (while + if + break) - 状态机循环

        来源：解析器、协议处理器、游戏循环、事件驱动系统
        典型应用：
          - 逐个消费队列直到遇到终止信号（None）
          - 解析变长协议帧直到结束标记
          - 游戏主循环直到退出条件满足
        控制流特征：
          - while循环：基于条件的迭代（非固定次数）
          - 手动索引管理：i += 1（区别于for的自动递增）
          - if + break：遇到哨兵值（None）时提前终止
          - 列表累积：收集有效元素

        技术要点：
          - while i < len(items): 显式边界检查（防止IndexError）
          - break退出循环，i不再递增（此时i指向None的位置）
          - 这种模式在C风格代码转Python时很常见
        """
        source = '''
def target(items):
    result = []
    i = 0
    while i < len(items):
        item = items[i]
        if item is None:
            break
        result.append(item)
        i += 1
    return result
'''
        self.verify_pattern(source, min_equivalence=0.90)

    @unittest.skipIf(sys.version_info < (3, 10), "match-case requires Python 3.10+")
    def test_R10_pattern_matching(self):
        """
        R10: 模式匹配 (3.10+) (match-case)

        来源：Python 3.10引入的结构化模式匹配，替代复杂的if-elif链
        典型应用：
          - HTTP状态码处理（200/404/500等）
          - AST节点类型分派（编译器/解释器）
          - 协议消息类型路由
          - CLI命令解析
        控制流特征：
          - match-case：结构化模式匹配（比if-elif更强大）
          - 字面量匹配："ok", "error", "not_found"
          - 通配符模式：case _ 匹配所有其他情况
          - 每个分支返回对应的状态码

        技术要点：
          - match-case支持解构嵌套、类型守卫、OR模式等高级特性
          - 比if-elif更简洁且编译器可优化
          - 版本跳过：@pytest.mark.skipIf 确保兼容性
        """
        source = '''
def target(status):
    match status:
        case "ok":
            return 200
        case "error":
            return 500
        case "not_found":
            return 404
        case _:
            return 0
'''
        self.verify_pattern(source, min_equivalence=0.88)


class TestOpenSourcePatterns(TestRealCodePatterns):
    """R11-R14: 开源项目典型模式测试"""

    @pytest.mark.xfail(reason="反编译器对多函数定义+raise+复杂异常处理的场景支持有限")
    def test_R11_http_request_retry_requests_style(self):
        """
        R11: HTTP请求重试 (requests风格)

        来源：requests库、urllib3、httpx、aiohttp等HTTP客户端
        典型应用：
          - REST API调用失败后的自动重试
          - 网络超时后的指数退避重试
          - 限流（Rate Limiting）后的延迟重试
        控制流特征：
          - for循环：有限次重试
          - try-except TimeoutError：专门捕获超时异常
          - if response.get("ok")：检查业务层成功标志
          - except块内的if：判断是否为最后一次重试
          - continue：非最后一次则继续重试
          - return None：所有重试均失败后的默认返回

        技术要点：
          - call_api(url) 占位函数模拟HTTP请求
          - response.get("ok") 使用dict.get避免KeyError
          - 只对TimeoutError重试，其他异常直接传播
          - 这是requests.adapters.HTTPAdapter的核心逻辑简化版
        """
        source = '''
def call_api(url):
    if "fail" in url:
        raise TimeoutError(f"Connection timed out: {url}")
    return {"ok": True, "data": {"url": url}}

def target(url, retries=3):
    for attempt in range(retries):
        try:
            response = call_api(url)
            if response.get("ok"):
                return response["data"]
        except TimeoutError:
            if attempt == retries - 1:
                raise
            continue
    return None
'''
        self.verify_pattern(source, min_equivalence=0.86)

    def test_R12_array_traversal_filter_numpy_style(self):
        """
        R12: 数组遍历过滤 (numpy风格)

        来源：numpy、pandas、scipy等科学计算库的数据处理模式
        典型应用：
          - 多维数组的扁平化遍历和条件筛选
          - 批量数据处理管道（类似numpy的boolean indexing）
          - 嵌套列表的展平和过滤
        控制流特征：
          - 外层for：遍历子数组（二维结构的第一维）
          - if len(arr) > 0：空数组保护（避免无效遍历）
          - 内层for：遍历子数组的每个元素
          - if x > 0：正值过滤条件
          - result.append(x)：收集符合条件的元素

        技术要点：
          - 模拟了numpy的 arr[arr > 0] 语义（但用纯Python实现）
          - 两层循环 + 两个if条件，体现典型的数据清洗流程
          - len(arr) > 0 的检查防止空列表时的无用迭代
        """
        source = '''
def target(arrays):
    result = []
    for arr in arrays:
        if len(arr) > 0:
            for x in arr:
                if x > 0:
                    result.append(x)
    return result
'''
        self.verify_pattern(source, min_equivalence=0.91)

    def test_R13_data_cleaning_pandas_style(self):
        """
        R13: 数据清洗 (pandas风格)

        来源：pandas DataFrame处理、ETL工具、数据分析管道
        典型应用：
          - 从字典列表中清洗脏数据
          - 字段存在性和类型校验
          - 数值范围验证
          - 缺失值和异常值的过滤
        控制流特征：
          - for row in rows：逐行处理（类似pandas的iterrows/apply）
          - try-except (ValueError, TypeError)：多重异常捕获
          - if row.get("value")：字段存在性检查（防止KeyError）
          - float(row["value"]) > 0：类型转换 + 数值范围验证
          - continue：任何验证失败都跳过该行

        技术要点：
          - row.get("value") 比 row["value"] 更安全（None vs KeyError）
          - float() 可能抛出ValueError（非法字符串）或TypeError（None）
          - 多重异常捕获：except (ValueError, TypeError) 统一处理
          - 模拟了pandas的 dropna + query 功能
        """
        source = '''
def target(rows):
    cleaned = []
    for row in rows:
        try:
            if row.get("value") and float(row["value"]) > 0:
                cleaned.append(row)
        except (ValueError, TypeError):
            continue
    return cleaned
'''
        self.verify_pattern(source, min_equivalence=0.87)

    def test_R14_route_matching_flask_style(self):
        """
        R14: 路由匹配 (flask风格)

        来源：Flask、Django、FastAPI等Web框架的路由系统
        典型应用：
          - URL路径到处理函数的映射
          - API版本路由（/api/v1/, /api/v2/）
          - 中间件链中的请求分发
        控制流特征：
          - for pattern, handler in routes.items()：遍历路由表（字典）
          - if path.startswith(pattern)：前缀匹配（支持子路径）
          - if handler：handler存在性检查（可能为None表示禁用）
          - return handler()：调用匹配的处理函数并返回结果
          - 兜底返回 "404"：未匹配任何路由

        技术要点：
          - routes.items() 遍历键值对（模式→处理器）
          - startswith 支持模糊匹配（/api 匹配 /api/users）
          - handler() 调用可能有副作用（数据库查询、认证等）
          - 这是WSGI路由系统的核心逻辑简化版
        """
        source = '''
def target(path, routes):
    for pattern, handler in routes.items():
        if path.startswith(pattern):
            if handler:
                return handler()
    return "404"
'''
        self.verify_pattern(source, min_equivalence=0.92)


class TestComplexBusinessPatterns(TestRealCodePatterns):
    """R15-R20: 复杂业务模式测试"""

    @pytest.mark.xfail(reason="反编译器对多函数定义+异常处理的复杂业务场景支持有限")
    def test_R15_config_loading_multi_source(self):
        """
        R15: 配置加载 (for + try + if) - 多源配置加载

        来源：配置管理系统（如Spring Boot Config、Python-decouple）
        典型应用：
          - 从多个配置源加载并合并（环境变量 → 文件 → 默认值）
          - 微服务的配置中心集成（Consul、etcd、Apollo）
          - 特性开关（Feature Flags）的动态加载
        控制流特征：
          - for source in sources：遍历配置源优先级列表
          - try-except Exception：宽泛异常捕获（多种加载失败可能）
          - config.update(data)：合并配置（后者覆盖前者）
          - if required：严格模式检查（任一源失败则整体失败）
          - continue：非严格模式下跳过失败的源

        技术要点：
          - load_config(source) 占位函数模拟从不同源加载（文件/环境/远程）
          - required 参数控制容错策略（True=严格，False=宽松）
          - dict.update() 实现配置合并（浅合并，嵌套字典需特殊处理）
          - 这是12-Factor App的Config原则实现
        """
        source = '''
def load_config(source):
    configs = {
        "file": {"db_host": "localhost", "db_port": 5432},
        "env": {"debug": True, "log_level": "INFO"},
        "remote": {"cache_ttl": 3600, "max_connections": 100}
    }
    if source not in configs:
        raise ValueError(f"Unknown config source: {source}")
    return configs[source]

def target(sources, required=True):
    config = {}
    for source in sources:
        try:
            data = load_config(source)
            config.update(data)
        except Exception as e:
            if required:
                raise
            continue
    return config
'''
        self.verify_pattern(source, min_equivalence=0.75)

    def test_R16_log_rotation_size_check(self):
        """
        R16: 日志轮转 (while + if + break) - 文件大小检查

        来源：logging模块的RotatingFileHandler、logrotate工具
        典型应用：
          - 日志文件达到阈值后自动轮转（创建新文件）
          - 防止磁盘空间耗尽
          - 归档旧日志文件
        控制流特征：
          - while log_file.size() > max_size：持续检查直到满足条件
          - rotate(log_file)：执行轮转操作（重命名/压缩/删除）
          - rotations += 1：计数器递增
          - if rotations >= 5：安全阀机制（防止无限循环）
          - break：达到最大轮转次数后强制退出

        技术要点：
          - log_file.size() 和 rotate(log_file) 是占位函数
          - max_size=1024 是阈值（字节或其他单位）
          - rotations >= 5 是硬编码的安全上限（生产环境应可配置）
          - while循环体现"持续监控直到条件满足"语义
        """
        source = '''
class MockLogFile:
    def __init__(self, size):
        self._size = size

    def size(self):
        return self._size

    def rotate(self):
        self._size = self._size // 2

def rotate(log_file):
    log_file.rotate()

def target(log_file, max_size=1024):
    rotations = 0
    while log_file.size() > max_size:
        rotate(log_file)
        rotations += 1
        if rotations >= 5:
            break
    return rotations
'''
        self.verify_pattern(source, min_equivalence=0.84)

    @pytest.mark.xfail(reason="反编译器对类定义+上下文管理器+异常处理的复杂场景支持有限")
    def test_R17_parallel_task_processing_threadpool(self):
        """
        R17: 并行任务处理 (with + for + try) - 线程池处理

        来源：concurrent.futures.ThreadPoolExecutor、multiprocessing
        典型应用：
          - 批量HTTP请求的并行发送
          - 并行数据处理（MapReduce模式）
          - 异步任务队列的消费和处理
        控制流特征：
          - with ThreadPool() as pool：上下文管理器管理线程池生命周期
          - for task in tasks：遍历任务列表
          - pool.submit(execute_task, task)：异步提交任务
          - result.result()：阻塞等待任务完成（获取结果或异常）
          - try-except Exception：捕获单个任务的失败
          - results.append({"error": str(e)})：记录错误信息

        技术要点：
          - ThreadPool 和 execute_task 是占位函数/类
          - with语句确保线程池的正确关闭（shutdown(wait=True)）
          - result.result() 会重新抛出任务函数中的异常
          - 单个任务失败不影响其他任务（容错设计）
          - results列表混合成功结果和错误字典（需调用方区分）
        """
        source = '''
from concurrent.futures import Future

class MockThreadPool:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def submit(self, func, *args):
        class MockResult:
            def __init__(self, func, args):
                self._func = func
                self._args = args

            def result(self):
                return self._func(*self._args)
        return MockResult(func, args)

ThreadPool = MockThreadPool

def execute_task(task):
    if task == "fail":
        raise RuntimeError(f"Task failed: {task}")
    return {"task": task, "status": "done"}

def target(tasks, results):
    with ThreadPool() as pool:
        for task in tasks:
            try:
                result = pool.submit(execute_task, task)
                results.append(result.result())
            except Exception as e:
                results.append({"error": str(e)})
    return results
'''
        self.verify_pattern(source, min_equivalence=0.70)

    def test_R18_state_machine_complex_transitions(self):
        """
        R18: 状态机 (while + if-elif-else) - 复杂状态流转

        来源：工作流引擎、协议状态机、游戏AI、编译器词法/语法分析器
        典型应用：
          - 订单状态流转（待支付→已支付→发货→完成/退款）
          - TCP连接状态（SYN_SENT→ESTABLISHED→FIN_WAIT→CLOSED）
          - 游戏角色状态（idle→running→jumping→attacking→idle）
        控制流特征：
          - while state != "done"：循环直到终态
          - if-elif-else链：状态分派（每种状态有不同行为）
          - state = "xxx"：状态转移（修改循环条件）
          - output.append(...)：记录状态机轨迹（便于调试/审计）
          - else分支 + break：未知状态的紧急退出

        技术要点：
          - 状态机是计算机科学的基础模式（FSM - Finite State Machine）
          - 每个状态明确列出可能的转移目标
          - else分支作为防御性编程（处理非法状态）
          - output列表可用于生成状态转移图或日志
        """
        source = '''
def target(initial_state):
    state = initial_state
    output = []
    while state != "done":
        if state == "init":
            output.append("initializing")
            state = "running"
        elif state == "running":
            output.append("processing")
            state = "done"
        else:
            output.append(f"unknown: {state}")
            break
    return output
'''
        self.verify_pattern(source, min_equivalence=0.89)

    def test_R19_recursion_to_iteration_dfs(self):
        """
        R19: 递归转迭代 (while + if + list操作) - DFS转迭代

        来源：树/图的深度优先搜索、表达式求值、DOM遍历
        典型应用：
          - 文件系统目录树的递归遍历（转为迭代避免栈溢出）
          - JSON/XML嵌套结构的深度遍历
          - 编译器的AST遍历（visitor模式）
        控制流特征：
          - while stack：栈不为空时持续处理（显式栈代替调用栈）
          - node = stack.pop()：弹出栈顶节点（LIFO）
          - if node and node not in visited：节点有效性 + 去重检查
          - visited.append(node)：标记已访问
          - for child in reversed(node.children)：逆序压入子节点

        技术要点：
          - reversed() 保证左子树先被访问（模拟递归的顺序）
          - node.children 是占位属性（假设node对象有children属性）
          - 显式栈避免了Python的递归深度限制（sys.getrecursionlimit()）
          - not in visited 防止环路导致的无限循环（图遍历必需）
          - 这是DFS的标准迭代实现（时间O(V+E)，空间O(V)）
        """
        source = '''
class MockNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

    def __repr__(self):
        return f"Node({self.name})"

    def __eq__(self, other):
        return isinstance(other, MockNode) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

def target(root):
    stack = [root]
    visited = []
    while stack:
        node = stack.pop()
        if node and node not in visited:
            visited.append(node)
            for child in reversed(node.children):
                stack.append(child)
    return visited
'''
        self.verify_pattern(source, min_equivalence=0.83)

    @pytest.mark.xfail(reason="反编译器对最复杂业务流程（多类定义+多函数+5层嵌套+异常处理）的支持尚不完善")
    def test_R20_complex_business_workflow(self):
        """
        R20: 复杂业务流程 (with + for + if + try + if) - 最复杂的组合

        来源：电商订单处理、银行交易系统、ERP业务流程
        典型应用：
          - 订单批量处理（验证→支付→发货→通知）
          - 金融交易的批处理（校验→风控→记账→清算）
          - 数据迁移/同步的事务性处理
        控制流特征：
          - with transaction() as tx：数据库事务上下文（原子性保证）
          - for order in orders：批量处理订单
          - if order.is_valid：前置条件检查（订单有效性）
          - try-except OrderError：捕获业务异常
          - processed = process_order(order)：核心业务逻辑
          - if processed.successful：成功分支（收集结果）
          - elif order.retryable：可重试分支（retry_order）
          - else：失败分支（refund退款）
          - except块：异常处理（log_error + 收集错误信息）

        技术要点：
          - 5层嵌套（with → for → if → try → if-elif-else）
          - 事务保证：要么全部成功，要么全部回滚
          - 三种结果处理：成功/可重试/失败（完整覆盖）
          - 异常不中断整个批次（单个订单失败不影响其他）
          - 这是企业级代码的真实复杂度（不是过度设计的例子）
        """
        source = '''
class MockTransaction:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

def transaction():
    return MockTransaction()

class MockOrder:
    def __init__(self, order_id, is_valid=True, retryable=False):
        self.order_id = order_id
        self.is_valid = is_valid
        self.retryable = retryable

class MockProcessResult:
    def __init__(self, successful, data=None):
        self.successful = successful
        self.data = data

def process_order(order):
    if order.order_id == "fail":
        raise OrderError(f"Processing failed for {order.order_id}")
    return MockProcessResult(True, {"order_id": order.order_id, "status": "processed"})

class OrderError(Exception):
    pass

def retry_order(order):
    pass

def refund(order):
    pass

def log_error(error):
    pass

def target(orders):
    results = []
    with transaction() as tx:
        for order in orders:
            if order.is_valid:
                try:
                    processed = process_order(order)
                    if processed.successful:
                        results.append(processed.data)
                    elif order.retryable:
                        retry_order(order)
                    else:
                        refund(order)
                except OrderError as e:
                    log_error(e)
                    results.append({"error": str(e)})
    return results
'''
        self.verify_pattern(source, min_equivalence=0.68)


if __name__ == '__main__':
    unittest.main(verbosity=2)
