"""
CFG AST转换器 - 将CFG生成的字典格式AST转换为项目ASTNode对象

这是CFG模块完善的关键组件，负责将CFG分析结果转换为可执行的AST树。
"""

import types
from typing import Dict, Any, Optional, List, Union, Callable
import logging

# 导入项目AST节点
from core.ast_nodes import (
    ASTNode, ASTBlock, ASTIf, ASTFor, ASTWhile, ASTTry, ASTWith,
    ASTFunctionDef, ASTClassDef, ASTReturn, ASTYield, ASTAssign, ASTAugAssign, ASTAnnAssign, ASTExpr,
    ASTName, ASTConstant, ASTBinary, ASTUnary, ASTCompare,
    ASTCall, ASTAttribute, ASTSubscript, ASTList, ASTTuple,
    ASTDict, ASTSet, ASTPass, ASTBreak, ASTContinue, ASTDelete,
    ASTExceptHandler, ASTWithItem, ASTJoinedStr, ASTFormattedValue,
    ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr, ASTComprehension,
    ASTNamedExpr, ASTIfExp, ASTImport, ASTImportFrom, ASTAlias, ASTAwaitable, ASTRaise,
    ASTLambda, ASTSlice, ASTAssert, ASTGlobal, ASTNonlocal,
    # [Python 3.10+] 模式匹配
    ASTMatch, ASTCase, ASTMatchClass, ASTMatchMapping, ASTMatchSequence
)

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """AST转换错误"""
    pass


