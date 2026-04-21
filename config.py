from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional, Callable, TypeVar, Tuple, List, Union
from dataclasses import dataclass, field, asdict
from contextvars import ContextVar
import threading
import uuid

T = TypeVar('T')


_decorator_config_store: Dict[str, Any] = {}
_config_lock = threading.RLock()


_request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
_trace_id_ctx: ContextVar[str] = ContextVar('trace_id', default='')
_span_id_ctx: ContextVar[str] = ContextVar('span_id', default='')
_user_ctx: ContextVar[Dict[str, Any]] = ContextVar('user_context')
_extra_ctx: ContextVar[Dict[str, Any]] = ContextVar('extra_context')


class DecoratorContext:
    @staticmethod
    def get_request_id() -> str:
        return _request_id_ctx.get()
    
    @staticmethod
    def set_request_id(value: str) -> None:
        _request_id_ctx.set(value)
    
    @staticmethod
    def generate_request_id() -> str:
        rid = str(uuid.uuid4())[:12]
        _request_id_ctx.set(rid)
        return rid
    
    @staticmethod
    def get_trace_id() -> str:
        return _trace_id_ctx.get()
    
    @staticmethod
    def set_trace_id(value: str) -> None:
        _trace_id_ctx.set(value)
    
    @staticmethod
    def generate_trace_id() -> str:
        tid = str(uuid.uuid4())[:16]
        _trace_id_ctx.set(tid)
        return tid
    
    @staticmethod
    def get_span_id() -> str:
        return _span_id_ctx.get()
    
    @staticmethod
    def set_span_id(value: str) -> None:
        _span_id_ctx.set(value)
    
    @staticmethod
    def generate_span_id() -> str:
        sid = str(uuid.uuid4())[:8]
        _span_id_ctx.set(sid)
        return sid
    
    @staticmethod
    def get_user_context() -> Dict[str, Any]:
        try:
            return _user_ctx.get()
        except LookupError:
            return {}
    
    @staticmethod
    def set_user_context(value: Dict[str, Any]) -> None:
        _user_ctx.set(value)
    
    @staticmethod
    def update_user_context(**kwargs: Any) -> None:
        try:
            current = _user_ctx.get()
        except LookupError:
            current = {}
        current.update(kwargs)
        _user_ctx.set(current)
    
    @staticmethod
    def get_extra_context() -> Dict[str, Any]:
        try:
            return _extra_ctx.get()
        except LookupError:
            return {}
    
    @staticmethod
    def set_extra_context(value: Dict[str, Any]) -> None:
        _extra_ctx.set(value)
    
    @staticmethod
    def update_extra_context(**kwargs: Any) -> None:
        try:
            current = _extra_ctx.get()
        except LookupError:
            current = {}
        current.update(kwargs)
        _extra_ctx.set(current)
    
    @staticmethod
    def get_all_context() -> Dict[str, Any]:
        try:
            user_ctx = _user_ctx.get().copy()
        except LookupError:
            user_ctx = {}
        
        try:
            extra_ctx = _extra_ctx.get().copy()
        except LookupError:
            extra_ctx = {}
        
        return {
            'request_id': _request_id_ctx.get(),
            'trace_id': _trace_id_ctx.get(),
            'span_id': _span_id_ctx.get(),
            'user': user_ctx,
            'extra': extra_ctx,
        }
    
    @staticmethod
    def set_all_context(ctx: Dict[str, Any]) -> None:
        if 'request_id' in ctx:
            _request_id_ctx.set(ctx['request_id'])
        if 'trace_id' in ctx:
            _trace_id_ctx.set(ctx['trace_id'])
        if 'span_id' in ctx:
            _span_id_ctx.set(ctx['span_id'])
        if 'user' in ctx:
            _user_ctx.set(ctx['user'].copy())
        if 'extra' in ctx:
            _extra_ctx.set(ctx['extra'].copy())
    
    @staticmethod
    def clear() -> None:
        _request_id_ctx.set('')
        _trace_id_ctx.set('')
        _span_id_ctx.set('')
        _user_ctx.set({})
        _extra_ctx.set({})


