"""Round 144: 复杂类方法4"""
from typing import List, Dict, Any, Iterator

class EventEmitter:
    """事件发射器"""
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = {}
    
    def on(self, event: str, listener: callable) -> None:
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        if event in self.listeners:
            for listener in self.listeners[event]:
                listener(*args, **kwargs)
    
    def remove_listener(self, event: str, listener: callable) -> None:
        if event in self.listeners:
            self.listeners[event] = [l for l in self.listeners[event] if l != listener]

def test_event_emitter():
    emitter = EventEmitter()
    results = []
    def listener(x):
        results.append(x)
    emitter.on('test', listener)
    emitter.emit('test', 1)
    assert results == [1]
