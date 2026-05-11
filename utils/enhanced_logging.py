#!/usr/bin/env python3
"""
增强的日志记录系统

为Pycdc-Python提供详细的日志记录功能
"""

import logging
import sys
import time
import traceback
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from io import StringIO


class PycdcLogHandler(logging.Handler):
    """Pycdc-Python自定义日志处理器"""
    
    def __init__(self, level=logging.DEBUG, log_file=None):
        super().__init__(level)
        self.log_file = log_file
        self.log_records = []
        
        # 创建日志文件处理器（如果指定了日志文件）
        if log_file:
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setLevel(level)
        else:
            self.file_handler = None
    
    def emit(self, record):
        """发送日志记录"""
        # 添加时间戳
        if not hasattr(record, 'timestamp'):
            record.timestamp = time.time()
        
        # 格式化日志记录
        formatted_record = self.format(record)
        
        # 添加到内存中的记录列表
        self.log_records.append(record)
        
        # 如果指定了日志文件，写入文件
        if self.file_handler:
            self.file_handler.emit(record)
    
    def get_recent_logs(self, count=100):
        """获取最近的日志记录"""
        return self.log_records[-count:]
    
    def filter_logs(self, level=None, pattern=None):
        """过滤日志记录"""
        filtered_logs = self.log_records
        
        # 按级别过滤
        if level is not None:
            filtered_logs = [log for log in filtered_logs if log.levelno >= level]
        
        # 按模式过滤
        if pattern is not None:
            filtered_logs = [log for log in filtered_logs if pattern in log.getMessage()]
        
        return filtered_logs
    
    def clear_logs(self):
        """清除日志记录"""
        self.log_records.clear()


class PycdcLogger:
    """Pycdc-Python日志记录器"""
    
    def __init__(self, name='pycdc', level=logging.DEBUG, log_file=None):
        self.name = name
        self.level = level
        self.log_file = log_file
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 清除之前的处理器
        self.logger.handlers.clear()
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 创建自定义日志处理器
        self.log_handler = PycdcLogHandler(level, log_file)
        self.log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
        self.log_handler.setFormatter(self.log_formatter)
        self.logger.addHandler(self.log_handler)
        
        # 创建统计信息
        self.stats = {
            'execution_time': 0,
            'memory_usage': 0,
            'instruction_count': 0,
            'error_count': 0,
            'warning_count': 0
        }
        
        # 创建性能计时器
        self.timers = {}
        
        # 创建字节码指令执行跟踪器
        self.instruction_tracker = {
            'total_instructions': 0,
            'processed_instructions': 0,
            'failed_instructions': 0,
            'skipped_instructions': 0,
            'instruction_timeline': []
        }
    
    def set_level(self, level):
        """设置日志级别"""
        self.level = level
        self.logger.setLevel(level)
        self.log_handler.setLevel(level)
        if self.log_handler.file_handler:
            self.log_handler.file_handler.setLevel(level)
    
    def debug(self, message, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """记录一般信息"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """记录警告信息"""
        self.stats['warning_count'] += 1
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """记录错误信息"""
        self.stats['error_count'] += 1
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """记录严重错误信息"""
        self.logger.critical(message, *args, **kwargs)
    
    def start_timer(self, name):
        """开始计时"""
        self.timers[name] = time.time()
    
    def end_timer(self, name):
        """结束计时"""
        if name in self.timers:
            elapsed = time.time() - self.timers[name]
            self.info(f"Timer '{name}': {elapsed:.4f} seconds")
            self.stats['execution_time'] += elapsed
            del self.timers[name]
            return elapsed
        return 0
    
    def track_instruction(self, opcode, offset, result='success'):
        """跟踪字节码指令执行"""
        self.instruction_tracker['total_instructions'] += 1
        self.instruction_tracker['processed_instructions'] += 1
        
        # 记录指令执行时间线
        timestamp = time.time()
        self.instruction_tracker['instruction_timeline'].append({
            'timestamp': timestamp,
            'opcode': opcode,
            'offset': offset,
            'result': result
        })
        
        # 限制时间线大小
        if len(self.instruction_tracker['instruction_timeline']) > 1000:
            self.instruction_tracker['instruction_timeline'] = self.instruction_tracker['instruction_timeline'][-1000:]
        
        # 记录详细日志
        if result == 'success':
            self.debug(f"Processed instruction: {opcode} at offset {offset}")
        elif result == 'failed':
            self.instruction_tracker['failed_instructions'] += 1
            self.error(f"Failed to process instruction: {opcode} at offset {offset}")
        elif result == 'skipped':
            self.instruction_tracker['skipped_instructions'] += 1
            self.warning(f"Skipped instruction: {opcode} at offset {offset}")
    
    def get_recent_logs(self, count=100):
        """获取最近的日志记录"""
        return self.log_handler.get_recent_logs(count)
    
    def filter_logs(self, level=None, pattern=None):
        """过滤日志记录"""
        return self.log_handler.filter_logs(level, pattern)
    
    def clear_logs(self):
        """清除日志记录"""
        self.log_handler.clear_logs()
        self.instruction_tracker['instruction_timeline'].clear()
    
    def get_stats(self):
        """获取统计信息"""
        stats = self.stats.copy()
        stats['instruction_stats'] = self.instruction_tracker.copy()
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'execution_time': 0,
            'memory_usage': 0,
            'instruction_count': 0,
            'error_count': 0,
            'warning_count': 0
        }
        
        self.instruction_tracker = {
            'total_instructions': 0,
            'processed_instructions': 0,
            'failed_instructions': 0,
            'skipped_instructions': 0,
            'instruction_timeline': []
        }
    
    def generate_report(self):
        """生成日志报告"""
        stats = self.get_stats()
        
        report = ["Pycdc-Python日志报告", "=" * 50]
        report.append(f"执行时间: {stats['execution_time']:.4f}秒")
        report.append(f"内存使用: {stats['memory_usage']:.2f}MB")
        report.append(f"错误数量: {stats['error_count']}")
        report.append(f"警告数量: {stats['warning_count']}")
        
        if stats['instruction_stats']:
            report.append("")
            report.append("字节码指令执行统计:")
            report.append("-" * 30)
            inst_stats = stats['instruction_stats']
            report.append(f"总指令数: {inst_stats['total_instructions']}")
            report.append(f"成功处理: {inst_stats['processed_instructions']}")
            report.append(f"失败处理: {inst_stats['failed_instructions']}")
            report.append(f"跳过指令: {inst_stats['skipped_instructions']}")
            
            # 计算成功率
            if inst_stats['total_instructions'] > 0:
                success_rate = inst_stats['processed_instructions'] / inst_stats['total_instructions'] * 100
                report.append(f"成功率: {success_rate:.2f}%")
        
        return "\n".join(report)


def log_instruction(logger_func, opcode, offset, *args, **kwargs):
    """字节码指令执行日志记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*func_args, **func_kwargs):
            result = None
            error = None
            try:
                result = func(*func_args, **func_kwargs)
                logger_func(f"Processed instruction: {opcode} at offset {offset}")
                return result
            except Exception as e:
                error = e
                logger_func(f"Failed to process instruction: {opcode} at offset {offset}: {str(e)}")
                raise
        return wrapper
    return decorator