def with_context(**context_kwargs: Any) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        import functools
        import asyncio
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            old_context = DecoratorContext.get_all_context()
            try:
                if 'request_id' in context_kwargs:
                    DecoratorContext.set_request_id(context_kwargs['request_id'])
                if 'trace_id' in context_kwargs:
                    DecoratorContext.set_trace_id(context_kwargs['trace_id'])
                if 'span_id' in context_kwargs:
                    DecoratorContext.set_span_id(context_kwargs['span_id'])
                if 'user' in context_kwargs:
                    DecoratorContext.set_user_context(context_kwargs['user'])
                if 'extra' in context_kwargs:
                    DecoratorContext.set_extra_context(context_kwargs['extra'])
                
                DecoratorContext.update_extra_context(**{
                    k: v for k, v in context_kwargs.items()
                    if k not in {'request_id', 'trace_id', 'span_id', 'user', 'extra'}
                })
                
                return func(*args, **kwargs)
            finally:
                DecoratorContext.set_all_context(old_context)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            old_context = DecoratorContext.get_all_context()
            try:
                if 'request_id' in context_kwargs:
                    DecoratorContext.set_request_id(context_kwargs['request_id'])
                if 'trace_id' in context_kwargs:
                    DecoratorContext.set_trace_id(context_kwargs['trace_id'])
                if 'span_id' in context_kwargs:
                    DecoratorContext.set_span_id(context_kwargs['span_id'])
                if 'user' in context_kwargs:
                    DecoratorContext.set_user_context(context_kwargs['user'])
                if 'extra' in context_kwargs:
                    DecoratorContext.set_extra_context(context_kwargs['extra'])
                
                DecoratorContext.update_extra_context(**{
                    k: v for k, v in context_kwargs.items()
                    if k not in {'request_id', 'trace_id', 'span_id', 'user', 'extra'}
                })
                
                return await func(*args, **kwargs)
            finally:
                DecoratorContext.set_all_context(old_context)
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@dataclass
class LogConfig:
    level: str = "INFO"
    log_args: bool = True
    log_return: bool = True
    log_time: bool = True
    log_context: bool = True
    enabled: bool = True


@dataclass
class TimerConfig:
    unit: str = "ms"
    precision: int = 4
    log_level: str = "INFO"
    enabled: bool = True


@dataclass
class CatchConfig:
    exceptions: Tuple[type, ...] = (Exception,)
    default: Any = None
    reraise: bool = False
    log_error: bool = True
    enabled: bool = True


@dataclass
class RateLimitConfig:
    max_calls: int = 10
    time_window: float = 60.0
    wait: bool = False
    on_limit: Optional[Callable] = None
    thread_safe: bool = True
    process_safe: bool = False
    enabled: bool = True


@dataclass
class RetryConfig:
    max_attempts: int = 3
    delay: float = 1.0
    backoff: float = 1.0
    exceptions: Tuple[type, ...] = (Exception,)
    enabled: bool = True


@dataclass
class MonitorConfig:
    name: Optional[str] = None
    track_calls: bool = True
    track_errors: bool = True
    track_latency: bool = True
    track_exceptions: bool = True
    histogram_bins: int = 10
    enabled: bool = True


