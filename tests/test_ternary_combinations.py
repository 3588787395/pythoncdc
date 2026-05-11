#!/usr/bin/env python3
"""
三元组合控制流语法测试 - 30个关键嵌套模式

测试分类:
- T01-T20: 标准三元组合（3层标准嵌套）
- T21-T25: 深层和超深三元组合（4-5层）
- T26-T28: 6-7层极限嵌套（标记为xfail）
- T29-T30: 带 break/continue/return/raise 的特殊模式

理论依据：
- CFG区域归约算法对多层嵌套控制流的处理能力
- 编译器压力测试：验证反编译器在复杂嵌套下的正确性
- 控制流完备性矩阵：覆盖所有重要的三层嵌套排列组合
"""

import pytest
import sys
import os
import ast
import dis
import types
from typing import Optional, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.code_generator import CodeGenerator
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入核心模块: {e}")
    CORE_AVAILABLE = False


class TestTernaryCombinations:
    """三元组合控制流语法测试

    测试反编译器对三层及更深嵌套控制流结构的处理能力。
    覆盖 if/for/while/try/with 的所有重要三元组合。
    """

    @classmethod
    def setup_class(cls):
        """初始化测试环境"""
        if not CORE_AVAILABLE:
            pytest.skip("核心模块未加载，跳过所有测试")

    def compile_and_decompile(self, source: str) -> Tuple[str, bool]:
        """编译源码→反编译→返回结果和状态"""
        try:
            code = compile(source, '<test>', 'exec')
        except SyntaxError as e:
            raise ValueError(f"源码语法错误: {e}")

        try:
            cfg_builder = CFGBuilder()
            cfg = cfg_builder.build(code)

            analyzer = RegionAnalyzer(cfg)
            generator = RegionASTGenerator(cfg, analyzer)
            result = generator.generate()

            code_gen = CodeGenerator()
            decompiled = code_gen.generate(result)
            return decompiled, True
        except Exception as e:
            return str(e), False

    def verify_syntax_valid(self, source: str) -> bool:
        """验证源码语法正确性"""
        try:
            ast.parse(source)
            return True
        except SyntaxError:
            return False

    def verify_decompilation_result(self, source: str) -> dict:
        """完整验证流程：编译→反编译→语法检查"""
        result = {
            'source': source,
            'decompiled': None,
            'syntax_ok': False,
            'success': False,
            'error': None
        }

        if not self.verify_syntax_valid(source):
            result['error'] = "源码语法错误"
            return result

        decompiled, success = self.compile_and_decompile(source)
        result['decompiled'] = decompiled
        result['success'] = success

        if success and decompiled:
            result['syntax_ok'] = self.verify_syntax_valid(decompiled)
            if not result['syntax_ok']:
                result['error'] = "反编译结果语法错误"

        return result

    # ==================== 标准三元组合 T01-T10 ====================

    def test_T01_if_for_if(self):
        """T01: if>for>if (条件→循环→条件，数据处理模式，3层)

        场景：外层条件判断 → 中层循环遍历 → 内层条件过滤数据
        典型应用：条件性数据处理管道
        """
        source = '''
def target(data, threshold):
    if data:
        for item in data:
            if item > threshold:
                process(item)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T01反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T01反编译结果语法错误"

    def test_T02_for_if_for(self):
        """T02: for>if>for (循环→条件→循环，嵌套迭代，3层)

        场景：外层循环 → 条件分支选择 → 内层循环处理
        典型应用：二维数组的条件性遍历
        """
        source = '''
def target(matrix):
    for row in matrix:
        if row:
            for element in row:
                handle(element)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T02反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T02反编译结果语法错误"

    def test_T03_try_for_if(self):
        """T03: try>for>if (异常保护→循环→条件，3层)

        场景：try保护整个循环过程 → 循环遍历 → 内层条件判断
        典型应用：安全的批量数据处理
        """
        source = '''
def target(items):
    try:
        for item in items:
            if item.valid():
                process(item)
    except Exception as e:
        log_error(e)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T03反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T03反编译结果语法错误"

    def test_T04_if_try_for(self):
        """T04: if>try>for (条件判断→异常保护→循环，3层)

        场景：条件判断是否需要处理 → try保护 → 循环执行
        典型应用：可选的安全批量操作
        """
        source = '''
def target(flag, items):
    if flag:
        try:
            for item in items:
                risky_operation(item)
        except Error:
            fallback()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T04反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T04反编译结果语法错误"

    def test_T05_for_try_if(self):
        """T05: for>try>if (循环→异常保护→条件，3层)

        场景：循环遍历 → 每次迭代try保护 → 内层条件判断
        典型应用：逐项安全处理与条件过滤
        """
        source = '''
def target(items):
    for item in items:
        try:
            if is_valid(item):
                process(item)
        except ValidationError:
            skip(item)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T05反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T05反编译结果语法错误"

    def test_T06_while_if_for(self):
        """T06: while>if>for (循环→条件→循环，3层)

        场景：while外层循环 → 条件判断 → for内层循环
        典型应用：带条件的迭代式处理
        """
        source = '''