def log_performance(logger_func):
    """性能日志记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = get_memory_usage()
            
            logger_func(f"Starting execution of {func.__name__}")
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                end_memory = get_memory_usage()
                
                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory
                
                logger_func(f"Completed execution of {func.__name__} in {execution_time:.4f}s")
                if memory_delta > 0:
                    logger_func(f"Memory delta: {memory_delta:.2f}MB")
                
                return result
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                
                logger_func(f"Execution of {func.__name__} failed after {execution_time:.4f}s: {str(e)}")
                raise
        return wrapper
    return decorator


def log_error(logger_func):
    """错误日志记录装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__name__}: {str(e)}"
                logger_func(error_msg)
                logger_func(f"Traceback: {traceback.format_exc()}")
                raise
        return wrapper
    return decorator


def get_memory_usage():
    """获取当前内存使用情况（MB）"""
    import os
    import psutil
    
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


# 创建一个全局日志记录器实例
_global_logger = PycdcLogger()


def get_logger(name='pycdc'):
    """获取全局日志记录器实例"""
    return _global_logger


def configure_logging(name='pycdc', level=logging.DEBUG, log_file=None):
    """配置全局日志记录器"""
    global _global_logger
    _global_logger = PycdcLogger(name, level, log_file)
    return _global_logger


def debug(message, *args, **kwargs):
    """记录调试信息"""
    _global_logger.debug(message, *args, **kwargs)


def info(message, *args, **kwargs):
    """记录一般信息"""
    _global_logger.info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    """记录警告信息"""
    _global_logger.warning(message, *args, **kwargs)


def error(message, *args, **kwargs):
    """记录错误信息"""
    _global_logger.error(message, *args, **kwargs)


def critical(message, *args, **kwargs):
    """记录严重错误信息"""
    _global_logger.critical(message, *args, **kwargs)