@dataclass
class DecoratorChainConfig:
    log: Optional[LogConfig] = None
    timer: Optional[TimerConfig] = None
    catch: Optional[CatchConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    retry: Optional[RetryConfig] = None
    monitor: Optional[MonitorConfig] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.log and self.log.enabled:
            result['log'] = asdict(self.log)
        if self.timer and self.timer.enabled:
            result['timer'] = asdict(self.timer)
        if self.catch and self.catch.enabled:
            result['catch'] = asdict(self.catch)
        if self.rate_limit and self.rate_limit.enabled:
            rl_dict = asdict(self.rate_limit)
            if 'on_limit' in rl_dict:
                del rl_dict['on_limit']
            if 'exceptions' in rl_dict:
                rl_dict['exceptions'] = [e.__name__ for e in rl_dict['exceptions']]
            result['rate_limit'] = rl_dict
        if self.retry and self.retry.enabled:
            rt_dict = asdict(self.retry)
            if 'exceptions' in rt_dict:
                rt_dict['exceptions'] = [e.__name__ for e in rt_dict['exceptions']]
            result['retry'] = rt_dict
        if self.monitor and self.monitor.enabled:
            result['monitor'] = asdict(self.monitor)
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DecoratorChainConfig':
        instance = cls()
        
        if 'log' in config_dict:
            log_cfg = config_dict['log']
            if log_cfg.get('enabled', True):
                instance.log = LogConfig(
                    level=log_cfg.get('level', 'INFO'),
                    log_args=log_cfg.get('log_args', True),
                    log_return=log_cfg.get('log_return', True),
                    log_time=log_cfg.get('log_time', True),
                    log_context=log_cfg.get('log_context', True),
                    enabled=True
                )
        
        if 'timer' in config_dict:
            timer_cfg = config_dict['timer']
            if timer_cfg.get('enabled', True):
                instance.timer = TimerConfig(
                    unit=timer_cfg.get('unit', 'ms'),
                    precision=timer_cfg.get('precision', 4),
                    log_level=timer_cfg.get('log_level', 'INFO'),
                    enabled=True
                )
        
        if 'catch' in config_dict:
            catch_cfg = config_dict['catch']
            if catch_cfg.get('enabled', True):
                exceptions_list = catch_cfg.get('exceptions', ['Exception'])
                exceptions = tuple(
                    _exception_from_name(name) for name in exceptions_list
                )
                instance.catch = CatchConfig(
                    exceptions=exceptions,
                    default=catch_cfg.get('default'),
                    reraise=catch_cfg.get('reraise', False),
                    log_error=catch_cfg.get('log_error', True),
                    enabled=True
                )
        
        if 'rate_limit' in config_dict:
            rl_cfg = config_dict['rate_limit']
            if rl_cfg.get('enabled', True):
                instance.rate_limit = RateLimitConfig(
                    max_calls=rl_cfg.get('max_calls', 10),
                    time_window=rl_cfg.get('time_window', 60.0),
                    wait=rl_cfg.get('wait', False),
                    thread_safe=rl_cfg.get('thread_safe', True),
                    process_safe=rl_cfg.get('process_safe', False),
                    enabled=True
                )
        
        if 'retry' in config_dict:
            rt_cfg = config_dict['retry']
            if rt_cfg.get('enabled', True):
                exceptions_list = rt_cfg.get('exceptions', ['Exception'])
                exceptions = tuple(
                    _exception_from_name(name) for name in exceptions_list
                )
                instance.retry = RetryConfig(
                    max_attempts=rt_cfg.get('max_attempts', 3),
                    delay=rt_cfg.get('delay', 1.0),
                    backoff=rt_cfg.get('backoff', 1.0),
                    exceptions=exceptions,
                    enabled=True
                )
        
        if 'monitor' in config_dict:
            mon_cfg = config_dict['monitor']
            if mon_cfg.get('enabled', True):
                instance.monitor = MonitorConfig(
                    name=mon_cfg.get('name'),
                    track_calls=mon_cfg.get('track_calls', True),
                    track_errors=mon_cfg.get('track_errors', True),
                    track_latency=mon_cfg.get('track_latency', True),
                    track_exceptions=mon_cfg.get('track_exceptions', True),
                    histogram_bins=mon_cfg.get('histogram_bins', 10),
                    enabled=True
                )
        
        return instance


def _exception_from_name(name: str) -> type:
    if name == 'Exception':
        return Exception
    if name == 'ValueError':
        return ValueError
    if name == 'TypeError':
        return TypeError
    if name == 'ZeroDivisionError':
        return ZeroDivisionError
    if name == 'ConnectionError':
        return ConnectionError
    if name == 'TimeoutError':
        return TimeoutError
    if name == 'IOError':
        return IOError
    if name == 'KeyError':
        return KeyError
    if name == 'IndexError':
        return IndexError
    if name == 'AttributeError':
        return AttributeError
    try:
        import builtins
        return getattr(builtins, name)
    except AttributeError:
        return Exception


def load_config_from_dict(config_dict: Dict[str, Any]) -> DecoratorChainConfig:
    return DecoratorChainConfig.from_dict(config_dict)


def load_config_from_json(json_str: str) -> DecoratorChainConfig:
    config_dict = json.loads(json_str)
    return DecoratorChainConfig.from_dict(config_dict)


def load_config_from_file(file_path: str) -> DecoratorChainConfig:
    if not os.path.exists(file_path):
        return DecoratorChainConfig()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.endswith('.json'):
            config_dict = json.load(f)
        elif file_path.endswith(('.yaml', '.yml')):
            try:
                import yaml
                config_dict = yaml.safe_load(f)
            except ImportError:
                raise RuntimeError("PyYAML not installed. Please install with: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported config file format: {file_path}")
    
    return DecoratorChainConfig.from_dict(config_dict)


def save_config_to_file(config: DecoratorChainConfig, file_path: str) -> None:
    config_dict = config.to_dict()
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if file_path.endswith('.json'):
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        elif file_path.endswith(('.yaml', '.yml')):
            try:
                import yaml
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                raise RuntimeError("PyYAML not installed. Please install with: pip install pyyaml")
        else:
            raise ValueError(f"Unsupported config file format: {file_path}")


def get_global_config(decorator_name: str) -> Optional[Dict[str, Any]]:
    with _config_lock:
        return _decorator_config_store.get(decorator_name)


def set_global_config(decorator_name: str, config: Dict[str, Any]) -> None:
    with _config_lock:
        _decorator_config_store[decorator_name] = config


def enable_decorator(decorator_name: str) -> None:
    with _config_lock:
        if decorator_name in _decorator_config_store:
            _decorator_config_store[decorator_name]['enabled'] = True


def disable_decorator(decorator_name: str) -> None:
    with _config_lock:
        if decorator_name in _decorator_config_store:
            _decorator_config_store[decorator_name]['enabled'] = False


def is_decorator_enabled(decorator_name: str) -> bool:
    with _config_lock:
        cfg = _decorator_config_store.get(decorator_name)
        return cfg.get('enabled', True) if cfg else True


def update_rate_limit_config(max_calls: Optional[int] = None, 
                              time_window: Optional[float] = None) -> None:
    with _config_lock:
        if 'rate_limit' not in _decorator_config_store:
            _decorator_config_store['rate_limit'] = {}
        
        if max_calls is not None:
            _decorator_config_store['rate_limit']['max_calls'] = max_calls
        if time_window is not None:
            _decorator_config_store['rate_limit']['time_window'] = time_window


def update_retry_config(max_attempts: Optional[int] = None,
                        delay: Optional[float] = None,
                        backoff: Optional[float] = None) -> None:
    with _config_lock:
        if 'retry' not in _decorator_config_store:
            _decorator_config_store['retry'] = {}
        
        if max_attempts is not None:
            _decorator_config_store['retry']['max_attempts'] = max_attempts
        if delay is not None:
            _decorator_config_store['retry']['delay'] = delay
        if backoff is not None:
            _decorator_config_store['retry']['backoff'] = backoff


DEFAULT_CONFIG = DecoratorChainConfig(
    log=LogConfig(
        level="INFO",
        log_args=True,
        log_return=True,
        log_time=True,
        log_context=True,
        enabled=True
    ),
    timer=TimerConfig(
        unit="ms",
        precision=4,
        log_level="INFO",
        enabled=True
    ),
    catch=CatchConfig(
        exceptions=(Exception,),
        default=None,
        reraise=False,
        log_error=True,
        enabled=True
    ),
    rate_limit=RateLimitConfig(
        max_calls=10,
        time_window=60.0,
        wait=False,
        thread_safe=True,
        process_safe=False,
        enabled=True
    ),
    retry=RetryConfig(
        max_attempts=3,
        delay=1.0,
        backoff=1.0,
        exceptions=(Exception,),
        enabled=True
    ),
    monitor=MonitorConfig(
        name=None,
        track_calls=True,
        track_errors=True,
        track_latency=True,
        track_exceptions=True,
        histogram_bins=10,
        enabled=True
    )
)