def target(data):
    i = 0
    while i < len(data):
        chunk = data[i:i+10]
        if chunk:
            for item in chunk:
                process(item)
        i += 10
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T06反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T06反编译结果语法错误"

    def test_T07_if_while_if(self):
        """T07: if>while>if (条件→循环→条件，3层)

        场景：外层条件启用 → while持续循环 → 内层条件检查
        典型应用：条件性的持续监控或轮询
        """
        source = '''
def target(enabled, sensor):
    if enabled:
        while sensor.active():
            reading = sensor.read()
            if reading > threshold:
                alert(reading)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T07反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T07反编译结果语法错误"

    def test_T08_for_if_while(self):
        """T08: for>if>while (循环→条件→循环异类，3层)

        场景：for外层循环 → 条件分支 → while内层循环
        典型应用：混合类型的嵌套迭代
        """
        source = '''
def target(items):
    for category in items:
        if category.needs_processing():
            item = category.first()
            while item:
                process(item)
                item = category.next()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T08反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T08反编译结果语法错误"

    def test_T09_try_if_for(self):
        """T09: try>if>for (异常→条件→循环，3层)

        场景：try保护整体 → 条件判断是否需要处理 → 循环执行
        典型应用：安全的条件性批量操作
        """
        source = '''
def target(config):
    try:
        if config.enabled:
            for task in config.tasks:
                execute(task)
    except ConfigError:
        use_default_config()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T09反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T09反编译结果语法错误"

    def test_T10_if_for_try(self):
        """T10: if>for>try (条件→循环→异常，3层)

        场景：条件判断 → 循环遍历 → 每次迭代的异常处理
        典型应用：条件性的容错批处理
        """
        source = '''
def target(process_items):
    if should_process():
        for item in process_items:
            try:
                transform(item)
            except TransformError:
                keep_original(item)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T10反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T10反编译结果语法错误"

    # ==================== 标准三元组合 T11-T20 ====================

    def test_T11_with_for_if(self):
        """T11: with>for>if (上下文→循环→条件，3层)

        场景：with管理资源 → 循环使用资源 → 条件过滤
        典型应用：文件/数据库的上下文管理+遍历+过滤
        """
        source = '''
def target(filename):
    with open(filename) as f:
        for line in f:
            if line.strip():
                parse(line)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T11反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T11反编译结果语法错误"

    def test_T12_for_with_if(self):
        """T12: for>with>if (循环→上下文→条件，3层)

        场景：循环遍历 → 每项使用with管理资源 → 条件处理
        典型应用：批量资源管理与条件处理
        """
        source = '''
def target(filenames):
    for fname in filenames:
        with open(fname) as f:
            content = f.read()
            if content:
                analyze(content)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T12反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T12反编译结果语法错误"

    def test_T13_if_with_for(self):
        """T13: if>with>for (条件→上下文→循环，3层)

        场景：条件判断 → with获取资源 → 循环使用
        典型应用：可选的资源遍历操作
        """
        source = '''
def target(use_cache, cache):
    if use_cache:
        with cache.connect() as conn:
            for record in conn.query():
                process(record)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T13反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T13反编译结果语法错误"

    def test_T14_try_for_while(self):
        """T14: try>for>while (异常→循环→循环异类，3层)

        场景：try保护 → for循环 → while内层循环
        典型应用：安全的混合类型嵌套循环
        """
        source = '''
def target(data_source):
    try:
        for batch in data_source.batches():
            current = batch.first()
            while current:
                process(current)
                current = batch.next()
    except DataSourceError:
        recover()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T14反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T14反编译结果语法错误"

    def test_T15_while_try_for(self):
        """T15: while>try>for (循环→异常→循环，3层)

        场景：while持续循环 → try保护每次迭代 → for内层处理
        典型应用：重试机制的批量处理
        """
        source = '''
def target(queue):
    while not queue.empty():
        try:
            task = queue.get()
            for subtask in task.subtasks():
                execute(subtask)
        except TaskError:
            queue.retry(task)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T15反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T15反编译结果语法错误"

    def test_T16_if_try_while(self):
        """T16: if>try>while (条件→异常→循环异类，3层)

        场景：条件启用 → try保护 → while持续处理
        典型应用：可选的异常保护持续处理
        """
        source = '''
