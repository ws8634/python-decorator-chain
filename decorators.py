import functools
import time
import logging
import uuid
import asyncio
import inspect
import threading
from typing import Any, Callable, Optional, Type, Tuple, List, Dict, Union
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import math
import statistics

try:
    import multiprocessing
    from multiprocessing import Manager
    HAS_MULTIPROCESSING = True
except ImportError:
    HAS_MULTIPROCESSING = False

try:
    import fcntl
    import os
    HAS_FILE_LOCK = True
except ImportError:
    HAS_FILE_LOCK = False

from config import DecoratorContext, get_global_config, is_decorator_enabled

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = DecoratorContext.get_request_id() or '-'
        record.trace_id = DecoratorContext.get_trace_id() or '-'
        return True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [REQ_ID:%(request_id)s] [TRACE_ID:%(trace_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("DecoratorSystem")
context_filter = ContextFilter()

root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.addFilter(context_filter)

for handler in logger.handlers:
    handler.addFilter(context_filter)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [REQ_ID:%(request_id)s] [TRACE_ID:%(trace_id)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    handler.addFilter(context_filter)
    logger.addHandler(handler)


_global_monitor_registry: Dict[str, 'MonitorStats'] = {}
_monitor_lock = threading.RLock()


@dataclass
class MonitorStats:
    name: str
    total_calls: int = 0
    success_calls: int = 0
    error_calls: int = 0
    total_latency: float = 0.0
    max_latency: float = 0.0
    min_latency: float = float('inf')
    latency_samples: List[float] = field(default_factory=list)
    exception_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    histogram_bins: int = 10
    histogram: List[int] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated_at: float = field(default_factory=time.time)
    _lock: threading.RLock = field(default_factory=threading.RLock)
    
    def record_success(self, latency: float) -> None:
        with self._lock:
            self.total_calls += 1
            self.success_calls += 1
            self.total_latency += latency
            self.max_latency = max(self.max_latency, latency)
            self.min_latency = min(self.min_latency, latency)
            self.latency_samples.append(latency)
            self.last_updated_at = time.time()
    
    def record_error(self, latency: float, exception_type: str) -> None:
        with self._lock:
            self.total_calls += 1
            self.error_calls += 1
            self.total_latency += latency
            self.max_latency = max(self.max_latency, latency)
            self.min_latency = min(self.min_latency, latency)
            self.latency_samples.append(latency)
            self.exception_counts[exception_type] += 1
            self.last_updated_at = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = self.total_latency / self.total_calls if self.total_calls > 0 else 0.0
            success_rate = (self.success_calls / self.total_calls * 100) if self.total_calls > 0 else 100.0
            error_rate = (self.error_calls / self.total_calls * 100) if self.total_calls > 0 else 0.0
            
            p50 = p95 = p99 = 0.0
            if self.latency_samples:
                sorted_samples = sorted(self.latency_samples)
                n = len(sorted_samples)
                p50 = sorted_samples[int(n * 0.5)] if n > 0 else 0.0
                p95 = sorted_samples[int(n * 0.95)] if n > 0 else 0.0
                p99 = sorted_samples[int(n * 0.99)] if n > 0 else 0.0
            
            uptime = self.last_updated_at - self.created_at
            
            return {
                'name': self.name,
                'total_calls': self.total_calls,
                'success_calls': self.success_calls,
                'error_calls': self.error_calls,
                'success_rate_pct': round(success_rate, 2),
                'error_rate_pct': round(error_rate, 2),
                'avg_latency_ms': round(avg_latency * 1000, 4),
                'min_latency_ms': round(self.min_latency * 1000, 4) if self.min_latency != float('inf') else 0.0,
                'max_latency_ms': round(self.max_latency * 1000, 4),
                'p50_latency_ms': round(p50 * 1000, 4),
                'p95_latency_ms': round(p95 * 1000, 4),
                'p99_latency_ms': round(p99 * 1000, 4),
                'exception_distribution': dict(self.exception_counts),
                'total_samples': len(self.latency_samples),
                'uptime_seconds': round(uptime, 2),
            }
    
    def reset(self) -> None:
        with self._lock:
            self.total_calls = 0
            self.success_calls = 0
            self.error_calls = 0
            self.total_latency = 0.0
            self.max_latency = 0.0
            self.min_latency = float('inf')
            self.latency_samples = []
            self.exception_counts = defaultdict(int)
            self.created_at = time.time()
            self.last_updated_at = time.time()


def get_monitor_stats(name: Optional[str] = None) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    with _monitor_lock:
        if name:
            if name in _global_monitor_registry:
                return _global_monitor_registry[name].get_stats()
            return {}
        return {k: v.get_stats() for k, v in _global_monitor_registry.items()}


def print_monitor_report(name: Optional[str] = None) -> None:
    stats = get_monitor_stats(name)
    
    if not stats:
        print("\n【监控统计】没有可用的监控数据")
        return
    
    print("\n" + "=" * 80)
    print("【监控统计报表】")
    print("=" * 80)
    
    if name and isinstance(stats, dict) and 'name' in stats:
        _print_single_monitor(stats)
    else:
        for mon_name, mon_stats in stats.items():
            print(f"\n--- {mon_name} ---")
            _print_single_monitor(mon_stats)


def _print_single_monitor(stats: Dict[str, Any]) -> None:
    print(f"""
  调用统计:
    - 总调用次数: {stats['total_calls']}
    - 成功次数: {stats['success_calls']}
    - 失败次数: {stats['error_calls']}
    - 成功率: {stats['success_rate_pct']}%
    - 失败率: {stats['error_rate_pct']}%
  
  延迟统计 (毫秒):
    - 平均延迟: {stats['avg_latency_ms']}
    - 最小延迟: {stats['min_latency_ms']}
    - 最大延迟: {stats['max_latency_ms']}
    - P50 延迟: {stats['p50_latency_ms']}
    - P95 延迟: {stats['p95_latency_ms']}
    - P99 延迟: {stats['p99_latency_ms']}
""")
    
    if stats['exception_distribution']:
        print("  异常分布:")
        for exc_type, count in stats['exception_distribution'].items():
            print(f"    - {exc_type}: {count} 次")
    
    print(f"  运行时长: {stats['uptime_seconds']} 秒")
    print(f"  采样数量: {stats['total_samples']}")


def reset_monitor(name: Optional[str] = None) -> None:
    with _monitor_lock:
        if name and name in _global_monitor_registry:
            _global_monitor_registry[name].reset()
        else:
            for stats in _global_monitor_registry.values():
                stats.reset()


def _is_async_func(func: Callable) -> bool:
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


def _get_or_create_monitor(name: str) -> MonitorStats:
    with _monitor_lock:
        if name not in _global_monitor_registry:
            _global_monitor_registry[name] = MonitorStats(name=name)
        return _global_monitor_registry[name]


@dataclass
class RateLimitState:
    calls: List[float] = field(default_factory=list)
    max_calls: int = 10
    time_window: float = 60.0
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def acquire(self) -> bool:
        with self._lock:
            current_time = time.time()
            self.calls = [t for t in self.calls if current_time - t < self.time_window]
            
            if len(self.calls) >= self.max_calls:
                return False
            
            self.calls.append(current_time)
            return True
    
    def get_remaining(self) -> int:
        with self._lock:
            current_time = time.time()
            self.calls = [t for t in self.calls if current_time - t < self.time_window]
            return max(0, self.max_calls - len(self.calls))


class _ProcessSafeRateLimiter:
    def __init__(self, max_calls: int = 10, time_window: float = 60.0):
        self.max_calls = max_calls
        self.time_window = time_window
        self._manager: Optional[Manager] = None
        self._shared_calls: Optional[Any] = None
        self._shared_lock: Optional[Any] = None
        self._initialized = False
        self._init_lock = threading.Lock()
    
    def _init_shared(self) -> None:
        if self._initialized or not HAS_MULTIPROCESSING:
            return
        
        with self._init_lock:
            if self._initialized:
                return
            
            try:
                self._manager = Manager()
                self._shared_calls = self._manager.list()
                self._shared_lock = self._manager.Lock()
                self._initialized = True
            except Exception:
                self._initialized = False
    
    def acquire(self) -> bool:
        self._init_shared()
        
        if self._initialized and self._shared_lock and self._shared_calls is not None:
            with self._shared_lock:
                current_time = time.time()
                valid_calls = [t for t in self._shared_calls if current_time - t < self.time_window]
                
                while len(self._shared_calls) > len(valid_calls):
                    self._shared_calls.pop(0)
                
                if len(valid_calls) >= self.max_calls:
                    return False
                
                self._shared_calls.append(current_time)
                return True
        else:
            if not hasattr(self, '_local_calls'):
                self._local_calls: List[float] = []
                self._local_lock = threading.Lock()
            
            with self._local_lock:
                current_time = time.time()
                self._local_calls = [t for t in self._local_calls if current_time - t < self.time_window]
                
                if len(self._local_calls) >= self.max_calls:
                    return False
                
                self._local_calls.append(current_time)
                return True


def log(level: str = "INFO", 
        log_args: bool = True, 
        log_return: bool = True, 
        log_time: bool = True,
        log_context: bool = True) -> Callable:
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('log'):
                return func(*args, **kwargs)
            
            call_id = str(uuid.uuid4())[:8]
            start_time = time.time()
            
            context_info = ""
            if log_context:
                ctx = DecoratorContext.get_all_context()
                ctx_parts = []
                if ctx.get('request_id'):
                    ctx_parts.append(f"REQ_ID: {ctx['request_id']}")
                if ctx.get('trace_id'):
                    ctx_parts.append(f"TRACE_ID: {ctx['trace_id']}")
                if ctx.get('span_id'):
                    ctx_parts.append(f"SPAN_ID: {ctx['span_id']}")
                if ctx.get('user'):
                    ctx_parts.append(f"USER: {ctx['user']}")
                if ctx.get('extra'):
                    ctx_parts.append(f"EXTRA: {ctx['extra']}")
                context_info = " ".join(ctx_parts)
                if context_info:
                    context_info = f" [{context_info}]"
            
            log_parts = [f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}]{context_info}"]
            
            if log_args:
                log_parts.append(f"[ARGS: {args}] [KWARGS: {kwargs}]")
            
            logger.log(log_level, " ".join(log_parts))
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                result_parts = [f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}] SUCCESS"]
                
                if log_return:
                    result_parts.append(f"[RETURN: {result}]")
                
                if log_time:
                    result_parts.append(f"[ELAPSED: {elapsed:.4f}s]")
                
                logger.log(log_level, " ".join(result_parts))
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}] FAILED "
                    f"[EXCEPTION: {type(e).__name__}: {e}] [ELAPSED: {elapsed:.4f}s]{context_info}"
                )
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('log'):
                return await func(*args, **kwargs)
            
            call_id = str(uuid.uuid4())[:8]
            start_time = time.time()
            
            context_info = ""
            if log_context:
                ctx = DecoratorContext.get_all_context()
                ctx_parts = []
                if ctx.get('request_id'):
                    ctx_parts.append(f"REQ_ID: {ctx['request_id']}")
                if ctx.get('trace_id'):
                    ctx_parts.append(f"TRACE_ID: {ctx['trace_id']}")
                if ctx.get('span_id'):
                    ctx_parts.append(f"SPAN_ID: {ctx['span_id']}")
                if ctx.get('user'):
                    ctx_parts.append(f"USER: {ctx['user']}")
                if ctx.get('extra'):
                    ctx_parts.append(f"EXTRA: {ctx['extra']}")
                context_info = " ".join(ctx_parts)
                if context_info:
                    context_info = f" [{context_info}]"
            
            log_parts = [f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}] [ASYNC]{context_info}"]
            
            if log_args:
                log_parts.append(f"[ARGS: {args}] [KWARGS: {kwargs}]")
            
            logger.log(log_level, " ".join(log_parts))
            
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                result_parts = [f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}] [ASYNC] SUCCESS"]
                
                if log_return:
                    result_parts.append(f"[RETURN: {result}]")
                
                if log_time:
                    result_parts.append(f"[ELAPSED: {elapsed:.4f}s]")
                
                logger.log(log_level, " ".join(result_parts))
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}] [ASYNC] FAILED "
                    f"[EXCEPTION: {type(e).__name__}: {e}] [ELAPSED: {elapsed:.4f}s]{context_info}"
                )
                raise
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def timer(unit: str = "ms", 
          precision: int = 4, 
          log_level: str = "INFO") -> Callable:
    
    valid_units = {"s": 1.0, "ms": 1000.0, "us": 1000000.0}
    multiplier = valid_units.get(unit.lower(), 1000.0)
    unit_name = unit.lower()
    
    log_level_val = getattr(logging, log_level.upper(), logging.INFO)
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('timer'):
                return func(*args, **kwargs)
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.perf_counter() - start_time) * multiplier
                logger.log(
                    log_level_val,
                    f"[TIMER] [FUNCTION: {func.__name__}] "
                    f"Execution time: {elapsed:.{precision}f} {unit_name}"
                )
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('timer'):
                return await func(*args, **kwargs)
            
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.perf_counter() - start_time) * multiplier
                logger.log(
                    log_level_val,
                    f"[TIMER] [FUNCTION: {func.__name__}] [ASYNC] "
                    f"Execution time: {elapsed:.{precision}f} {unit_name}"
                )
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def catch(exceptions: Tuple[Type[Exception], ...] = (Exception,), 
          default: Any = None, 
          reraise: bool = False,
          log_error: bool = True) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('catch'):
                return func(*args, **kwargs)
            
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.error(
                        f"[CATCH] [FUNCTION: {func.__name__}] "
                        f"Caught {type(e).__name__}: {e} - Returning default value: {default}"
                    )
                
                if reraise:
                    raise
                
                return default
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('catch'):
                return await func(*args, **kwargs)
            
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.error(
                        f"[CATCH] [FUNCTION: {func.__name__}] [ASYNC] "
                        f"Caught {type(e).__name__}: {e} - Returning default value: {default}"
                    )
                
                if reraise:
                    raise
                
                return default
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def rate_limit(max_calls: int = 10, 
               time_window: float = 60.0,
               wait: bool = False,
               on_limit: Optional[Callable] = None,
               thread_safe: bool = True,
               process_safe: bool = False) -> Callable:
    
    rate_limit_states: Dict[int, Any] = {}
    states_lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        func_id = id(func)
        
        with states_lock:
            if func_id not in rate_limit_states:
                if process_safe and HAS_MULTIPROCESSING:
                    rate_limit_states[func_id] = _ProcessSafeRateLimiter(
                        max_calls=max_calls,
                        time_window=time_window
                    )
                else:
                    rate_limit_states[func_id] = RateLimitState(
                        max_calls=max_calls,
                        time_window=time_window
                    )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('rate_limit'):
                return func(*args, **kwargs)
            
            state = rate_limit_states[func_id]
            current_time = time.time()
            
            acquired = state.acquire()
            
            if not acquired:
                if wait:
                    if isinstance(state, RateLimitState):
                        with state._lock:
                            if state.calls:
                                oldest_call = state.calls[0]
                                wait_time = state.time_window - (current_time - oldest_call)
                                if wait_time > 0:
                                    logger.warning(
                                        f"[RATE_LIMIT] [FUNCTION: {func.__name__}] "
                                        f"Rate limit exceeded ({state.max_calls}/{state.time_window}s). "
                                        f"Waiting {wait_time:.2f}s..."
                                    )
                                    time.sleep(wait_time)
                                    state.acquire()
                else:
                    if on_limit is not None:
                        if _is_async_func(on_limit):
                            pass
                        else:
                            return on_limit(*args, **kwargs)
                    
                    logger.warning(
                        f"[RATE_LIMIT] [FUNCTION: {func.__name__}] "
                        f"Rate limit exceeded ({max_calls}/{time_window}s). "
                        f"Call rejected."
                    )
                    raise RateLimitExceededError(
                        f"Function '{func.__name__}' exceeded rate limit: "
                        f"{max_calls} calls per {time_window} seconds"
                    )
            
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('rate_limit'):
                return await func(*args, **kwargs)
            
            state = rate_limit_states[func_id]
            current_time = time.time()
            
            acquired = state.acquire()
            
            if not acquired:
                if wait:
                    if isinstance(state, RateLimitState):
                        with state._lock:
                            if state.calls:
                                oldest_call = state.calls[0]
                                wait_time = state.time_window - (current_time - oldest_call)
                                if wait_time > 0:
                                    logger.warning(
                                        f"[RATE_LIMIT] [FUNCTION: {func.__name__}] [ASYNC] "
                                        f"Rate limit exceeded ({state.max_calls}/{state.time_window}s). "
                                        f"Waiting {wait_time:.2f}s..."
                                    )
                                    await asyncio.sleep(wait_time)
                                    state.acquire()
                else:
                    if on_limit is not None:
                        if _is_async_func(on_limit):
                            return await on_limit(*args, **kwargs)
                        else:
                            return on_limit(*args, **kwargs)
                    
                    logger.warning(
                        f"[RATE_LIMIT] [FUNCTION: {func.__name__}] [ASYNC] "
                        f"Rate limit exceeded ({max_calls}/{time_window}s). "
                        f"Call rejected."
                    )
                    raise RateLimitExceededError(
                        f"Function '{func.__name__}' exceeded rate limit: "
                        f"{max_calls} calls per {time_window} seconds"
                    )
            
            return await func(*args, **kwargs)
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