class CFGASTConverter:
    """
    CFG AST到项目AST的转换器
    
    将CFG模块生成的字典格式AST转换为项目定义的ASTNode对象。
    这是CFG模块完善到100%的关键组件。
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.original_consts: Optional[List[Any]] = None  # [关键修复] 原始常量池
        self._converters: Dict[str, Callable] = {
            # 语句类型
            'Module': self._convert_module,
            'FunctionDef': self._convert_function_def,
            'AsyncFunctionDef': self._convert_function_def,
            'ClassDef': self._convert_class_def,
            'If': self._convert_if,
            'For': self._convert_for,
            'AsyncFor': self._convert_async_for,
            'While': self._convert_while,
            'Try': self._convert_try,
            'With': self._convert_with,
            'AsyncWith': self._convert_async_with,
            'Return': self._convert_return,
            'Yield': self._convert_yield,
            'YieldFrom': self._convert_yield_from,
            'Assign': self._convert_assign,
            'AugAssign': self._convert_aug_assign,
            'AnnAssign': self._convert_ann_assign,
            'Assert': self._convert_assert,
            'Expr': self._convert_expr_stmt,
            'Pass': self._convert_pass,
            'Break': self._convert_break,
            'Continue': self._convert_continue,
            'Delete': self._convert_delete,
            'Import': self._convert_import,
            'ImportFrom': self._convert_import_from,
            'Global': self._convert_global,
            'Nonlocal': self._convert_nonlocal,
            'Block': self._convert_block,
            'Sequence': self._convert_sequence,

            # 表达式类型（作为语句时）
            'Constant': self._convert_constant_expr,
            'Name': self._convert_name_expr,
            'BinOp': self._convert_binop_expr,
            'UnaryOp': self._convert_unaryop_expr,
            'Compare': self._convert_compare_expr,
            'Call': self._convert_call_expr,
            'Attribute': self._convert_attribute_expr,
            'Subscript': self._convert_subscript_expr,
            'List': self._convert_list_expr,
            'Tuple': self._convert_tuple_expr,
            'Dict': self._convert_dict_expr,
            'Set': self._convert_set_expr,
            'ListComp': self._convert_list_comp_expr,
            'SetComp': self._convert_set_comp_expr,
            'DictComp': self._convert_dict_comp_expr,
            'GeneratorExp': self._convert_generator_exp_expr,
            'NamedExpr': self._convert_named_expr,
            'Await': self._convert_await_expr,
            'Raise': self._convert_raise_expr,
            'Lambda': self._convert_lambda_expr,
            'IfExp': self._convert_ifexp_full,  # [关键修复] 添加条件表达式处理
            
            # [Python 3.10+] 模式匹配
            'Match': self._convert_match,
            'Case': self._convert_case,
        }
    
    def convert(self, node_dict: Dict[str, Any]) -> Optional[ASTNode]:
        """
        将CFG AST字典转换为项目AST节点
        
        Args:
            node_dict: CFG生成的AST字典
            
        Returns:
            转换后的ASTNode对象，转换失败返回None
        """
        if not node_dict:
            return None
        
        if isinstance(node_dict, list):
            if len(node_dict) == 1:
                node_dict = node_dict[0]
            else:
                results = []
                for item in node_dict:
                    r = self.convert(item)
                    if r:
                        results.append(r)
                if len(results) == 1:
                    return results[0]
                return ASTBlock(results) if results else None
        
        node_type = node_dict.get('type')
        if not node_type:
            logger.warning("Node dictionary missing 'type' field")
            return None
        
        
        converter = self._converters.get(node_type)
        if converter:
            try:
                result = converter(node_dict)
                if self.verbose:
                    logger.info(f"Converted {node_type} node successfully")
                return result
            except Exception as e:
                logger.error(f"Error converting {node_type} node: {e}")
                import traceback
                traceback.print_exc()
                if self.verbose:
                    logger.exception("Conversion error details")
                return None
        else:
            logger.warning(f"Unknown node type: {node_type}")
            # 尝试作为表达式处理
            return self._convert_expression(node_dict)
    
    def convert_body(self, body_list: List[Dict[str, Any]]) -> ASTBlock:
        """
        转换语句列表为代码块
        
        Args:
            body_list: CFG AST字典列表
            
        Returns:
            包含所有转换后节点的ASTBlock
        """
        block = ASTBlock()
        for i, node_dict in enumerate(body_list):
            # [关键修复] 处理列表类型的节点（如 init_statements + [while_loop]）
            if isinstance(node_dict, list):
                for j, item in enumerate(node_dict):
                    if isinstance(item, dict):
                        node_type = item.get('type', 'Unknown')
                        node = self.convert(item)
                        if node:
                            block.append(node)
                        else:
                            pass
                continue
            
            node_type = node_dict.get('type', 'Unknown')
            node = self.convert(node_dict)
            if node:
                block.append(node)
            else:
                pass
        return block
    
    # ==================== 语句转换方法 ====================
    
    def _convert_module(self, node_dict: Dict[str, Any]) -> ASTBlock:
        """转换模块节点"""
        # [关键修复] 保存原始常量池信息
        self.original_consts = node_dict.get('original_consts')
        if self.verbose and self.original_consts:
            pass

        block = self.convert_body(node_dict.get('body', []))

        if not block.nodes:
            block.append(ASTPass())

        return block

    def _create_const_placeholder(self, consts: List[Any]) -> Optional[ASTBlock]:
        """
        [关键修复] 创建常量占位符语句

        为了保持常量池顺序与原始代码一致，创建一系列虚拟的赋值语句，
        每个语句引用一个常量，确保常量在常量池中保持原始顺序。

        Args:
            consts: 原始常量池列表

        Returns:
            常量占位符ASTBlock节点，如果不需要则返回None
        """
        # 过滤出需要在占位符中使用的常量
        # 跳过None（通常是返回值）和code对象
        filtered_consts = []
        for const in consts:
            if const is not None and not isinstance(const, types.CodeType):
                filtered_consts.append(const)

        if not filtered_consts:
            return None

        # [关键修复] 创建一系列赋值语句，每个引用一个常量
        # 使用下划线前缀表示这是内部变量
        # 例如:
        #   _0 = True
        #   _1 = False
        # 这样可以确保每个常量都被LOAD_CONST引用，且顺序正确
        block = ASTBlock()
        for i, const in enumerate(filtered_consts):
            assign = ASTAssign(
                targets=[ASTName(name=f'_{i}')],
                value=ASTConstant(value=const)
            )
            block.append(assign)

        return block
    
    def _convert_function_def(self, node_dict: Dict[str, Any]) -> ASTFunctionDef:
        """转换函数定义节点"""
        name = node_dict.get('name', '<anonymous>')
        
        # [关键修复] 处理args参数 - 可能是列表或字典
        raw_args = node_dict.get('args', [])
        defaults = []  # [关键修复] 初始化默认值列表
        kwonlyargs = []  # [关键修复] 初始化关键字-only参数列表
        kw_defaults = []  # [关键修复] 初始化关键字-only默认值列表
        
        if isinstance(raw_args, list):
            # 直接是参数名列表（从ASTGeneratorV2来的格式）
            args = raw_args
            vararg = node_dict.get('vararg')
            kwarg = node_dict.get('kwarg')
        else:
            # 是字典格式，需要转换
            args_dict = self._convert_arguments(raw_args)
            # 从args_dict中提取参数列表和vararg/kwarg
            args = args_dict.get('args', []) if isinstance(args_dict, dict) else []
            vararg = args_dict.get('vararg') if isinstance(args_dict, dict) else None
            kwarg = args_dict.get('kwarg') if isinstance(args_dict, dict) else None
            # [关键修复] 提取默认值信息
            defaults = args_dict.get('defaults', []) if isinstance(args_dict, dict) else []
            kwonlyargs = args_dict.get('kwonlyargs', []) if isinstance(args_dict, dict) else []
            kw_defaults = args_dict.get('kw_defaults', []) if isinstance(args_dict, dict) else []
        
        body = self.convert_body(node_dict.get('body', []))
        
        # [异步] 提取异步标志
        is_async = node_dict.get('is_async', False) or node_dict.get('type') == 'AsyncFunctionDef'
        
        # ASTFunctionDef需要name作为必需参数
        func_def = ASTFunctionDef(name=name, args=args, body=body, vararg=vararg, kwarg=kwarg, is_async=is_async)
        
        # [关键修复] 设置默认值信息
        func_def._defaults = defaults
        func_def._kwonlyargs = kwonlyargs
        func_def._kw_defaults = kw_defaults
        
        # 处理装饰器
        decorators = node_dict.get('decorator_list', [])
        if decorators:
            func_def._decorators = [
                self._convert_expression(d) for d in decorators
            ]
        
        # 处理返回注解
        returns = node_dict.get('returns')
        if returns:
            func_def._returns = self._convert_expression(returns)
        
        return func_def
    
    def _convert_class_def(self, node_dict: Dict[str, Any]) -> ASTClassDef:
        """转换类定义节点"""
        name = node_dict.get('name', '<anonymous>')
        bases = [
            self._convert_expression(b) for b in node_dict.get('bases', [])
        ]
        
        # [关键修复] 转换类体
        # 只过滤类体级别的return语句，不过滤方法内的return
        body_list = node_dict.get('body', [])
        filtered_body = ASTBlock()
        for node_dict_item in body_list:
            node_type = node_dict_item.get('type', '')
            # 只过滤直接的Return语句（类体级别）
            # 方法内的Return在FunctionDef的body中，不应该在这里过滤
            if node_type == 'Return':
                # 跳过类体中的return语句
                continue
            node = self.convert(node_dict_item)
            if node:
                filtered_body.append(node)
        
        # 使用过滤后的body
        body = filtered_body if filtered_body.nodes else ASTBlock([ASTPass()])

        # ASTClassDef需要name作为必需参数
        # [关键修复] 始终使用ASTBlock对象作为body
        class_def = ASTClassDef(name=name, bases=bases, body=body)
        
        # [关键修复] 处理关键字参数（如metaclass=MetaClass）
        keywords = node_dict.get('keywords', [])
        if keywords:
            class_def._keywords = keywords
        
        # 处理装饰器
        decorators = node_dict.get('decorator_list', [])
        if decorators:
            class_def._decorators = [
                self._convert_expression(d) for d in decorators
            ]
        
        # [关键修复] 处理类型参数（Python 3.12+ 泛型语法）
        type_params = node_dict.get('type_params', [])
        if type_params:
            class_def.type_params = type_params
        
        return class_def
    
    def _convert_if(self, node_dict: Dict[str, Any]) -> ASTIf:
        """转换if语句节点"""

        is_nested = node_dict.get('_is_nested_if', False)

        # 转换条件表达式
        test_dict = node_dict.get('test', {})
        if isinstance(test_dict, list):
            if len(test_dict) == 1:
                test_dict = test_dict[0]
            elif len(test_dict) > 1:
                test_dict = {'type': 'BoolOp', 'op': 'And', 'values': test_dict}
            else:
                test_dict = {}
        test = self._convert_expression(test_dict)
        if not test:
            test = ASTConstant(True)
        
        # 转换then分支
        # [关键修复] CFG AST可能使用'body'或'then_body'字段名
        body_list = node_dict.get('body') or node_dict.get('then_body', [])
        body = self.convert_body(body_list)
        
        # [关键修复] 处理elif_test/elif_body
        # 如果存在elif_test和elif_body，将它们转换为orelse中的if节点
        elif_tests = node_dict.get('elif_test', [])
        elif_bodies = node_dict.get('elif_body', [])
        final_else = node_dict.get('final_else', [])
        # [关键修复] CFG AST可能使用'orelse'或'else_body'字段名
        original_orelse = node_dict.get('orelse') or node_dict.get('else_body', [])
        
        # [调试] 打印original_orelse
        
        # 构建orelse
        orelse = []
        
        # 添加elif链
        if elif_tests and elif_bodies:
            # [关键修复] 构建elif链，每个elif都是一个ASTIf节点
            # 通过orelse链连接所有的elif
            prev_elif = None
            for i in range(len(elif_tests) - 1, -1, -1):
                elif_test = elif_tests[i]
                if isinstance(elif_test, list):
                    if len(elif_test) == 1:
                        elif_test = elif_test[0]
                    elif len(elif_test) > 1:
                        elif_test = {'type': 'BoolOp', 'op': 'And', 'values': elif_test}
                    else:
                        elif_test = {}
                elif_test_node = self._convert_expression(elif_test)
                elif_body_block = self.convert_body(elif_bodies[i])
                
                # 创建当前elif节点，orelse指向下一个elif或else
                if prev_elif is not None:
                    current_elif = ASTIf(elif_test_node, elif_body_block, ASTBlock([prev_elif]))
                    current_elif._is_elif = True
                elif final_else:
                    final_else_nodes = []
                    for node in final_else:
                        converted = self.convert(node)
                        if converted:
                            final_else_nodes.append(converted)
                    if final_else_nodes:
                        current_elif = ASTIf(elif_test_node, elif_body_block, ASTBlock(final_else_nodes))
                    else:
                        current_elif = ASTIf(elif_test_node, elif_body_block, None)
                    current_elif._is_elif = True
                else:
                    current_elif = ASTIf(elif_test_node, elif_body_block, None)
                    current_elif._is_elif = True
                
                prev_elif = current_elif
            
            # 添加第一个elif到orelse
            if prev_elif:
                orelse.append(prev_elif)
        
        # [关键修复] 如果没有elif链，使用原始orelse
        # [关键修复] 如果有elif链，也需要处理original_orelse中的嵌套if节点
        # [关键修复] 但是，如果original_orelse中的节点已经在final_else中，跳过
        has_elif_chain = bool(elif_tests and elif_bodies)
        if original_orelse:
            final_else_ids = set()
            for node in final_else:
                if isinstance(node, dict):
                    node_id = (node.get('type'), node.get('lineno'))
                    final_else_ids.add(node_id)
            
            for node in original_orelse:
                if isinstance(node, dict):
                    node_id = (node.get('type'), node.get('lineno'))
                    if node_id in final_else_ids:
                        continue
                
                converted = self.convert(node)
                if converted:
                    is_nested = isinstance(node, dict) and node.get('_is_nested_if', False)
                    is_elif = isinstance(node, dict) and node.get('_is_elif', False)
                    if is_nested and isinstance(converted, ASTIf):
                        converted._is_nested_if = True
                    if is_elif and isinstance(converted, ASTIf):
                        converted._is_elif = True
                    
                    if has_elif_chain and orelse and isinstance(orelse[-1], ASTIf) and not is_nested:
                        last_elif = orelse[-1]
                        while last_elif.orelse and last_elif.orelse.nodes and isinstance(last_elif.orelse.nodes[-1], ASTIf):
                            last_elif = last_elif.orelse.nodes[-1]
                        if last_elif.orelse:
                            last_elif.orelse.nodes.append(converted)
                        else:
                            last_elif.orelse = ASTBlock([converted])
                    else:
                        orelse.append(converted)
        
        # [关键修复] 如果没有elif链，但有final_else，将final_else添加到orelse
        # 这种情况发生在简单的if-else结构中（没有elif）
        if not elif_tests and final_else:
            for node in final_else:
                converted = self.convert(node)
                if converted:
                    orelse.append(converted)
        
        if orelse:
            orelse_block = ASTBlock(orelse)
        else:
            orelse_block = None
        
        result = ASTIf(test, body, orelse_block)
        if node_dict.get('_is_elif', False):
            result._is_elif = True
        return result
    
    def _convert_for(self, node_dict: Dict[str, Any]) -> ASTFor:
        """转换for循环节点"""
        # 转换循环变量
        target_dict = node_dict.get('target', {})
        target = self._convert_expression(target_dict)
        if not target:
            target = ASTName('<target>')
        
        # 转换迭代器
        iter_dict = node_dict.get('iter', {})
        iter_node = self._convert_expression(iter_dict)
        if not iter_node:
            iter_node = ASTName('<iterator>')
        
        # 转换循环体
        body = self.convert_body(node_dict.get('body', []))
        
        # 转换else分支
        orelse = node_dict.get('orelse', [])
        if orelse:
            orelse_block = self.convert_body(orelse)
        else:
            orelse_block = None
        
        # ASTFor需要target作为必需参数
        for_node = ASTFor(target=target, iter_node=iter_node, body=body, else_block=orelse_block)
        
        return for_node
    
    def _convert_async_for(self, node_dict: Dict[str, Any]) -> ASTFor:
        """转换异步for循环节点"""
        # 转换循环变量
        target_dict = node_dict.get('target', {})
        target = self._convert_expression(target_dict)
        if not target:
            target = ASTName('<target>')
        
        # 转换迭代器
        iter_dict = node_dict.get('iter', {})
        iter_node = self._convert_expression(iter_dict)
        if not iter_node:
            iter_node = ASTName('<iterator>')
        
        # 转换循环体
        body = self.convert_body(node_dict.get('body', []))
        
        # 转换else分支
        orelse = node_dict.get('orelse', [])
        if orelse:
            orelse_block = self.convert_body(orelse)
        else:
            orelse_block = None
        
        # 创建异步for节点，设置is_async=True
        for_node = ASTFor(target=target, iter_node=iter_node, body=body, else_block=orelse_block, is_async=True)
        
        return for_node
    
    def _convert_while(self, node_dict: Dict[str, Any]) -> ASTWhile:
        """转换while循环节点"""
        # 转换条件
        test_dict = node_dict.get('test', {})
        test = self._convert_expression(test_dict)
        if not test:
            test = ASTConstant(True)
        
        # 转换循环体
        body = self.convert_body(node_dict.get('body', []))
        
        # 转换else分支
        orelse = node_dict.get('orelse', [])
        if orelse:
            orelse_block = self.convert_body(orelse)
        else:
            orelse_block = None
        
        return ASTWhile(test, body, orelse_block)
    
    def _convert_try(self, node_dict: Dict[str, Any]) -> ASTTry:
        """转换try-except节点"""
        # 转换try体
        body = self.convert_body(node_dict.get('body', []))
        
        # 转换except handlers
        handlers = []
        handlers_list = node_dict.get('handlers', [])
        for handler_dict in handlers_list:
            if isinstance(handler_dict, dict):
                handler = self._convert_except_handler(handler_dict)
                if handler:
                    handlers.append(handler)
        
        # 转换else分支
        orelse = node_dict.get('orelse', [])
        if orelse:
            orelse_block = self.convert_body(orelse)
        else:
            orelse_block = None
        
        # 转换finally分支
        finalbody = node_dict.get('finalbody', [])
        if finalbody:
            finalbody_block = self.convert_body(finalbody)
        else:
            finalbody_block = None
        
        # [关键修复] ASTTry的属性是只读的，必须通过构造函数设置
        try_node = ASTTry(body=body, handlers=handlers, orelse=orelse_block, finalbody=finalbody_block)
        
        return try_node
    
    def _convert_with(self, node_dict: Dict[str, Any]) -> ASTWith:
        """转换with语句节点"""
        # 转换items
        items = []
        for item_dict in node_dict.get('items', []):
            item = self._convert_with_item(item_dict)
            if item:
                items.append(item)

        # 转换body
        body = self.convert_body(node_dict.get('body', []))

        # [关键修复] 检查是否是异步with
        is_async = node_dict.get('is_async', False)
        with_node = ASTWith(items=items, is_async=is_async)
        with_node.body = body

        return with_node

    def _convert_async_with(self, node_dict: Dict[str, Any]) -> ASTWith:
        """转换异步with语句节点"""
        # 转换items
        items = []
        for item_dict in node_dict.get('items', []):
            item = self._convert_with_item(item_dict)
            if item:
                items.append(item)

        # 转换body
        body = self.convert_body(node_dict.get('body', []))

        # [关键修复] 创建异步with节点 - 使用关键字参数
        with_node = ASTWith(items=items, is_async=True)
        with_node.body = body

        return with_node

    def _convert_return(self, node_dict: Dict[str, Any]) -> ASTReturn:
        """转换return语句节点"""
        value_dict = node_dict.get('value')
        if value_dict:
            value = self._convert_expression(value_dict)
            ret = ASTReturn(value)
        else:
            # [关键修复] ASTReturn需要提供value参数，使用None表示return None
            ret = ASTReturn(None)
        # [关键修复] 设置 _in_function 属性为 True，确保 return 语句能被正确生成
        ret._in_function = True
        return ret

    def _convert_yield(self, node_dict: Dict[str, Any]) -> ASTYield:
        """转换yield语句节点"""
        value_dict = node_dict.get('value')
        if value_dict:
            value = self._convert_expression(value_dict)
            return ASTYield(value)
        return ASTYield()

    def _convert_yield_from(self, node_dict: Dict[str, Any]) -> ASTYield:
        """转换yield from语句节点"""
        value_dict = node_dict.get('value')
        if value_dict:
            value = self._convert_expression(value_dict)
            return ASTYield(value, is_from=True)
        return ASTYield(is_from=True)

    def _convert_yield_expr(self, expr_dict: Dict[str, Any]) -> ASTYield:
        """转换yield表达式"""
        value_dict = expr_dict.get('value')
        if value_dict:
            value = self._convert_expression(value_dict)
            return ASTYield(value)
        return ASTYield()
    
    def _convert_starred_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTNode]:
        """[关键修复] 转换Starred表达式（用于解包赋值中的*rest）"""
        value_dict = expr_dict.get('value', {})
        if value_dict:
            value = self._convert_expression(value_dict)
            if value:
                return {'type': 'Starred', 'value': value}
        return None

    def _convert_iter_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTNode]:
        """[关键修复] 转换Iter类型（推导式的迭代对象包装）

        Iter类型是推导式中迭代对象的包装，内部包含实际的迭代对象（如DictComp、ListComp等）。
        我们只需要返回内部值的转换结果。
        """
        value_dict = expr_dict.get('value', {})
        if value_dict:
            return self._convert_expression(value_dict)
        return None

    def _convert_assign(self, node_dict: Dict[str, Any]) -> ASTAssign:
        """转换赋值语句节点"""
        # [关键修复-2026] 转换所有目标（支持链式赋值 a = b = c = 0）
        targets = node_dict.get('targets', [])
        converted_targets = []
        
        for target_dict in targets:
            target = self._convert_expression(target_dict)
            if target:
                converted_targets.append(target)
            else:
                converted_targets.append(ASTName('<target>'))
        
        if not converted_targets:
            converted_targets = [ASTName('<target>')]
        
        # 转换值
        value_dict = node_dict.get('value', {})
        value = self._convert_expression(value_dict)
        if not value:
            value = ASTConstant(None)
        
        # ASTAssign需要targets列表（支持多目标用于链式赋值）
        result = ASTAssign(converted_targets, value)
        
        if node_dict.get('is_chain_assign'):
            result.is_chain_assign = True
        
        return result
    
    def _convert_aug_assign(self, node_dict: Dict[str, Any]) -> ASTAugAssign:
        """转换增强赋值语句节点（如 +=, -=）"""
        # 转换目标
        target_dict = node_dict.get('target', {})
        target = self._convert_expression(target_dict)
        if not target:
            target = ASTName('<target>')
        
        # 转换值
        value_dict = node_dict.get('value', {})
        value = self._convert_expression(value_dict)
        if not value:
            value = ASTConstant(None)
        
        # 获取操作符
        op = node_dict.get('op', '+=')
        
        # 使用专门的ASTAugAssign节点
        return ASTAugAssign(target, op, value)
    
    def _convert_ann_assign(self, node_dict: Dict[str, Any]) -> ASTAnnAssign:
        """转换带注解的赋值语句节点（如 name: str = value）"""
        # 转换目标
        target_dict = node_dict.get('target', {})
        target = self._convert_expression(target_dict)
        if not target:
            target = ASTName('<target>')
        
        # 转换注解
        annotation_dict = node_dict.get('annotation', {})
        annotation = self._convert_expression(annotation_dict)
        if not annotation:
            annotation = ASTName('<annotation>')
        
        # 转换值（可能为None）
        value_dict = node_dict.get('value')
        value = None
        if value_dict is not None:
            value = self._convert_expression(value_dict)
        
        # 获取simple标志
        simple = node_dict.get('simple', 1)
        
        # 使用专门的ASTAnnAssign节点
        return ASTAnnAssign(target, annotation, value, simple)
    
    def _convert_assert(self, node_dict: Dict[str, Any]) -> ASTAssert:
        """转换assert语句节点"""
        # 转换测试条件
        test_dict = node_dict.get('test', {})
        test = self._convert_expression(test_dict)
        if not test:
            test = ASTConstant(True)
        
        # 转换消息（可能为None）
        msg_dict = node_dict.get('msg')
        msg = None
        if msg_dict is not None:
            msg = self._convert_expression(msg_dict)
        
        return ASTAssert(test, msg)
    
    def _convert_expr_stmt(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """转换表达式语句节点"""
        value_dict = node_dict.get('value', {})
        value = self._convert_expression(value_dict)
        if not value:
            value = ASTConstant(None)
        
        return ASTExpr(value)
    
    def _convert_pass(self, node_dict: Dict[str, Any]) -> ASTPass:
        """转换pass语句节点"""
        return ASTPass()
    
    def _convert_break(self, node_dict: Dict[str, Any]) -> ASTBreak:
        """转换break语句节点"""
        return ASTBreak()
    
    def _convert_continue(self, node_dict: Dict[str, Any]) -> ASTContinue:
        """转换continue语句节点"""
        return ASTContinue()

    def _convert_delete(self, node_dict: Dict[str, Any]) -> ASTDelete:
        """转换delete语句节点"""
        targets = node_dict.get('targets', [])
        converted_targets = []
        for target in targets:
            converted = self._convert_expression(target)
            if converted:
                converted_targets.append(converted)
            else:
                if isinstance(target, dict):
                    target_type = target.get('type', 'Name')
                    if target_type == 'Name':
                        from core.ast_nodes import ASTName
                        converted_targets.append(ASTName(target.get('id', '_')))
                    else:
                        from core.ast_nodes import ASTName
                        converted_targets.append(ASTName('_'))
                else:
                    from core.ast_nodes import ASTName
                    converted_targets.append(ASTName('_'))
        return ASTDelete(converted_targets)

    def _convert_import(self, node_dict: Dict[str, Any]) -> ASTImport:
        """转换import语句节点"""
        names = node_dict.get('names', [])
        # 提取名称列表，支持别名
        if isinstance(names, list):
            name_list = []
            for name_info in names:
                if isinstance(name_info, dict):
                    name = name_info.get('name', '')
                    asname = name_info.get('asname')
                    if asname and asname != name:
                        # 有别名
                        name_list.append(ASTAlias(name, asname))
                    else:
                        name_list.append(name)
                else:
                    name_list.append(str(name_info))
            return ASTImport(name_list)
        else:
            return ASTImport([str(names)])

    def _convert_import_from(self, node_dict: Dict[str, Any]) -> ASTImportFrom:
        """转换from import语句节点"""
        module = node_dict.get('module', '')
        names = node_dict.get('names', [])
        # 提取名称列表，支持别名
        if isinstance(names, list):
            name_list = []
            for name_info in names:
                if isinstance(name_info, dict):
                    name = name_info.get('name', '')
                    asname = name_info.get('asname')
                    if asname and asname != name:
                        # 有别名
                        name_list.append(ASTAlias(name, asname))
                    else:
                        name_list.append(name)
                else:
                    name_list.append(str(name_info))
            return ASTImportFrom(module, name_list)
        else:
            return ASTImportFrom(module, [str(names)])

    def _convert_global(self, node_dict: Dict[str, Any]) -> ASTGlobal:
        """转换global语句节点"""
        names = node_dict.get('names', [])
        if isinstance(names, list):
            return ASTGlobal([str(n) for n in names])
        else:
            return ASTGlobal([str(names)])

    def _convert_nonlocal(self, node_dict: Dict[str, Any]) -> ASTNonlocal:
        """转换nonlocal语句节点"""
        names = node_dict.get('names', [])
        if isinstance(names, list):
            return ASTNonlocal([str(n) for n in names])
        else:
            return ASTNonlocal([str(names)])

    def _convert_block(self, node_dict: Dict[str, Any]) -> ASTBlock:
        """转换代码块节点"""
        return self.convert_body(node_dict.get('statements', []))
    
    def _convert_sequence(self, node_dict: Dict[str, Any]) -> ASTBlock:
        """转换语句序列节点"""
        return self.convert_body(node_dict.get('statements', []))
    
    # ==================== 表达式转换方法 ====================
    
    def _convert_expression(self, expr_dict: Dict[str, Any]) -> Optional[ASTNode]:
        """
        转换表达式节点
        
        这是表达式转换的通用入口，处理所有表达式类型。
        """
        if not expr_dict:
            return None
        
        expr_type = expr_dict.get('type', 'Unknown')
        
        # 根据表达式类型选择转换方法
        converters = {
            'Constant': self._convert_constant_full,
            'Name': self._convert_name_full,
            'BinOp': self._convert_binop_full,
            'UnaryOp': self._convert_unaryop_full,
            'Compare': self._convert_compare_full,
            'Call': self._convert_call_full,
            'Attribute': self._convert_attribute_full,
            'Subscript': self._convert_subscript_full,
            'List': self._convert_list_full,
            'Tuple': self._convert_tuple_full,
            'Dict': self._convert_dict_full,
            'Set': self._convert_set_full,
            'IfExp': self._convert_ifexp_full,  # 条件表达式
            'JoinedStr': self._convert_joined_str_full,  # f-string
            'FormattedValue': self._convert_formatted_value_full,  # 格式化值
            # [关键修复] 添加推导式表达式处理
            'ListComp': self._convert_list_comp_expr,
            'SetComp': self._convert_set_comp_expr,
            'DictComp': self._convert_dict_comp_expr,
            'GeneratorExp': self._convert_generator_exp_expr,
            # [海象运算符] 添加海象运算符表达式处理
            'NamedExpr': self._convert_named_expr_full,
            # [关键修复] 添加逻辑表达式处理
            'BoolOp': self._convert_boolop_full,
            # [异步] 添加 await 表达式处理
            'Await': self._convert_await_expr_full,
            # [关键修复] 添加 lambda 表达式处理
            'Lambda': self._convert_lambda_expr,
            # [关键修复] 添加切片表达式处理
            'Slice': self._convert_slice_full,
            # [关键修复] 添加 Yield 表达式处理
            'Yield': self._convert_yield_expr,
            # [关键修复] 添加 YieldFrom 表达式处理
            'YieldFrom': self._convert_yield_from,
            # [关键修复] 添加 Starred 表达式处理（用于 match/case 中的 *rest）
            'Starred': self._convert_starred_full,
            # [关键修复] 添加 Iter 类型处理（推导式的迭代对象包装）
            'Iter': self._convert_iter_full,
        }
        
        converter = converters.get(expr_type)
        if converter:
            try:
                return converter(expr_dict)
            except Exception as e:
                logger.error(f"Error converting expression {expr_type}: {e}")
                return None
        
        # [关键修复] 处理FunctionObject
        if expr_type in ('FunctionObject', 'AsyncFunctionDef'):
            if expr_type == 'AsyncFunctionDef':
                return self._convert_function_def(expr_dict)
            # 检查是否是lambda函数
            code_value = expr_dict.get('code')
            if code_value:
                import types
                code_obj = None
                if isinstance(code_value, types.CodeType):
                    code_obj = code_value
                elif isinstance(code_value, dict):
                    code_obj = code_value.get('code')
                
                if code_obj and hasattr(code_obj, 'co_name') and code_obj.co_name == '<lambda>':
                    # [关键修复] 将lambda函数的code对象转换为Lambda AST
                    # 使用与_decompile_lambda_function相同的逻辑
                    import dis
                    
                    # 获取lambda函数的参数
                    arg_names = list(code_obj.co_varnames[:code_obj.co_argcount])
                    args = [ASTName(name) for name in arg_names]
                    
                    # 获取lambda函数的字节码指令
                    instructions = list(dis.get_instructions(code_obj))
                    
                    # 提取lambda体（返回值表达式）
                    body_instrs = []
                    for instr in instructions:
                        if instr.opname not in ('COPY_FREE_VARS', 'RESUME', 'RETURN_VALUE'):
                            body_instrs.append(instr)
                    
                    # 使用表达式重建器来解析lambda体
                    if body_instrs:
                        from .ast_generator_v2 import ExpressionReconstructor
                        reconstructor = ExpressionReconstructor()
                        for instr in body_instrs:
                            reconstructor._process_instruction(instr)
                        
                        if reconstructor.stack:
                            body_dict = reconstructor.stack[-1]
                            body = self._convert_expression(body_dict)
                        else:
                            body = ASTConstant(None)
                    else:
                        body = ASTConstant(None)
                    
                    if body:
                        return ASTLambda(args=args, body=body)
            
            func_def = self._convert_function_def({
                'type': 'FunctionDef',
                'name': getattr(code_obj, 'co_name', '<func>') if code_obj else '<func>',
                'code': code_obj,
                'args': {},
                'body': [{'type': 'Pass'}],
            })
            return func_def
        
        # [关键修复] 处理BoolOpPending（逻辑表达式中间状态）
        if expr_type == 'BoolOpPending':
            # BoolOpPending是中间状态，尝试转换为左操作数
            left = expr_dict.get('left')
            if left:
                return self._convert_expression(left)
            return None
        
        # [关键修复] 处理ExceptionInfo（异常信息对象）
        if expr_type == 'ExceptionInfo':
            # ExceptionInfo是中间状态，不生成实际的表达式
            return None
        
        # [关键修复] 处理AugAssign（增强赋值表达式）
        # AugAssign在表达式重建器中被创建，但应该被转换为BinOp
        if expr_type == 'AugAssign':
            return self._convert_augassign_full(expr_dict)
        
        # [Python 3.10+] 模式匹配类型 - 这些不是表达式，应该返回None
        if expr_type in ('MatchValue', 'MatchSequence', 'MatchMapping', 'MatchClass', 'MatchAs', 'MatchOr', 'MatchStar', 'MatchStarred', 'MatchKeys'):
            return None
        
        # [关键修复] 处理PUSH_NULL - Python 3.11+的null值标记，用于函数调用
        if expr_type == 'Assign':
            value = expr_dict.get('value', {})
            if value:
                return self._convert_expression(value)
            return ASTConstant(None)
        
        if expr_type == 'PUSH_NULL':
            return None
        
        logger.warning(f"Unknown expression type: {expr_type}")
        return self._convert_constant_full(expr_dict)
    
    def _convert_constant_full(self, expr_dict: Dict[str, Any]) -> ASTConstant:
        """完整转换常量表达式"""
        value = expr_dict.get('value')
        return ASTConstant(value)
    
    def _convert_name_full(self, expr_dict: Dict[str, Any]) -> ASTName:
        """完整转换名称表达式"""
        name_id = expr_dict.get('id', '<unknown>')
        return ASTName(name_id)
    
    def _convert_binop_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTBinary]:
        """完整转换二元操作表达式"""
        left = self._convert_expression(expr_dict.get('left', {}))
        right = self._convert_expression(expr_dict.get('right', {}))
        op_str = expr_dict.get('op', '+')
        
        # 映射操作符字符串到ASTBinary.BinOp
        op_map = {
            '+': ASTBinary.BinOp.BIN_ADD,
            '-': ASTBinary.BinOp.BIN_SUBTRACT,
            '*': ASTBinary.BinOp.BIN_MULTIPLY,
            '/': ASTBinary.BinOp.BIN_DIVIDE,
            '//': ASTBinary.BinOp.BIN_FLOOR_DIVIDE,
            '%': ASTBinary.BinOp.BIN_MODULO,
            '**': ASTBinary.BinOp.BIN_POWER,
            '<<': ASTBinary.BinOp.BIN_LSHIFT,
            '>>': ASTBinary.BinOp.BIN_RSHIFT,
            '&': ASTBinary.BinOp.BIN_AND,
            '|': ASTBinary.BinOp.BIN_OR,
            '^': ASTBinary.BinOp.BIN_XOR,
            '@': ASTBinary.BinOp.BIN_MAT_MULTIPLY,  # Python 3.5+ 矩阵乘法
        }
        
        op = op_map.get(op_str, ASTBinary.BinOp.BIN_ADD)

        if left and right:
            return ASTBinary(left, right, op)
        return left or right
    
    def _convert_augassign_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTBinary]:
        """[关键修复] 完整转换增强赋值表达式（AugAssign）
        
        AugAssign在表达式重建器中被创建（如 x += 1），
        但它实际上是一个二元操作，应该被转换为ASTBinary。
        注意：真正的增强赋值语句（如 x += 1）应该在语句级别处理。
        """
        target = self._convert_expression(expr_dict.get('target', {}))
        value = self._convert_expression(expr_dict.get('value', {}))
        op_str = expr_dict.get('op', '+=')
        
        # 将增强赋值操作符转换为普通二元操作符
        # 例如：+= -> +, -= -> -, *= -> *, 等等
        op_map = {
            '+=': ASTBinary.BinOp.BIN_ADD,
            '-=': ASTBinary.BinOp.BIN_SUBTRACT,
            '*=': ASTBinary.BinOp.BIN_MULTIPLY,
            '/=': ASTBinary.BinOp.BIN_DIVIDE,
            '//=': ASTBinary.BinOp.BIN_FLOOR_DIVIDE,
            '%=': ASTBinary.BinOp.BIN_MODULO,
            '**=': ASTBinary.BinOp.BIN_POWER,
            '<<=': ASTBinary.BinOp.BIN_LSHIFT,
            '>>=': ASTBinary.BinOp.BIN_RSHIFT,
            '&=': ASTBinary.BinOp.BIN_AND,
            '|=': ASTBinary.BinOp.BIN_OR,
            '^=': ASTBinary.BinOp.BIN_XOR,
            '@=': ASTBinary.BinOp.BIN_MAT_MULTIPLY,
        }
        
        op = op_map.get(op_str, ASTBinary.BinOp.BIN_ADD)
        
        if target and value:
            return ASTBinary(target, value, op)
        return target or value
    
    def _convert_unaryop_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTUnary]:
        """完整转换一元操作表达式"""
        operand = self._convert_expression(expr_dict.get('operand', {}))
        op_str = expr_dict.get('op', '+')
        
        # [关键修复] ASTUnary使用的是UnOp而不是UnaryOp
        op_map = {
            '+': ASTUnary.UnOp.UN_POSITIVE,
            '-': ASTUnary.UnOp.UN_NEGATIVE,
            'not': ASTUnary.UnOp.UN_NOT,
            '~': ASTUnary.UnOp.UN_INVERT,
        }
        
        op = op_map.get(op_str, ASTUnary.UnOp.UN_POSITIVE)

        if operand:
            return ASTUnary(operand, op)
        return None

    def _convert_boolop_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTBinary]:
        """完整转换逻辑表达式 (and/or)"""
        values = expr_dict.get('values', [])
        if len(values) < 2:
            # 只有一个值，直接转换
            return self._convert_expression(values[0]) if values else None

        op_str = expr_dict.get('op', 'and')
        # [关键修复] 支持大小写不同的op值（如"Or"和"or"）
        op_str_lower = op_str.lower()
        # 映射操作符字符串到ASTBinary.BinOp
        op_map = {
            'and': ASTBinary.BinOp.BIN_LOG_AND,
            'or': ASTBinary.BinOp.BIN_LOG_OR,
        }
        op = op_map.get(op_str_lower, ASTBinary.BinOp.BIN_LOG_AND)

        # 递归构建二元操作树
        # (a and b and c) -> ((a and b) and c)
        left = self._convert_expression(values[0])
        for i in range(1, len(values)):
            right = self._convert_expression(values[i])
            if left and right:
                left = ASTBinary(left, right, op)
            elif right:
                left = right
        return left

    def _convert_compare_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTCompare]:
        """完整转换比较表达式"""
        left = self._convert_expression(expr_dict.get('left', {}))
        
        # [修复-E3] 支持两种格式:
        # 1. 标准AST格式: comparators=[...] (多个比较)
        # 2. 简化格式: right={...} (单个比较，用于guard表达式)
        comparators = [
            self._convert_expression(c) for c in expr_dict.get('comparators', [])
        ]
        if not comparators and 'right' in expr_dict:
            # 使用right字段作为唯一的comparator
            right = self._convert_expression(expr_dict.get('right', {}))
            if right:
                comparators = [right]
        
        ops = expr_dict.get('ops', ['=='])
        
        # [修复-E3] 处理ops的两种格式:
        # 1. 字符串列表: ['==', '!=']
        # 2. 对象列表: [{'type': 'CompareOp', 'op': '=='}]
        if ops and isinstance(ops, list) and len(ops) > 0 and isinstance(ops[0], dict):
            ops = [op.get('op', '==') if isinstance(op, dict) else op for op in ops]
        
        # [关键修复] 将字符串操作符转换为整数
        op_map = {
            '<': 0,   # CMP_LESS
            '<=': 1,  # CMP_LESS_EQUAL
            '==': 2,  # CMP_EQUAL
            '!=': 3,  # CMP_NOT_EQUAL
            '>': 4,   # CMP_GREATER
            '>=': 5,  # CMP_GREATER_EQUAL
            'in': 6,  # CMP_IN
            'not in': 7,  # CMP_NOT_IN
            'is': 8,  # CMP_IS
            'is not': 9,  # CMP_IS_NOT
        }
        int_ops = [op_map.get(op, 2) for op in ops]  # 默认使用 ==

        if left and comparators:
            # ASTCompare.__init__ 参数顺序是 (left, comparators, ops)
            return ASTCompare(left, comparators, int_ops)
        return left
    
    def _convert_call_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTCall]:
        """完整转换函数调用表达式"""
        func = self._convert_expression(expr_dict.get('func', {}))
        
        # [关键修复] 处理参数，包括Starred（*args）和普通参数
        args = []
        var_arg = None  # *args
        kw_arg = None   # **kwargs
        
        for a in expr_dict.get('args', []):
            if isinstance(a, dict):
                if a.get('type') == 'Starred':
                    # *args 参数
                    var_arg = self._convert_expression(a.get('value', {}))
                else:
                    arg = self._convert_expression(a)
                    if arg:
                        args.append(arg)
        
        # [关键修复] 处理关键字参数，包括KeywordStarred（**kwargs）
        kwparams = []
        kwargs = expr_dict.get('kwargs', []) or expr_dict.get('keywords', [])
        if kwargs:
            for kw in kwargs:
                if isinstance(kw, dict):
                    if kw.get('type') == 'keyword':
                        kw_value = self._convert_expression(kw.get('value', {}))
                        if kw_value:
                            from core.ast_nodes import ASTKeyword
                            kwparams.append(ASTKeyword(name=kw.get('arg'), value=kw_value))
                    elif kw.get('type') == 'KeywordStarred':
                        # **kwargs 参数
                        kw_arg = self._convert_expression(kw.get('value', {}))
        
        if func:
            return ASTCall(func, pparams=args, kwparams=kwparams, var=var_arg, kw=kw_arg)
        return None
    
    def _convert_attribute_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTAttribute]:
        """完整转换属性访问表达式"""
        value = self._convert_expression(expr_dict.get('value', {}))
        attr = expr_dict.get('attr', '<attr>')
        
        if value:
            # [关键修复] ASTAttribute需要ctx参数
            from core.ast_nodes import NodeType
            ctx = expr_dict.get('ctx', 1)  # 1 = Load context
            return ASTAttribute(value, attr, ctx)
        return None
    
    def _convert_subscript_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTSubscript]:
        """完整转换下标访问表达式"""
        value = self._convert_expression(expr_dict.get('value', {}))
        slice_val = self._convert_expression(expr_dict.get('slice', {}))
        
        if value and slice_val:
            return ASTSubscript(value, slice_val)
        return value
    
    def _convert_list_full(self, expr_dict: Dict[str, Any]) -> ASTList:
        """完整转换列表表达式"""
        elts = [
            self._convert_expression(e) for e in expr_dict.get('elts', [])
        ]
        elts = [e for e in elts if e is not None]
        return ASTList(elts)
    
    def _convert_tuple_full(self, expr_dict: Dict[str, Any]) -> ASTTuple:
        """完整转换元组表达式"""
        elts = [
            self._convert_expression(e) for e in expr_dict.get('elts', [])
        ]
        elts = [e for e in elts if e is not None]
        return ASTTuple(elts)
    
    def _convert_dict_full(self, expr_dict: Dict[str, Any]) -> ASTDict:
        """完整转换字典表达式"""
        keys = [
            self._convert_expression(k) for k in expr_dict.get('keys', [])
        ]
        keys = [k for k in keys if k is not None]
        
        values = [
            self._convert_expression(v) for v in expr_dict.get('values', [])
        ]
        values = [v for v in values if v is not None]
        
        return ASTDict(keys, values)
    
    def _convert_set_full(self, expr_dict: Dict[str, Any]) -> ASTSet:
        """完整转换集合表达式"""
        elts = [
            self._convert_expression(e) for e in expr_dict.get('elts', [])
        ]
        elts = [e for e in elts if e is not None]
        return ASTSet(elts)
    
    def _convert_ifexp_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTNode]:
        """完整转换条件表达式（x if cond else y）"""
        # [关键修复] 创建ASTIfExp节点
        test = self._convert_expression(expr_dict.get('test', {}))
        body = self._convert_expression(expr_dict.get('body', {}))
        orelse = self._convert_expression(expr_dict.get('orelse', {}))
        
        # [关键修复] 创建ASTIfExp节点
        if test and body and orelse:
            return ASTIfExp(test=test, body=body, orelse=orelse)
        
        # 如果转换失败，返回body或orelse或None
        return body or orelse or ASTConstant(None)
    
    def _convert_joined_str_full(self, expr_dict: Dict[str, Any]) -> ASTJoinedStr:
        """完整转换f-string表达式"""
        values = []
        for val_dict in expr_dict.get('values', []):
            val_type = val_dict.get('type', '')
            # [关键修复] 跳过PUSH_NULL标记
            if val_type == 'PUSH_NULL':
                continue
            if val_type == 'FormattedValue':
                # 特殊处理FormattedValue
                val = self._convert_formatted_value_full(val_dict)
            else:
                val = self._convert_expression(val_dict)
            if val:
                values.append(val)
        
        joined_str = ASTJoinedStr()
        joined_str._values = values
        return joined_str
    
    def _convert_formatted_value_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTFormattedValue]:
        """完整转换格式化值表达式"""
        value = self._convert_expression(expr_dict.get('value', {}))
        if not value:
            return None
        
        # [关键修复] 处理conversion，可能是字符串('s', 'r', 'a')或整数(0, 1, 2, 3)
        conversion_val = expr_dict.get('conversion')
        conversion = 0
        if isinstance(conversion_val, int):
            # 已经是整数
            conversion = conversion_val
        elif isinstance(conversion_val, str):
            # 字符串格式：'s', 'r', 'a' 或 '!s', '!r', '!a'
            if conversion_val in ('s', '!s'):
                conversion = 1
            elif conversion_val in ('r', '!r'):
                conversion = 2
            elif conversion_val in ('a', '!a'):
                conversion = 3
        
        format_spec = None
        if expr_dict.get('format_spec'):
            format_spec = self._convert_expression(expr_dict.get('format_spec'))
        
        return ASTFormattedValue(value=value, conversion=conversion, format_spec=format_spec)
    
    # ==================== 辅助转换方法 ====================
    
    def _convert_except_handler(self, handler_dict: Dict[str, Any]) -> Optional[ASTExceptHandler]:
        """转换except handler"""
        # 转换异常类型
        exc_type_dict = handler_dict.get('exc_type')
        if exc_type_dict:
            if isinstance(exc_type_dict, dict):
                type_node = self._convert_expression(exc_type_dict)
            else:
                # 如果exc_type不是字典，使用默认值
                type_node = ASTName('Exception')
        else:
            # [关键修复] 如果exc_type为None，表示空的except:（捕获所有异常）
            type_node = None
        
        # 转换异常名称（as name）
        name = handler_dict.get('name')
        
        # 转换handler体
        body = self.convert_body(handler_dict.get('body', []))
        
        # [关键修复] ASTExceptHandler的异常类型参数是exc_type，不是type
        handler = ASTExceptHandler(exc_type=type_node, name=name, body=body)
        
        # [关键修复] 传递 except* 标记
        is_except_star = handler_dict.get('is_except_star', False)
        if is_except_star:
            handler.is_except_star = True
        
        return handler
    
    def _convert_with_item(self, item_dict: Dict[str, Any]) -> Optional[ASTWithItem]:
        """转换with item（context_expr as optional_vars）"""
        # 转换上下文表达式
        context_expr = self._convert_expression(item_dict.get('context_expr', {}))
        if not context_expr:
            return None
        
        # 转换可选变量
        optional_vars = None
        optional_vars_dict = item_dict.get('optional_vars')
        if optional_vars_dict:
            optional_vars = self._convert_expression(optional_vars_dict)
        
        # [关键修复] ASTWithItem需要在构造函数中传入参数
        return ASTWithItem(context_expr, optional_vars)
    
    def _convert_arguments(self, args_dict: Dict[str, Any]) -> Any:
        """转换函数参数"""
        # [关键修复] 确保返回包含 vararg 和 kwarg 的字典
        if isinstance(args_dict, dict):
            result = {
                'args': args_dict.get('args', []),
                'vararg': None,
                'kwarg': None,
                # [关键修复] 传递默认值信息
                'defaults': args_dict.get('defaults', []),
                'kwonlyargs': args_dict.get('kwonlyargs', []),
                'kw_defaults': args_dict.get('kw_defaults', [])
            }
            
            # 处理 vararg
            if args_dict.get('vararg'):
                vararg = args_dict['vararg']
                if isinstance(vararg, dict):
                    result['vararg'] = vararg.get('arg')
                elif isinstance(vararg, str):
                    result['vararg'] = vararg
                elif hasattr(vararg, 'arg'):
                    result['vararg'] = vararg.arg
            
            # 处理 kwarg
            if args_dict.get('kwarg'):
                kwarg = args_dict['kwarg']
                if isinstance(kwarg, dict):
                    result['kwarg'] = kwarg.get('arg')
                elif isinstance(kwarg, str):
                    result['kwarg'] = kwarg
                elif hasattr(kwarg, 'arg'):
                    result['kwarg'] = kwarg.arg
            
            return result
        
        return args_dict
    
    # ==================== 快捷转换方法（用于表达式作为语句） ====================
    
    def _convert_constant_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将常量表达式作为语句"""
        return ASTExpr(self._convert_constant_full(node_dict))
    
    def _convert_name_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将名称表达式作为语句"""
        return ASTExpr(self._convert_name_full(node_dict))
    
    def _convert_binop_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将二元操作表达式作为语句"""
        expr = self._convert_binop_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_unaryop_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将一元操作表达式作为语句"""
        expr = self._convert_unaryop_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_compare_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将比较表达式作为语句"""
        expr = self._convert_compare_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_call_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将调用表达式作为语句"""
        expr = self._convert_call_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_attribute_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将属性访问表达式作为语句"""
        expr = self._convert_attribute_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_subscript_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将下标访问表达式作为语句"""
        expr = self._convert_subscript_full(node_dict)
        return ASTExpr(expr) if expr else ASTExpr(ASTConstant(None))
    
    def _convert_list_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将列表表达式作为语句"""
        return ASTExpr(self._convert_list_full(node_dict))
    
    def _convert_tuple_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将元组表达式作为语句"""
        return ASTExpr(self._convert_tuple_full(node_dict))
    
    def _convert_dict_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将字典表达式作为语句"""
        return ASTExpr(self._convert_dict_full(node_dict))
    
    def _convert_set_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将集合表达式作为语句"""
        return ASTExpr(self._convert_set_full(node_dict))

    def _convert_named_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """将海象运算符表达式作为语句"""
        target = self._convert_expression(node_dict.get('target'))
        value = self._convert_expression(node_dict.get('value'))
        return ASTExpr(ASTNamedExpr(target=target, value=value))

    def _convert_named_expr_full(self, expr_dict: Dict[str, Any]) -> ASTNamedExpr:
        """完整转换海象运算符表达式"""
        target = self._convert_expression(expr_dict.get('target'))
        value = self._convert_expression(expr_dict.get('value'))
        return ASTNamedExpr(target=target, value=value)
    
    def _convert_await_expr(self, node_dict: Dict[str, Any]) -> ASTExpr:
        """转换 await 表达式作为语句"""
        value = self._convert_expression(node_dict.get('value'))
        return ASTExpr(ASTAwaitable(value=value))
    
    def _convert_await_expr_full(self, expr_dict: Dict[str, Any]) -> ASTAwaitable:
        """完整转换 await 表达式"""
        value = self._convert_expression(expr_dict.get('value'))
        return ASTAwaitable(value=value)

    def _convert_raise_expr(self, node_dict: Dict[str, Any]) -> Optional[ASTNode]:
        value = node_dict.get('exc') or node_dict.get('value')
        cause = node_dict.get('cause')
        converted_cause = self.convert(cause) if cause else None
        if value:
            converted_value = self.convert(value)
            if converted_value:
                return ASTRaise(exc=converted_value, cause=converted_cause)
        else:
            return ASTRaise(exc=None)
        return None

    # ==================== 推导式转换方法 ====================

    def _convert_list_comp_expr(self, node_dict: Dict[str, Any]) -> ASTListComp:
        """转换列表推导式表达式"""
        elt = self._convert_expression(node_dict.get('elt'))
        generators = self._convert_comprehensions(node_dict.get('generators', []))
        return ASTListComp(elt=elt, generators=generators)

    def _convert_set_comp_expr(self, node_dict: Dict[str, Any]) -> ASTSetComp:
        """转换集合推导式表达式"""
        elt = self._convert_expression(node_dict.get('elt'))
        generators = self._convert_comprehensions(node_dict.get('generators', []))
        return ASTSetComp(elt=elt, generators=generators)

    def _convert_dict_comp_expr(self, node_dict: Dict[str, Any]) -> ASTDictComp:
        """转换字典推导式表达式"""
        key = self._convert_expression(node_dict.get('key'))
        value = self._convert_expression(node_dict.get('value'))
        generators = self._convert_comprehensions(node_dict.get('generators', []))
        return ASTDictComp(key=key, value=value, generators=generators)

    def _convert_generator_exp_expr(self, node_dict: Dict[str, Any]):
        """转换生成器表达式"""
        # [关键修复] 生成器表达式应该用ASTGenExpr，不是ASTListComp
        elt = self._convert_expression(node_dict.get('elt'))
        generators = self._convert_comprehensions(node_dict.get('generators', []))
        return ASTGenExpr(elt=elt, generators=generators)

    def _convert_lambda_expr(self, node_dict: Dict[str, Any]):
        """转换lambda表达式"""
        # [关键修复] 转换lambda参数
        args_dict = node_dict.get('args', {})
        args = []
        if isinstance(args_dict, dict):
            args_list = args_dict.get('args', [])
            for arg in args_list:
                if isinstance(arg, dict):
                    # [关键修复] 支持两种格式：{'arg': 'name'} 或 {'type': 'Name', 'id': 'name'}
                    arg_name = arg.get('arg')
                    if arg_name is None:
                        arg_name = arg.get('id', '<arg>')
                    args.append(ASTName(arg_name))
                elif isinstance(arg, str):
                    args.append(ASTName(arg))
                elif hasattr(arg, 'arg'):
                    args.append(ASTName(arg.arg))
        
        # [关键修复] 转换lambda体
        body = self._convert_expression(node_dict.get('body', {}))
        if not body:
            body = ASTConstant(None)
        
        # [关键修复] 创建ASTLambda节点
        return ASTLambda(args=args, body=body)

    # ==================== Match/Case 转换方法 ====================

    def _convert_match(self, node_dict: Dict[str, Any]) -> Optional[ASTMatch]:
        """[Python 3.10+] 转换match语句"""
        # 转换主题表达式
        subject = self._convert_expression(node_dict.get('subject', {}))
        if not subject:
            subject = ASTName('_')
        
        # 转换所有case
        cases = []
        for case_dict in node_dict.get('cases', []):
            case = self._convert_case(case_dict)
            if case:
                cases.append(case)
        
        return ASTMatch(subject=subject, cases=cases)

    def _convert_case(self, node_dict: Dict[str, Any]) -> Optional[ASTCase]:
        """[Python 3.10+] 转换case语句"""
        # 转换模式
        pattern = self._convert_match_pattern(node_dict.get('pattern', {}))
        
        # 转换guard（if条件）
        guard = None
        guard_dict = node_dict.get('guard')
        if guard_dict:
            guard = self._convert_expression(guard_dict)
        
        # 转换body
        body_nodes = []
        body_list = node_dict.get('body', [])
        if isinstance(body_list, list):
            for stmt_dict in body_list:
                stmt = self.convert(stmt_dict)
                if stmt:
                    body_nodes.append(stmt)
        elif isinstance(body_list, dict):
            stmt = self.convert(body_list)
            if stmt:
                body_nodes.append(stmt)
        
        body = ASTBlock(nodes=body_nodes)
        return ASTCase(pattern=pattern, body=body, guard=guard)

    def _convert_match_pattern(self, pattern_dict: Dict[str, Any]) -> Any:
        """[Python 3.10+] 转换匹配模式"""
        if not pattern_dict:
            return ASTName('_')
        
        # 如果已经是AST节点，直接返回
        if hasattr(pattern_dict, 'to_code'):
            return pattern_dict
        
        pattern_type = pattern_dict.get('type', '')
        
        if pattern_type == 'MatchValue':
            value = self._convert_expression(pattern_dict.get('value', {}))
            return value if value else ASTName('_')
        
        elif pattern_type == 'MatchSequence':
            patterns = pattern_dict.get('patterns', [])
            as_name = pattern_dict.get('as_name')  # [关键修复-2026] 保留AS binding
            
            # [关键修复-2026] 转换子模式但保留MatchSequence结构
            # 这样code_generator可以正确生成 (pattern1, pattern2) as name
            converted_patterns = []
            for p in patterns:
                converted = self._convert_match_pattern(p)
                converted_patterns.append(converted)
            
            # 返回字典而非ASTList，以保留AS binding和正确的括号
            return {
                'type': 'MatchSequence',
                'patterns': converted_patterns,
                'as_name': as_name
            }
        
        elif pattern_type == 'MatchMapping':
            keys = []
            values = []
            for k, v in zip(pattern_dict.get('keys', []), pattern_dict.get('patterns', [])):
                key_node = self._convert_expression(k) if isinstance(k, dict) else ASTName(str(k))
                val_node = self._convert_match_pattern(v)
                if key_node and val_node:
                    keys.append(key_node)
                    values.append(val_node)
            return ASTDict(keys=keys, values=values)
        
        elif pattern_type == 'MatchClass':
            cls = self._convert_expression(pattern_dict.get('cls', {}))
            patterns = [self._convert_match_pattern(p) for p in pattern_dict.get('patterns', [])]
            # [修复-2026] 保留as_name绑定
            as_name = pattern_dict.get('as_name')
            # [Phase 3 adv16_match_class_nested_in_if] 保留 keyword_keys
            # code_generator 依据 keyword_keys 区分位置参数与关键字参数
            # （pos_count = len(patterns) - len(keyword_keys)）。此前丢失
            # keyword_keys 导致所有 pattern 被当作位置参数，输出
            # Outer(Inner(1)) 而非 Outer(x=Inner(1))。
            keyword_keys = pattern_dict.get('keyword_keys', [])

            result = {'type': 'MatchClass', 'cls': cls, 'patterns': patterns}
            if keyword_keys:
                result['keyword_keys'] = keyword_keys
            if as_name:
                result['as_name'] = as_name
            return result
        
        elif pattern_type == 'MatchAs':
            name = pattern_dict.get('name', '_')
            value = pattern_dict.get('value') or pattern_dict.get('pattern')
            if value:
                value_pattern = self._convert_match_pattern(value)
                return {'type': 'MatchAs', 'pattern': value_pattern, 'name': name}
            return ASTName(name)
        
        elif pattern_type == 'MatchOr':
            # [关键修复-2026] 支持多值OR模式 (case 0 | 1 | 2:)
            # 新格式: {'type': 'MatchOr', 'patterns': [...]}  (多个值)
            # 旧格式: {'type': 'MatchOr', 'left': ..., 'right': ...}  (两个值，兼容)
            patterns = pattern_dict.get('patterns', [])
            
            if len(patterns) >= 2:
                # 新格式：多值OR模式，递归构建 BinOp 链
                converted_patterns = [self._convert_match_pattern(p) for p in patterns]

                # 用 BIN_OR 连接所有模式: 0 | 1 | 2
                # [注意] MatchOr使用按位或操作符 |
                result = converted_patterns[0]
                for i in range(1, len(converted_patterns)):
                    result = ASTBinary(
                        left=result,
                        right=converted_patterns[i],
                        op=ASTBinary.BinOp.BIN_OR  # 使用 BIN_OR 而不是不存在的 BIN_BIT_OR
                    )
                return result
            else:
                # 旧格式兼容：left/right 结构
                left = self._convert_match_pattern(pattern_dict.get('left', {}))
                right = self._convert_match_pattern(pattern_dict.get('right', {}))
                return ASTBinary(left=left, right=right, op=ASTBinary.BinOp.BIN_OR)
        
        elif pattern_type == 'MatchStar':
            name = pattern_dict.get('name', '_')
            return {'type': 'MatchStar', 'name': name}
        
        elif pattern_type == 'MatchStarred':
            # [新增-2026] 支持扩展解包 *rest
            inner_pattern = pattern_dict.get('pattern', {})
            inner_node = self._convert_match_pattern(inner_pattern)
            # 返回字典形式，由code_generator处理
            return {'type': 'MatchStarred', 'pattern': inner_node}
        
        elif pattern_type == 'MatchKeys':
            return ASTName('_')
        
        # 默认处理：作为表达式转换
        return self._convert_expression(pattern_dict)

    def _convert_slice_full(self, expr_dict: Dict[str, Any]) -> Optional[ASTSlice]:
        """完整转换切片表达式"""
        lower = self._convert_expression(expr_dict.get('lower'))
        upper = self._convert_expression(expr_dict.get('upper'))
        step = self._convert_expression(expr_dict.get('step'))
        return ASTSlice(lower, upper, step)

    def _convert_comprehensions(self, generators_list: List[Dict[str, Any]]) -> List[ASTComprehension]:
        """转换推导式生成器列表"""
        result = []
        for gen_dict in generators_list:
            if gen_dict.get('type') == 'comprehension':
                target = self._convert_expression(gen_dict.get('target'))
                iter_expr = self._convert_expression(gen_dict.get('iter'))
                ifs = [self._convert_expression(if_clause) for if_clause in gen_dict.get('ifs', [])]
                is_async = gen_dict.get('is_async', 0)
                # [关键修复] ASTComprehension的参数是iter_node，不是iter
                result.append(ASTComprehension(target=target, iter_node=iter_expr, ifs=ifs, is_async=is_async))
        return result


# ==================== 便捷函数 ====================

def convert_cfg_ast(node_dict: Dict[str, Any], verbose: bool = False) -> Optional[ASTNode]:
    """
    便捷函数：将CFG AST字典转换为项目AST节点
    
    Args:
        node_dict: CFG生成的AST字典
        verbose: 是否输出详细信息
        
    Returns:
        转换后的ASTNode对象
    """
    converter = CFGASTConverter(verbose=verbose)
    return converter.convert(node_dict)


def convert_cfg_body(body_list: List[Dict[str, Any]], verbose: bool = False) -> ASTBlock:
    """
    便捷函数：将CFG AST语句列表转换为代码块
    
    Args:
        body_list: CFG AST字典列表
        verbose: 是否输出详细信息
        
    Returns:
        包含所有转换后节点的ASTBlock
    """
    converter = CFGASTConverter(verbose=verbose)
    return converter.convert_body(body_list)