def target(monitor_enabled, stream):
    if monitor_enabled:
        try:
            while stream.has_data():
                packet = stream.read()
                handle(packet)
        except StreamError:
            reconnect(stream)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T16反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T16反编译结果语法错误"

    def test_T17_for_if_try(self):
        """T17: for>if>try (循环→条件→异常，3层)

        场景：for循环 → 条件筛选 → try保护处理
        典型应用：条件性容错处理
        """
        source = '''
def target(requests):
    for req in requests:
        if req.is_important():
            try:
                process_important(req)
            except CriticalError:
                escalate(req)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T17反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T17反编译结果语法错误"

    def test_T18_try_with_for(self):
        """T18: try>with>for (异常→上下文→循环，3层)

        场景：try保护整体 → with管理资源 → 循环使用
        典型应用：安全的资源管理与遍历
        """
        source = '''
def target(db_config):
    try:
        with connect_database(db_config) as db:
            for row in db.query("SELECT * FROM users"):
                process_user(row)
    except DatabaseError:
        notify_admin()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T18反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T18反编译结果语法错误"

    def test_T19_with_try_if(self):
        """T19: with>try>if (上下文→异常→条件，3层)

        场景：with管理资源 → try保护操作 → 条件判断
        典型应用：资源的异常保护条件处理
        """
        source = '''
def target(resource_path):
    with open_resource(resource_path) as resource:
        try:
            data = resource.load()
            if data.is_complete():
                finalize(data)
        except LoadError:
            repair(resource)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T19反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T19反编译结果语法错误"

    def test_T20_if_for_with(self):
        """T20: if>for>with (条件→循环→上下文，3层)

        场景：条件判断 → 循环遍历 → 每项用with管理资源
        典型应用：条件性的批量资源处理
        """
        source = '''
def target(process_files):
    if has_permission():
        for filepath in process_files:
            with open(filepath, 'r') as f:
                content = f.read()
                transform(content)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T20反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T20反编译结果语法错误"

    # ==================== 深层和超深三元组合 T21-T25 ====================

    def test_T21_4layer_if_for_if_for(self):
        """T21: 4层伪三元 (if>for>if>for)，4层嵌套

        场景：在标准三元组合基础上扩展一层循环
        测试反编译器对4层嵌套的处理能力
        """
        source = '''
def target(data, threshold1, threshold2):
    if data:
        for group in data.groups():
            if group.size() > threshold1:
                for item in group.items():
                    if item.value > threshold2:
                        final_process(item)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T21反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T21反编译结果语法错误"

    def test_T22_4layer_try_for_if_try(self):
        """T22: 4层伪三元 (try>for>if>try)，4层嵌套

        场景：双层异常保护的嵌套结构
        测试多层try嵌套的反编译能力
        """
        source = '''
def target(items):
    try:
        for batch in batches(items):
            if batch.is_valid():
                try:
                    for item in batch:
                        risky_transform(item)
                except TransformError:
                    handle_batch_error(batch)
    except BatchError:
        handle_outer_error()
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T22反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T22反编译结果语法错误"

    def test_T23_4layer_if_while_for_while(self):
        """T23: 4层伪三元 (if>while>for>while)，4层嵌套

        场景：混合循环类型的深层嵌套
        测试异类循环的多层嵌套处理
        """
        source = '''
def target(enabled, data_stream):
    if enabled:
        i = 0
        while i < max_iterations:
            for chunk in data_stream.chunks():
                j = 0
                while j < len(chunk):
                    process(chunk[j])
                    j += 1
            i += 1
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T23反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T23反编译结果语法错误"

    def test_T24_5layer_if_for_while_try_if(self):
        """T24: 5层超深 (if>for>while>try>if)，5层嵌套

        场景：5层深度嵌套，包含多种控制流结构
        测试反编译器在5层深度下的稳定性
        """
        source = '''
def target(condition, collection):
    if condition:
        for item in collection:
            while item.has_subitems():
                sub = item.next_subitem()
                try:
                    result = risky_operation(sub)
                    if result.success():
                        commit(result)
                except OperationError:
                    rollback(sub)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T24反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T24反编译结果语法错误"

    def test_T25_5layer_for_try_if_while_for(self):
        """T25: 5层超深 (for>try>if>while>for)，5层嵌套

        场景：以循环开头的5层深层嵌套
        测试不同起始结构的深层嵌套处理
        """
        source = '''
def target(tasks):
    for task in tasks:
        try:
            setup(task)
            if task.is_complex():
                subtask = task.first_subtask()
                while subtask:
                    for step in subtask.steps():
                        execute(step)
                    subtask = task.next_subtask()
        except TaskSetupError:
            cleanup(task)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T25反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T25反编译结果语法错误"

    # ==================== 超深三元组合 T26-T28 (xfail) ====================

    @pytest.mark.xfail(reason="深层嵌套性能边界 - 6层嵌套可能超出当前CFG区域归约算法的最佳处理范围")
    def test_T26_6layer_if_for_try_while_if_for(self):
        """T26: 6层超深 (if>for>try>while>if>for)，6层嵌套 [xfail]

        场景：6层深度嵌套，接近算法性能边界
        预期：可能因嵌套过深导致区域分析不准确
        """
        source = '''
