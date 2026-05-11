#!/usr/bin/env python3
"""
三元组合深层嵌套测试 - 3层控制流嵌套完备性验证

覆盖所有主要控制流结构的三层嵌套排列组合。
三层嵌套是检验区域归约算法递归正确性的关键深度。

理论依据（编译器结构化分析理论 - Johnson et al. 1994）：
- 结构化分析通过迭代归约将CFG分解为层次化区域树
- 三层嵌套产生3阶区域嵌套关系，考验归约算法的传递性
- 每种排列对应唯一的支配树+回边+异常边组合模式

测试矩阵：
| ID | L1 | L2 | L3 | 说明 |
|----|----|----|----|------|
| NT01-NT10 | 核心三元组合 | | | Phase 4明确要求的10个 |
| NT11-NT20 | 异常处理三元变体 | | | try/except/finally的三层排列 |
| NT21-NT30 | 循环+条件+异常混合 | | | 三类结构的交叉嵌套 |
| NT31-NT35 | with/match三元组合 | | | 新语法特性的三层嵌套 |
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.helpers.decompilation_helper import MatrixTestBase


class TestTernaryDeepNesting(MatrixTestBase):
    """三元组合完备性测试 - 覆盖35种三层控制流嵌套"""

    # ========================================================================
    # NT01-NT10: Phase 4核心三元组合
    # ========================================================================

    def test_NT01_except_for_if(self):
        """NT01: except>for>if - 异常处理器>循环>条件

        嵌套路径：except → for → if
        CFG特征：异常恢复后进入循环，循环体内有条件分支
        测试要点：异常作用域不泄漏到for/if、循环变量在if中可见"""
        source = '''
def func():
    try:
        data = load()
    except LoadError:
        for item in default_items():
            if item.active:
                process(item)
'''
        self.verify_matrix_decompilation(source, 'NT01')

    def test_NT02_finally_while_if(self):
        """NT02: finally>while>if - 清理块>条件循环>条件

        嵌套路径：finally → while → if
        CFG特征：finally保证执行，内含循环和条件
        测试要点：finally语义不被内层结构干扰"""
        source = '''
def func():
    try:
        main_operation()
    finally:
        while pending_tasks():
            task = next_task()
            if task.urgent:
                execute_immediate(task)
            else:
                queue(task)
'''
        self.verify_matrix_decompilation(source, 'NT02')

    def test_NT03_for_except_if(self):
        """NT03: for>except>if - 循环>异常处理>条件

        嵌套路径：for → try-except → if
        CFG特征：每次迭代都可能触发异常，异常处理后有条件逻辑
        测试要点：循环中的异常不影响后续迭代、except体中的if独立"""
        source = '''
def func(items):
    results = []
    for item in items:
        try:
            value = transform(item)
        except TransformError:
            value = None
        if value is not None:
            results.append(value)
    return results
'''
        self.verify_matrix_decompilation(source, 'NT03')

    def test_NT04_while_try_for(self):
        """NT04: while>try>for - 条件循环>异常保护>迭代循环

        嵌套路径：while → try → for
        CFG特征：外层循环包含try块，try内有迭代循环
        测试要点：for中的异常被try捕获而不终止while"""
        source = '''
def func(pool):
    while pool.has_work():
        try:
            batch = pool.get_batch()
            for item in batch:
                process(item)
        except ProcessingError:
            pool.skip_batch()
'''
        self.verify_matrix_decompilation(source, 'NT04')

    def test_NT05_if_for_try(self):
        """NT05: if>for>try - 条件>循环>异常保护

        嵌套路径：if → for → try
        CFG特征：条件成立时进入循环，循环体有异常保护
        测试要点：if为False时整个for+try都不执行"""
        source = '''
def func(flag, items):
    if flag:
        for item in items:
            try:
                handle(item)
            except HandleError:
                log_error(item)
'''
        self.verify_matrix_decompilation(source, 'NT05')

    def test_NT06_try_if_for(self):
        """NT06: try>if>for - 异常保护>条件>循环

        嵌套路径：try → if → for
        CFG特征：try保护的条件判断内的循环
        测试要点：if或for中的异常都被外层try捕获"""
        source = '''
def func(data):
    try:
        if data.is_valid():
            for entry in data.entries():
                process(entry)
    except DataError:
        recover(data)
'''
        self.verify_matrix_decompilation(source, 'NT06')

    def test_NT07_for_if_while(self):
        """NT07: for>if>while - 迭代循环>条件>条件循环

        嵌套路径：for → if → while
        CFG特征：双层异构循环嵌套（for + while），中间有条件门控
        测试要点：两种循环的break/continue互不干扰"""
        source = '''
def func(groups):
    results = []
    for group in groups:
        if group.enabled:
            member = group.first()
            while member:
                results.append(member.value)
                member = member.next()
    return results
'''
        self.verify_matrix_decompilation(source, 'NT07')

    def test_NT08_while_for_if(self):
        """NT08: while>for>if - 条件循环>迭代循环>条件

        嵌套路径：while → for → if
        CFG特征：双层异构循环，内层for中有条件分支
        测试要点：while条件与for迭代器的独立性"""
        source = '''
def func(outer_data):
    results = []
    while outer_data.has_more():
        batch = outer_data.next_batch()
        for item in batch:
            if item.is_valid():
                results.append(item)
    return results
'''
        self.verify_matrix_decompilation(source, 'NT08')

    def test_NT09_if_try_while(self):
        """NT09: if>try>while - 条件>异常保护>条件循环

        嵌套路径：if → try → while
        CFG特征：条件分支内的异常保护循环
        测试要点：while中的异常被try捕获、break退出while不影响if"""
        source = '''
def func(mode, connection):
    if mode == "stream":
        try:
            while connection.alive():
                msg = connection.receive()
                dispatch(msg)
        except ConnectionLost:
            reconnect(connection)
'''
        self.verify_matrix_decompilation(source, 'NT09')

    def test_NT10_for_while_try(self):
        """NT10: for>while>try - 迭代循环>条件循环>异常保护

        嵌套路径：for → while → try
        CFG特征：for循环内含while循环，最内层有异常保护
        测试要点：三层嵌套的异常传播路径正确"""
        source = '''
def func(sources):
    all_results = []
    for src in sources:
        retries = 3
        while retries > 0:
            try:
                result = fetch_from(src)
                all_results.append(result)
                break
            except FetchError as e:
                log(e)
                retries -= 1
    return all_results
'''
        self.verify_matrix_decompilation(source, 'NT10')

    # ========================================================================
    # NT11-NT20: 异常处理三元变体
    # ========================================================================

    def test_NT11_try_except_finally_for(self):
        """NT11: try>except>finally>for - 完整异常处理含循环

        嵌套路径：try → except → finally → for (finally内含for)
        测试要点：finally中的for始终执行"""
        source = '''
def func():
    try:
        work()
    except Error:
        fix()
    finally:
        for resource in acquired_resources():
            release(resource)
'''
        self.verify_matrix_decompilation(source, 'NT11')

    def test_NT12_for_try_except_else(self):
        """NT12: for>try>except>else - 循环内完整异常处理

        嵌套路径：for → try → except → else
        测试要点：循环每次迭代的异常处理独立性"""
        source = '''
def func(items):
    results = []
    for item in items:
        try:
            val = convert(item)
        except ConversionError:
            val = None
        else:
            val = enhance(val)
        results.append(val)
    return results
'''
        self.verify_matrix_decompilation(source, 'NT12')

    def test_NT13_while_try_finally_if(self):
        """NT13: while>try>finally>if

        嵌套路径：while → try → finally → if"""
        source = '''
def func(worker):
    while worker.busy():
        try:
            worker.process()
        finally:
            if worker.state_changed():
                worker.save_state()
'''
        self.verify_matrix_decompilation(source, 'NT13')

    def test_NT14_if_for_try_except(self):
        """NT14: if>for>try>except

        嵌套路径：if → for → try → except"""
        source = '''
def func(enabled, tasks):
    if enabled:
        for task in tasks:
            try:
                run(task)
            except TaskFailed:
                report_failure(task)
'''
        self.verify_matrix_decompilation(source, 'NT14')

    def test_NT15_try_for_while_except(self):
        """NT15: try>for>while>except - 外层try包裹双层循环

        嵌套路径：try → for → while → (except在外层)
        测试要点：for或while中的异常都由同一except处理"""
        source = '''
def func(matrix):
    try:
        for row in matrix:
            col = 0
            while col < len(row):
                process(row[col])
                col += 1
    except ProcessError:
        handle_error()
'''
        self.verify_matrix_decompilation(source, 'NT15')

    def test_NT16_except_for_while_if(self):
        """NT16: except>for>while>if - 异常处理器内三层嵌套

        嵌套路径：except → for → while → if"""
        source = '''
def func():
    try:
        crash()
    except CrashError:
        for group in recovery_groups():
            member = group.head()
            while member:
                if member.needs_fix():
                    repair(member)
                member = member.next()
'''
        self.verify_matrix_decompilation(source, 'NT16')

    def test_NT17_finally_if_for_while(self):
        """NT17: finally>if>for>while - finally内三层嵌套

        嵌套路径：finally → if → for → while"""
        source = '''
def func():
    try:
        risky_operation()
    finally:
        if cleanup_required:
            for subsystem in subsystems():
                conn = subsystem.connection()
                while conn.open():
                    conn.flush()
                    conn.close()
'''
        self.verify_matrix_decompilation(source, 'NT17')

    def test_NT18_try_except_try_except(self):
        """NT18: try>except>try>except - 双重异常处理嵌套

        嵌套路径：try → except → (内层try) → (内层except)"""
        source = '''
def func():
    try:
        step1()
    except Step1Error:
        try:
            fallback1()
        except FallbackError:
            emergency()
'''
        self.verify_matrix_decompilation(source, 'NT18')

    def test_NT19_for_try_for_try(self):
        """NT19: for>try>for>try - 双层循环各带异常保护

        嵌套路径：for → try → for → try"""
        source = '''
def func(outer_list):
    for outer in outer_list:
        try:
            inner_items = expand(outer)
            for inner in inner_items:
                try:
                    process_pair(outer, inner)
                except InnerError:
                    skip_inner(inner)
        except OuterError:
            skip_outer(outer)
'''
        self.verify_matrix_decompilation(source, 'NT19')

    def test_NT20_while_if_try_while(self):
        """NT20: while>if>try>while - 含异常保护的内外层while

        嵌套路径：while → if → try → while"""
        source = '''
def func(server):
    while server.running():
        if server.has_request():
            try:
                req = server.accept()
                while not req.complete():
                    req.read_chunk()
            except IOError:
                server.reset()
'''
        self.verify_matrix_decompilation(source, 'NT20')

    # ========================================================================
    # NT21-NT30: 循环+条件+异常混合三元组合
    # ========================================================================

    def test_NT21_if_while_for_try(self):
        """NT21: if>while>for>try - 四层（条件+双循环+异常）

        嵌套路径：if → while → for → try"""
        source = '''
def func(enabled, data):
    if enabled:
        while data.has_pages():
            page = data.next_page()
            for record in page.records():
                try:
                    analyze(record)
                except AnalysisError:
                    mark_skipped(record)
'''
        self.verify_matrix_decompilation(source, 'NT21')

    def test_NT22_for_if_while_try(self):
        """NT22: for>if>while>try

        嵌套路径：for → if → while → try"""
        source = '''
def func(batches):
    for batch in batches:
        if batch.valid():
            retry = 3
            while retry > 0:
                try:
                    execute(batch)
                    break
                except ExecutionError:
                    retry -= 1
'''
        self.verify_matrix_decompilation(source, 'NT22')

    def test_NT23_while_for_if_try(self):
        """NT23: while>for>if>try

        嵌套路径：while → for → if → try"""
        source = '''
def func(iterator):
    while iterator.has_next():
        chunk = iterator.next_chunk()
        for item in chunk:
            if item.processable():
                try:
                    compute(item)
                except ComputeError:
                    fallback(item)
'''
        self.verify_matrix_decompilation(source, 'NT23')

    def test_NT24_try_while_if_for(self):
        """NT24: try>while>if>for

        嵌套路径：try → while → if → for"""
        source = '''
def func(stream):
    try:
        while stream.readable():
            header = stream.peek()
            if header.is_array():
                for element in header.elements():
                    parse(element)
    except ParseError:
        stream.recover()
'''
        self.verify_matrix_decompilation(source, 'NT24')

    def test_NT25_if_try_while_for(self):
        """NT25: if>try>while>for

        嵌套路径：if → try → while → for"""
        source = '''
def func(mode, source):
    if mode == "deep":
        try:
            cursor = source.cursor()
            while cursor.valid():
                row = cursor.row()
                for cell in row.cells():
                    extract(cell)
        except CursorError:
            source.reset_cursor()
'''
        self.verify_matrix_decompilation(source, 'NT25')

    def test_NT26_for_try_if_while(self):
        """NT26: for>try>if>while

        嵌套路径：for → try → if → while"""
        source = '''
def func(jobs):
    for job in jobs:
        try:
            worker = job.acquire_worker()
            if worker.available():
                while job.has_steps():
                    step = job.next_step()
                    worker.execute(step)
        except WorkerError:
            job.release_worker()
'''
        self.verify_matrix_decompilation(source, 'NT26')

    def test_NT27_while_if_try_for(self):
        """NT27: while>if>try>for

        嵌套路径：while → if → try → for"""
        source = '''
def func(pipeline):
    while pipeline.active():
        stage = pipeline.current_stage()
        if stage.needs_input():
            try:
                inputs = gather_inputs(stage)
                for inp in inputs:
                    stage.feed(inp)
            except GatherError:
                stage.use_defaults()
'''
        self.verify_matrix_decompilation(source, 'NT27')

    def test_NT28_try_for_while_if(self):
        """NT28: try>for>while>if

        嵌套路径：try → for → while → if"""
        source = '''
def func(dataset):
    try:
        for table in dataset.tables():
            reader = table.reader()
            while reader.has_row():
                row = reader.read_row()
                if not row.empty():
                    emit(row)
    except DatasetError:
        emit_sentinel()
'''
        self.verify_matrix_decompilation(source, 'NT28')

    def test_NT29_if_for_try_while(self):
        """NT29: if>for>try>while

        嵌套路径：if → for → try → while"""
        source = '''
def func(process, inputs):
    if process.configured():
        for input in inputs:
            try:
                handle = process.open(input)
                while handle.more_data():
                    chunk = handle.read()
                    process.consume(chunk)
            except OpenError:
                process.skip(input)
'''
        self.verify_matrix_decompilation(source, 'NT29')

    def test_NT30_for_while_try_if(self):
        """NT30: for>while>try>if

        嵌套路径：for → while → try → if"""
        source = '''
def func(clients):
    for client in clients:
        session = client.connect()
        attempts = 0
        while attempts < 3 and session.active():
            try:
                response = session.query()
                if response.ok():
                    store(response)
                else:
                    retry_response(response)
            except QueryError:
                attempts += 1
'''
        self.verify_matrix_decompilation(source, 'NT30')

    # ========================================================================
    # NT31-NT35: with/match 三元组合
    # ========================================================================

    def test_NT31_with_for_if(self):
        """NT31: with>for>if - 上下文管理器>循环>条件"""
        source = '''
def func(resource):
    with open(resource) as f:
        for line in f:
            if line.strip():
                process(line)
'''
        self.verify_matrix_decompilation(source, 'NT31')

    def test_NT32_with_try_for(self):
        """NT32: with>try>for - 上下文管理器>异常保护>循环"""
        source = '''
def func(filepath):
    with open(filepath) as f:
        try:
            for record in parse_records(f):
                store(record)
        except ParseError:
            log_parse_failure(f.name)
'''
        self.verify_matrix_decompilation(source, 'NT32')

    def test_NT33_for_with_try(self):
        """NT33: for>with>try - 循环>上下文管理器>异常保护"""
        source = '''
def func(files):
    for path in files:
        with open(path) as f:
            try:
                data = json.load(f)
                results.append(data)
            except JSONDecodeError:
                results.append(None)
'''
        self.verify_matrix_decompilation(source, 'NT33')

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_NT34_match_if_for(self):
        """NT34: match>if>for - 模式匹配>条件>循环"""
        source = '''
def func(value, items):
    match value:
        case "all":
            for item in items:
                process_all(item)
        case "filtered":
            if items:
                for item in items:
                    if item.keep:
                        process_filtered(item)
        case _:
            pass
'''
        self.verify_matrix_decompilation(source, 'NT34', min_equivalence=0.78)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="需要Python 3.10+")
    def test_NT35_for_match_try(self):
        """NT35: for>match>try - 循环>模式匹配>异常保护"""
        source = '''
def func(commands):
    results = []
    for cmd in commands:
        match cmd:
            case {"op": "load", "path": p}:
                try:
                    results.append(load_file(p))
                except IOError:
                    results.append(None)
            case {"op": "compute", "x": x, "y": y}:
                results.append(x * y)
            case _:
                results.append(UNKNOWN)
    return results
'''
        self.verify_matrix_decompilation(source, 'NT35', min_equivalence=0.78)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