class RateLimitExceededError(Exception):
    pass


def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff: float = 1.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('retry'):
                return func(*args, **kwargs)
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            f"[RETRY] [FUNCTION: {func.__name__}] "
                            f"Success on attempt {attempt}/{max_attempts}"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"[RETRY] [FUNCTION: {func.__name__}] "
                            f"Attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[RETRY] [FUNCTION: {func.__name__}] "
                            f"All {max_attempts} attempts failed. Last error: {type(e).__name__}: {e}"
                        )
            
            raise last_exception
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('retry'):
                return await func(*args, **kwargs)
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            f"[RETRY] [FUNCTION: {func.__name__}] [ASYNC] "
                            f"Success on attempt {attempt}/{max_attempts}"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"[RETRY] [FUNCTION: {func.__name__}] [ASYNC] "
                            f"Attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[RETRY] [FUNCTION: {func.__name__}] [ASYNC] "
                            f"All {max_attempts} attempts failed. Last error: {type(e).__name__}: {e}"
                        )
            
            raise last_exception
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


def monitor(name: Optional[str] = None,
            track_calls: bool = True,
            track_errors: bool = True,
            track_latency: bool = True,
            track_exceptions: bool = True,
            histogram_bins: int = 10) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        monitor_name = name or func.__name__
        _get_or_create_monitor(monitor_name)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('monitor'):
                return func(*args, **kwargs)
            
            stats = _get_or_create_monitor(monitor_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                
                if track_calls and track_latency:
                    stats.record_success(latency)
                
                return result
                
            except Exception as e:
                latency = time.time() - start_time
                
                if track_errors and track_latency:
                    stats.record_error(latency, type(e).__name__)
                
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not is_decorator_enabled('monitor'):
                return await func(*args, **kwargs)
            
            stats = _get_or_create_monitor(monitor_name)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start_time
                
                if track_calls and track_latency:
                    stats.record_success(latency)
                
                return result
                
            except Exception as e:
                latency = time.time() - start_time
                
                if track_errors and track_latency:
                    stats.record_error(latency, type(e).__name__)
                
                raise
        
        if _is_async_func(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