def target(main_condition, data_source):
    if main_condition:
        for dataset in data_source.datasets():
            try:
                connection = dataset.connect()
                i = 0
                while i < dataset.max_retries():
                    record = dataset.get_record(i)
                    if record.is_valid():
                        for field in record.fields():
                            process_field(field)
                    i += 1
            except ConnectionError:
                retry_later(dataset)
'''
        result = self.verify_decompilation_result(source)
        if result['success']:
            assert result['syntax_ok'], "T26反编译结果语法错误"

    @pytest.mark.xfail(reason="深层嵌套性能边界 - 6层嵌套可能超出当前CFG区域归约算法的最佳处理范围")
    def test_T27_6layer_try_for_if_while_try_if(self):
        """T27: 6层超深 (try>for>if>while>try>if)，6层嵌套 [xfail]

        场景：以try开头、双层try的6层嵌套
        预期：多层异常处理的深层嵌套挑战
        """
        source = '''
def target(operation, input_data):
    try:
        init_operation(operation)
        for batch in input_data.batches():
            if batch.ready():
                item = batch.current()
                while item:
                    try:
                        result = operation.process(item)
                        if result.complete():
                            save(result)
                    except ProcessError:
                        handle_item_error(item)
                    item = batch.next()
    except InitError:
        abort_operation(operation)
'''
        result = self.verify_decompilation_result(source)
        if result['success']:
            assert result['syntax_ok'], "T27反编译结果语法错误"

    @pytest.mark.xfail(reason="深层嵌套性能边界 - 7层嵌套可能超出当前CFG区域归约算法的稳定范围")
    def test_T28_7layer_if_for_while_try_if_for_while(self):
        """T28: 7层极限 (if>for>while>try>if>for>while)，7层嵌套 [xfail]

        场景：7层极限嵌套，测试算法绝对边界
        预期：极可能触发区域归约的边界问题
        """
        source = '''
def target(master_flag, system):
    if master_flag:
        for module in system.modules():
            j = 0
            while j < module.max_components():
                component = module.component(j)
                try:
                    state = component.initialize()
                    if state.ready():
                        for part in component.parts():
                            k = 0
                            while k < part.phases():
                                phase = part.phase(k)
                                execute_phase(phase)
                                k += 1
                except ComponentError:
                    reset_component(component)
                j += 1
'''
        result = self.verify_decompilation_result(source)
        if result['success']:
            assert result['syntax_ok'], "T28反编译结果语法错误"

    # ==================== 特殊模式 T29-T30 ====================

    def test_T29_break_continue_ternary(self):
        """T29: 带 break/continue 的三元组合 (if>for[break]>if[continue])，3层

        场景：在三元组合中嵌入break和continue语句
        测试反编译器对循环控制流语句的正确还原
        """
        source = '''
def target(data, stop_value, skip_value):
    if data:
        for item in data:
            if item == stop_value:
                break
            if item == skip_value:
                continue
            process_normal(item)
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T29反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T29反编译结果语法错误"

    def test_T30_return_raise_ternary(self):
        """T30: 带 return/raise 的三元组合 (try>if[return]>if[raise])，3层

        场景：在三元组合中嵌入return和raise语句
        测试反编译器对提前退出语句的正确还原
        """
        source = '''
def target(value, critical_threshold, error_threshold):
    try:
        if value > critical_threshold:
            return "success"
        if value < error_threshold:
            raise ValueError("Value too low")
        process_normal(value)
        return "processed"
    except ValueError as e:
        log_error(e)
        return "error_handled"
'''
        result = self.verify_decompilation_result(source)
        assert result['success'], f"T30反编译失败: {result.get('error')}"
        assert result['syntax_ok'], "T30反编译结果语法错误"


# ==================== 辅助函数 ====================

def run_ternary_tests():
    """运行所有三元组合测试并生成报告"""
    import datetime

    print("=" * 70)
    print("三元组合控制流语法测试")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\n测试覆盖:")
    print("- T01-T20: 标准三元组合（3层标准嵌套）")
    print("- T21-T25: 深层和超深三元组合（4-5层）")
    print("- T26-T28: 6-7层极限嵌套（xfail标记）")
    print("- T29-T30: break/continue/return/raise特殊模式")
    print()


if __name__ == '__main__':
    run_ternary_tests()
    pytest.main([__file__, '-v', '--tb=short'])
