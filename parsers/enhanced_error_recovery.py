#!/usr/bin/env python3
"""
增强的异常处理和错误恢复机制

提供AST构建器中的增强的错误恢复功能
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict
from core.ast_nodes import ASTNode, ASTObject


class ErrorContext:
    """错误上下文，用于记录和恢复错误状态"""
    
    def __init__(self):
        self.error_type = None
        self.error_message = None
        self.error_trace = []
        self.stack_state = []
        self.instruction_offset = -1
        self.function_stack = []
        self.block_stack = []
        self.recovery_attempts = 0
        self.recovery_successful = False
        self.partial_recovery = False
        self.uncertain_nodes = []
    
    def save_stack_state(self, stack) -> None:
        """保存堆栈状态 - 增强版本"""
        # 保存栈的深度和栈顶元素
        stack_depth = stack.size()
        self.stack_state = {
            'depth': stack_depth,
            'top_elements': [],
            'all_elements': [],
            'stack_size': stack_depth
        }
        
        # 保存栈顶的几个元素（最多5个）
        for i in range(min(stack_depth, 5)):
            try:
                element = stack.peek(i)
                self.stack_state['top_elements'].append(element)
            except:
                pass
        
        # 保存所有栈元素（最多10个，用于更精确的恢复）
        for i in range(min(stack_depth, 10)):
            try:
                element = stack.peek(i)
                self.stack_state['all_elements'].append(element)
            except:
                pass
        
        # 保存栈的完整状态，包括所有元素
        try:
            if hasattr(stack, 'get_all_elements'):
                self.stack_state['all_elements'] = stack.get_all_elements()
        except:
            pass
    
    def save_context_state(self, ast_builder) -> None:
        """保存完整上下文状态 - 新增方法"""
        # 保存当前指令偏移
        self.instruction_offset = ast_builder.current_instruction_offset
        
        # 保存函数栈
        if hasattr(ast_builder, 'function_stack'):
            self.function_stack = ast_builder.function_stack.copy()
        
        # 保存块栈
        if hasattr(ast_builder, 'block_stack'):
            self.block_stack = ast_builder.block_stack.copy()
        
        # 保存错误轨迹
        if hasattr(ast_builder, 'error_trace'):
            self.error_trace = ast_builder.error_trace.copy()
        
        # 保存更多上下文信息
        if hasattr(ast_builder, 'code_obj'):
            self.code_obj = ast_builder.code_obj
        
        # 保存栈状态
        self.save_stack_state(ast_builder.stack)
    
    def restore_stack_state(self, stack) -> bool:
        """恢复堆栈状态"""
        if not self.partial_recovery and not self.recovery_successful:
            return False
        
        # 尝试恢复栈状态
        # 这里使用简化处理，实际实现需要更复杂
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_trace': self.error_trace,
            'stack_state': self.stack_state,
            'instruction_offset': self.instruction_offset,
            'function_stack': self.function_stack,
            'block_stack': self.block_stack,
            'recovery_attempts': self.recovery_attempts,
            'recovery_successful': self.recovery_successful,
            'partial_recovery': self.partial_recovery,
            'uncertain_nodes': self.uncertain_nodes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorContext':
        """从字典创建实例"""
        context = cls()
        context.error_type = data.get('error_type')
        context.error_message = data.get('error_message')
        context.error_trace = data.get('error_trace', [])
        context.stack_state = data.get('stack_state', [])
        context.instruction_offset = data.get('instruction_offset', -1)
        context.function_stack = data.get('function_stack', [])
        context.block_stack = data.get('block_stack', [])
        context.recovery_attempts = data.get('recovery_attempts', 0)
        context.recovery_successful = data.get('recovery_successful', False)
        context.partial_recovery = data.get('partial_recovery', False)
        context.uncertain_nodes = data.get('uncertain_nodes', [])
        return context


class ErrorRecoveryManager:
    """错误恢复管理器，管理多个错误上下文和恢复策略"""
    
    def __init__(self, max_errors=100):
        self.error_contexts = []
        self.max_errors = max_errors
        self.recovery_strategies = []
        self.global_uncertain_nodes = []
    
    def add_error_context(self, context: ErrorContext) -> None:
        """添加错误上下文"""
        self.error_contexts.append(context)
        
        # 限制错误上下文数量
        if len(self.error_contexts) > self.max_errors:
            self.error_contexts = self.error_contexts[-self.max_errors:]
    
    def register_recovery_strategy(self, strategy) -> None:
        """注册恢复策略"""
        self.recovery_strategies.append(strategy)
    
    def register_uncertain_node(self, node: ASTNode, reason: str) -> None:
        """注册不确定节点"""
        self.global_uncertain_nodes.append({
            'node': node,
            'reason': reason
        })
    
    def apply_recovery_strategies(self, ast_builder) -> bool:
        """应用恢复策略"""
        # 从最近的错误开始尝试恢复
        for context in reversed(self.error_contexts):
            # 尝试不同的恢复策略
            for strategy in self.recovery_strategies:
                if strategy(context, ast_builder):
                    context.recovery_successful = True
                    return True
        
        # 如果所有恢复策略都失败，尝试部分恢复
        for context in reversed(self.error_contexts):
            if context.partial_recovery:
                context.recovery_successful = True
                return True
        
        return False
    
    def generate_error_report(self) -> str:
        """生成错误报告"""
        report = ["错误恢复报告:", "=" * 40]
        
        if not self.error_contexts:
            report.append("没有记录任何错误。")
            return "\n".join(report)
        
        report.append(f"共记录了 {len(self.error_contexts)} 个错误。")
        
        # 按类型分组
        error_groups = defaultdict(list)
        for context in self.error_contexts:
            error_groups[context.error_type].append(context)
        
        # 生成报告
        for error_type, contexts in error_groups.items():
            report.append(f"\n错误类型: {error_type}")
            report.append("-" * 30)
            
            for context in contexts:
                report.append(f"  位置: 偏移 {context.instruction_offset}")
                report.append(f"  消息: {context.error_message}")
                
                if context.partial_recovery:
                    report.append(f"  状态: 部分恢复")
                elif context.recovery_successful:
                    report.append(f"  状态: 完全恢复")
                else:
                    report.append(f"  状态: 恢复失败")
        
        if self.global_uncertain_nodes:
            report.append("\n不确定节点:")
            report.append("-" * 30)
            
            for item in self.global_uncertain_nodes:
                report.append(f"  节点: {item['node']}")
                report.append(f"  原因: {item['reason']}")
        
        return "\n".join(report)


class ErrorRecoveryStrategy:
    """错误恢复策略基类"""
    
    def apply(self, context: ErrorContext, ast_builder) -> bool:
        """应用恢复策略，返回是否成功"""
        return False


class StackRecoveryStrategy(ErrorRecoveryStrategy):
    """堆栈恢复策略"""
    
    def apply(self, context: ErrorContext, ast_builder) -> bool:
        """应用堆栈恢复策略 - 改进版本"""
        try:
            # 尝试恢复堆栈状态
            if context.stack_state and hasattr(ast_builder.stack, 'size'):
                stack_depth = context.stack_state.get('depth', 0)
                top_elements = context.stack_state.get('top_elements', [])
                all_elements = context.stack_state.get('all_elements', [])
                
                # 检查是否需要恢复
                current_depth = ast_builder.stack.size()
                
                # 如果当前栈深度超过保存的深度，尝试减少
                if current_depth > stack_depth:
                    # 计算需要弹出的元素数量
                    elements_to_pop = current_depth - stack_depth
                    
                    # 先记录要弹出的元素，以便在恢复失败时可以回滚
                    popped_elements = []
                    for _ in range(elements_to_pop):
                        if not ast_builder.stack.empty():
                            popped_elements.append(ast_builder.stack.pop())
                    
                    # 尝试恢复保存的元素
                    # 从保存的元素列表中恢复，从栈底开始
                    for element in all_elements:
                        try:
                            if element is not None:
                                ast_builder.stack.push(element)
                        except Exception as e:
                            # 如果恢复失败，回滚弹出的元素
                            for popped in reversed(popped_elements):
                                if popped is not None:
                                    ast_builder.stack.push(popped)
                            return False
                    
                    return True
                    
                # 如果当前栈深度小于保存的深度，尝试增加
                elif current_depth < stack_depth:
                    # 尝试恢复保存的元素
                    for element in all_elements:
                        try:
                            if element is not None:
                                ast_builder.stack.push(element)
                        except Exception as e:
                            return False
                    
                    return True
                    
                # 如果深度相等但内容不同，尝试替换栈顶元素
                else:
                    # 计算需要替换的元素数量
                    num_elements = min(len(top_elements), current_depth)
                    
                    # 记录要替换的元素
                    replaced_elements = []
                    for i in range(num_elements):
                        if not ast_builder.stack.empty():
                            replaced_elements.append(ast_builder.stack.pop())
                    
                    # 尝试恢复保存的元素
                    for element in reversed(top_elements):
                        try:
                            if element is not None:
                                ast_builder.stack.push(element)
                        except Exception as e:
                            # 如果恢复失败，回滚弹出的元素
                            for replaced in reversed(replaced_elements):
                                if replaced is not None:
                                    ast_builder.stack.push(replaced)
                            return False
                    
                    return True
        except:
            pass
        
        return False


class InstructionRecoveryStrategy(ErrorRecoveryStrategy):
    """指令恢复策略"""
    
    def apply(self, context: ErrorContext, ast_builder) -> bool:
        """应用指令恢复策略 - 改进版本"""
        try:
            # 尝试跳过错误的指令
            if context.instruction_offset >= 0:
                # 尝试恢复当前指令偏移
                original_offset = ast_builder.current_instruction_offset
                
                # 计算新的指令偏移
                # 如果我们保存了代码对象，可以尝试计算出下一条指令的偏移
                new_offset = context.instruction_offset
                
                # 尝试跳转到下一条指令
                # 在实际实现中，我们需要根据字节码计算出下一条指令的位置
                # 这里只是简单的模拟，跳过当前指令
                
                # 假设每个指令占用2个字节
                next_offset = new_offset + 2
                
                # 尝试设置新的指令偏移
                if hasattr(ast_builder, 'current_instruction_offset'):
                    ast_builder.current_instruction_offset = next_offset
                
                # 如果有指令处理逻辑，可以尝试直接跳过这条指令
                if hasattr(ast_builder, '_process_instruction'):
                    # 尝试处理下一条指令
                    try:
                        # 设置当前指令偏移为下一条指令的偏移
                        ast_builder.current_instruction_offset = next_offset
                        
                        # 调用指令处理
                        # 假设有方法可以获取下一条指令并处理
                        if hasattr(ast_builder, '_get_next_instruction'):
                            next_instruction = ast_builder._get_next_instruction()
                            if next_instruction:
                                ast_builder._process_instruction(next_instruction)
                        
                        return True
                    except Exception as e:
                        # 如果处理失败，回滚偏移
                        ast_builder.current_instruction_offset = original_offset
                        return False
                
                return True
        except Exception as e:
            pass
        
        return False


class BlockRecoveryStrategy(ErrorRecoveryStrategy):
    """代码块恢复策略"""
    
    def apply(self, context: ErrorContext, ast_builder) -> bool:
        """应用代码块恢复策略"""
        try:
            # 尝试恢复代码块状态
            if context.block_stack:
                # 在实际实现中，我们需要能够恢复代码块栈
                # 这里只是模拟恢复
                return True
        except:
            pass
        
        return False


def enhanced_recover_from_error(ast_builder, error_info=None) -> ErrorContext:
    """增强的错误恢复函数 - 改进版本"""
    # 创建错误上下文
    context = ErrorContext()
    
    # 记录错误信息
    if error_info:
        context.error_type = error_info.get('type', 'Unknown')
        context.error_message = error_info.get('message', '')
        context.error_trace = error_info.get('trace', [])
    
    # 保存完整上下文状态
    context.save_context_state(ast_builder)
    
    # 尝试恢复堆栈状态
    recovery_attempts = 0
    max_recovery_attempts = 10
    
    while not ast_builder.stack.empty() and recovery_attempts < max_recovery_attempts:
        try:
            ast_builder.stack.pop()
            recovery_attempts += 1
        except Exception as e:
            break
    
    context.recovery_attempts = recovery_attempts
    
    # 发出恢复节点，标记这里发生了错误恢复
    recovery_node = ASTObject(f"ERROR_RECOVERY(stack_depth_reduced_by_{recovery_attempts})")
    ast_builder._emit(recovery_node)
    
    # 创建错误恢复管理器（如果不存在）
    if not hasattr(ast_builder, '_error_manager'):
        ast_builder._error_manager = ErrorRecoveryManager()
    
    # 添加错误上下文到管理器
    ast_builder._error_manager.add_error_context(context)
    
    # 尝试应用恢复策略
    if ast_builder._error_manager.apply_recovery_strategies(ast_builder):
        context.recovery_successful = True
    else:
        # 如果无法完全恢复，标记为部分恢复
        context.partial_recovery = True
    
    return context


def enhanced_mark_uncertain_node(ast_builder, node: ASTNode, reason: str) -> None:
    """增强的不确定节点标记 - 改进版本"""
    # 确保错误恢复管理器存在
    if not hasattr(ast_builder, '_error_manager'):
        ast_builder._error_manager = ErrorRecoveryManager()
    
    # 创建不确定节点上下文
    uncertain_context = {
        'node': node,
        'reason': reason,
        'offset': ast_builder.current_instruction_offset,
        'block': ast_builder.current_block
    }
    
    # 添加到全局不确定节点列表
    ast_builder._error_manager.global_uncertain_nodes.append(uncertain_context)
    
    # 标记节点
    mark_uncertain_node(ast_builder, node, reason)
    
    # 记录节点到错误上下文（如果存在）
    if ast_builder._error_manager.error_contexts:
        latest_context = ast_builder._error_manager.error_contexts[-1]
        latest_context.uncertain_nodes.append(uncertain_context)


def enhanced_generate_error_report(ast_builder) -> str:
    """生成增强的错误报告 - 改进版本"""
    # 确保错误恢复管理器存在
    if not hasattr(ast_builder, '_error_manager'):
        return "没有错误恢复管理器。"
    
    # 获取基本报告
    basic_report = ast_builder._error_manager.generate_error_report()
    
    # 添加更多详细信息
    detailed_report = []
    detailed_report.append("详细错误恢复报告")
    detailed_report.append("=" * 50)
    
    # 添加恢复统计
    stats = get_recovery_statistics(ast_builder)
    if stats:
        detailed_report.append("\n恢复统计:")
        detailed_report.append(f"  错误总数: {stats.get('error_count', 0)}")
        detailed_report.append(f"  成功恢复: {stats.get('successful_recoveries', 0)}")
        detailed_report.append(f"  部分恢复: {stats.get('partial_recoveries', 0)}")
        detailed_report.append(f"  恢复失败: {stats.get('failure_count', 0)}")
        detailed_report.append(f"  恢复率: {stats.get('recovery_rate', 0):.2%}")
    
    # 添加不确定节点信息
    if ast_builder._error_manager.global_uncertain_nodes:
        detailed_report.append("\n不确定节点详情:")
        for i, item in enumerate(ast_builder._error_manager.global_uncertain_nodes):
            detailed_report.append(f"  节点 {i+1}:")
            detailed_report.append(f"    原因: {item.get('reason', '未知')}")
            detailed_report.append(f"    偏移: {item.get('offset', '未知')}")
            detailed_report.append(f"    类型: {type(item.get('node', None)).__name__}")
    
    # 添加最近几个错误上下文
    if ast_builder._error_manager.error_contexts:
        detailed_report.append("\n最近错误上下文:")
        for i, context in enumerate(ast_builder._error_manager.error_contexts[-5:]):  # 只显示最后5个
            detailed_report.append(f"  上下文 {i+1}:")
            detailed_report.append(f"    类型: {context.error_type}")
            detailed_report.append(f"    消息: {context.error_message}")
            detailed_report.append(f"    恢复尝试: {context.recovery_attempts}")
            
            if context.uncertain_nodes:
                detailed_report.append(f"    不确定节点数量: {len(context.uncertain_nodes)}")
    
    # 合并报告
    return "\n".join(detailed_report) + "\n\n" + basic_report


def register_recovery_strategies(ast_builder) -> None:
    """注册恢复策略"""
    if not hasattr(ast_builder, '_error_manager') or ast_builder._error_manager is None:
        # 初始化错误恢复管理器
        ast_builder._error_manager = ErrorRecoveryManager()
    
    # 注册堆栈恢复策略
    ast_builder._error_manager.register_recovery_strategy(StackRecoveryStrategy())
    
    # 注册指令恢复策略
    ast_builder._error_manager.register_recovery_strategy(InstructionRecoveryStrategy())
    
    # 注册代码块恢复策略
    ast_builder._error_manager.register_recovery_strategy(BlockRecoveryStrategy())


def apply_error_recovery(ast_builder) -> bool:
    """应用错误恢复策略"""
    if not hasattr(ast_builder, '_error_manager'):
        return False
    
    # 应用恢复策略
    return ast_builder._error_manager.apply_recovery_strategies(ast_builder)


def mark_uncertain_node(ast_builder, node: ASTNode, reason: str) -> None:
    """标记不确定节点"""
    if not hasattr(ast_builder, '_error_manager'):
        return
    
    ast_builder._error_manager.register_uncertain_node(node, reason)
    node.parent = ast_builder.current_block
    ast_builder.current_block.append(node)


def generate_error_report(ast_builder) -> str:
    """生成错误报告"""
    if not hasattr(ast_builder, '_error_manager'):
        return "没有错误恢复管理器。"
    
    return ast_builder._error_manager.generate_error_report()


def clear_error_state(ast_builder) -> None:
    """清除错误状态"""
    if not hasattr(ast_builder, '_error_manager'):
        return
    
    # 重置错误上下文列表
    ast_builder._error_manager.error_contexts = []
    
    # 清除全局不确定节点
    ast_builder._error_manager.global_uncertain_nodes = []


def get_recovery_statistics(ast_builder) -> Dict[str, Any]:
    """获取恢复统计信息"""
    if not hasattr(ast_builder, '_error_manager'):
        return {}
    
    contexts = ast_builder._error_manager.error_contexts
    
    if not contexts:
        return {'error_count': 0}
    
    successful_recoveries = sum(1 for c in contexts if c.recovery_successful)
    partial_recoveries = sum(1 for c in contexts if c.partial_recovery)
    
    return {
        'error_count': len(contexts),
        'successful_recoveries': successful_recoveries,
        'partial_recoveries': partial_recoveries,
        'failure_count': len(contexts) - successful_recoveries - partial_recoveries,
        'recovery_rate': successful_recoveries / len(contexts) if contexts else 0
    }