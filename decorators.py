import functools
import time
import logging
import uuid
import asyncio
import contextvars
import inspect
import threading
from typing import Any, Callable, Optional, Type, Tuple, List, Dict, Union, Coroutine
from dataclasses import dataclass, field
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DecoratorSystem")

global_chain_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    'global_chain_id', 
    default=""
)

decorator_nesting_level: contextvars.ContextVar[int] = contextvars.ContextVar(
    'decorator_nesting_level', 
    default=0
)


def generate_chain_id() -> str:
    return str(uuid.uuid4())[:12]


def get_indent(level: int = None) -> str:
    if level is None:
        level = decorator_nesting_level.get()
    return "  " * level


@contextmanager
def with_nesting_level():
    token = decorator_nesting_level.set(decorator_nesting_level.get() + 1)
    try:
        yield
    finally:
        decorator_nesting_level.reset(token)


def log_event(dec_name: str, event_type: str, func_name: str, extra: str = "", level: int = logging.INFO):
    chain_id = global_chain_id.get()
    indent = get_indent()
    chain_id_str = f"[CHAIN: {chain_id}]" if chain_id else ""
    logger.log(
        level,
        f"{indent}{chain_id_str} [{dec_name}] {event_type} -> {func_name} {extra}"
    )


def is_async_func(func: Callable) -> bool:
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


@dataclass
class RateLimitState:
    calls: List[float] = field(default_factory=list)
    max_calls: int = 10
    time_window: float = 60.0
    _lock: Union[threading.Lock, asyncio.Lock, None] = None
    
    def get_lock(self, is_async: bool = False):
        if self._lock is None:
            self._lock = asyncio.Lock() if is_async else threading.Lock()
        return self._lock


def log(level: str = "INFO", log_args: bool = True, log_return: bool = True, 
        log_time: bool = True) -> Callable:
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    dec_name = "log"
    
    def decorator(func: Callable) -> Callable:
        
        if is_async_func(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, level=log_level)
                
                result = None
                exception_occurred = False
                
                try:
                    with with_nesting_level():
                        call_id = global_chain_id.get()
                        start_time = time.time()
                        
                        extra_parts = []
                        if log_args:
                            extra_parts.append(f"ARGS={args} KWARGS={kwargs}")
                        if extra_parts:
                            log_event(dec_name, "PARAMS", func.__name__, " ".join(extra_parts), level=log_level)
                        
                        try:
                            result = await func(*args, **kwargs)
                            elapsed = time.time() - start_time
                            
                            result_parts = []
                            if log_return:
                                result_parts.append(f"RETURN={result}")
                            if log_time:
                                result_parts.append(f"ELAPSED={elapsed:.4f}s")
                            if result_parts:
                                log_event(dec_name, "RESULT", func.__name__, " ".join(result_parts), level=log_level)
                            
                            return result
                            
                        except Exception as e:
                            exception_occurred = True
                            elapsed = time.time() - start_time
                            log_event(
                                dec_name, "EXCEPTION", func.__name__,
                                f"{type(e).__name__}: {e} ELAPSED={elapsed:.4f}s",
                                level=logging.ERROR
                            )
                            raise
                finally:
                    exit_status = "EXCEPTION" if exception_occurred else "EXIT"
                    log_event(dec_name, exit_status, func.__name__, level=log_level if not exception_occurred else logging.ERROR)
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, level=log_level)
                
                result = None
                exception_occurred = False
                
                try:
                    with with_nesting_level():
                        call_id = global_chain_id.get()
                        start_time = time.time()
                        
                        extra_parts = []
                        if log_args:
                            extra_parts.append(f"ARGS={args} KWARGS={kwargs}")
                        if extra_parts:
                            log_event(dec_name, "PARAMS", func.__name__, " ".join(extra_parts), level=log_level)
                        
                        try:
                            result = func(*args, **kwargs)
                            elapsed = time.time() - start_time
                            
                            result_parts = []
                            if log_return:
                                result_parts.append(f"RETURN={result}")
                            if log_time:
                                result_parts.append(f"ELAPSED={elapsed:.4f}s")
                            if result_parts:
                                log_event(dec_name, "RESULT", func.__name__, " ".join(result_parts), level=log_level)
                            
                            return result
                            
                        except Exception as e:
                            exception_occurred = True
                            elapsed = time.time() - start_time
                            log_event(
                                dec_name, "EXCEPTION", func.__name__,
                                f"{type(e).__name__}: {e} ELAPSED={elapsed:.4f}s",
                                level=logging.ERROR
                            )
                            raise
                finally:
                    exit_status = "EXCEPTION" if exception_occurred else "EXIT"
                    log_event(dec_name, exit_status, func.__name__, level=log_level if not exception_occurred else logging.ERROR)
            
            return wrapper
    
    return decorator


def timer(unit: str = "ms", precision: int = 4, log_level: str = "INFO") -> Callable:
    
    valid_units = {"s": 1.0, "ms": 1000.0, "us": 1000000.0}
    multiplier = valid_units.get(unit.lower(), 1000.0)
    unit_name = unit.lower()
    log_level_val = getattr(logging, log_level.upper(), logging.INFO)
    dec_name = "timer"
    
    def decorator(func: Callable) -> Callable:
        
        if is_async_func(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, f"[UNIT={unit_name}]", level=log_level_val)
                
                start_time = time.perf_counter()
                exception_occurred = False
                
                try:
                    with with_nesting_level():
                        try:
                            result = await func(*args, **kwargs)
                            return result
                        except Exception:
                            exception_occurred = True
                            raise
                finally:
                    elapsed = (time.perf_counter() - start_time) * multiplier
                    exit_status = "EXCEPTION" if exception_occurred else "EXIT"
                    log_event(
                        dec_name, exit_status, func.__name__,
                        f"[DURATION={elapsed:.{precision}f}{unit_name}]",
                        level=log_level_val if not exception_occurred else logging.WARNING
                    )
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, f"[UNIT={unit_name}]", level=log_level_val)
                
                start_time = time.perf_counter()
                exception_occurred = False
                
                try:
                    with with_nesting_level():
                        try:
                            result = func(*args, **kwargs)
                            return result
                        except Exception:
                            exception_occurred = True
                            raise
                finally:
                    elapsed = (time.perf_counter() - start_time) * multiplier
                    exit_status = "EXCEPTION" if exception_occurred else "EXIT"
                    log_event(
                        dec_name, exit_status, func.__name__,
                        f"[DURATION={elapsed:.{precision}f}{unit_name}]",
                        level=log_level_val if not exception_occurred else logging.WARNING
                    )
            
            return wrapper
    
    return decorator


def catch(exceptions: Tuple[Type[Exception], ...] = (Exception,), 
          default: Any = None, 
          reraise: bool = False,
          log_error: bool = True) -> Callable:
    
    dec_name = "catch"
    
    def decorator(func: Callable) -> Callable:
        
        if is_async_func(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, f"[CATCHING={[e.__name__ for e in exceptions]}]")
                
                exception_occurred = False
                caught_exception = False
                
                try:
                    with with_nesting_level():
                        try:
                            result = await func(*args, **kwargs)
                            return result
                        except exceptions as e:
                            caught_exception = True
                            if log_error:
                                log_event(
                                    dec_name, "CAUGHT", func.__name__,
                                    f"{type(e).__name__}: {e} -> DEFAULT={default}",
                                    level=logging.ERROR
                                )
                            
                            if reraise:
                                log_event(dec_name, "RERAISE", func.__name__, level=logging.WARNING)
                                exception_occurred = True
                                raise
                            
                            return default
                        except Exception:
                            exception_occurred = True
                            raise
                finally:
                    if caught_exception and not reraise:
                        log_event(dec_name, "EXIT", func.__name__, f"[RETURNED_DEFAULT={default}]", level=logging.INFO)
                    elif exception_occurred:
                        log_event(dec_name, "EXCEPTION", func.__name__, level=logging.ERROR)
                    else:
                        log_event(dec_name, "EXIT", func.__name__, level=logging.INFO)
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                log_event(dec_name, "ENTER", func.__name__, f"[CATCHING={[e.__name__ for e in exceptions]}]")
                
                exception_occurred = False
                caught_exception = False
                
                try:
                    with with_nesting_level():
                        try:
                            result = func(*args, **kwargs)
                            return result
                        except exceptions as e:
                            caught_exception = True
                            if log_error:
                                log_event(
                                    dec_name, "CAUGHT", func.__name__,
                                    f"{type(e).__name__}: {e} -> DEFAULT={default}",
                                    level=logging.ERROR
                                )
                            
                            if reraise:
                                log_event(dec_name, "RERAISE", func.__name__, level=logging.WARNING)
                                exception_occurred = True
                                raise
                            
                            return default
                        except Exception:
                            exception_occurred = True
                            raise
                finally:
                    if caught_exception and not reraise:
                        log_event(dec_name, "EXIT", func.__name__, f"[RETURNED_DEFAULT={default}]", level=logging.INFO)
                    elif exception_occurred:
                        log_event(dec_name, "EXCEPTION", func.__name__, level=logging.ERROR)
                    else:
                        log_event(dec_name, "EXIT", func.__name__, level=logging.INFO)
            
            return wrapper
    
    return decorator


def rate_limit(max_calls: int = 10, 
               time_window: float = 60.0,
               wait: bool = False,
               on_limit: Optional[Callable] = None,
               mode: str = "auto") -> Callable:
    
    if mode == "reject":
        wait = False
    elif mode == "wait":
        wait = True
    
    rate_limit_states: Dict[int, RateLimitState] = {}
    dec_name = "rate_limit"
    
    def decorator(func: Callable) -> Callable:
        func_id = id(func)
        is_async = is_async_func(func)
        
        if func_id not in rate_limit_states:
            rate_limit_states[func_id] = RateLimitState(
                max_calls=max_calls,
                time_window=time_window
            )
        
        state = rate_limit_states[func_id]
        lock = state.get_lock(is_async)
        mode_str = "WAIT" if wait else "REJECT"
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                current_time = time.time()
                allowed_to_proceed = False
                current_count = 0
                
                async with lock:
                    state.calls = [t for t in state.calls if current_time - t < state.time_window]
                    current_count = len(state.calls)
                    
                    log_event(
                        dec_name, "CHECK", func.__name__,
                        f"[CURRENT={current_count}/{state.max_calls} WINDOW={state.time_window}s MODE={mode_str}]"
                    )
                    
                    if current_count >= state.max_calls:
                        if wait:
                            oldest_call = state.calls[0]
                            wait_time = state.time_window - (current_time - oldest_call)
                            
                            if wait_time > 0:
                                log_event(
                                    dec_name, "LIMITED", func.__name__,
                                    f"[THROTTLED] Need to wait {wait_time:.3f}s for next slot...",
                                    level=logging.WARNING
                                )
                                log_event(
                                    dec_name, "WAITING", func.__name__,
                                    f"[SLEEP_START] wait_time={wait_time:.3f}s",
                                    level=logging.WARNING
                                )
                                
                                await asyncio.sleep(wait_time)
                                
                                current_time = time.time()
                                state.calls = [t for t in state.calls if current_time - t < state.time_window]
                                
                                log_event(
                                    dec_name, "RELEASED", func.__name__,
                                    f"[SLEEP_END] Waited {wait_time:.3f}s, now allowed to proceed",
                                    level=logging.INFO
                                )
                                
                                state.calls.append(current_time)
                                remaining = max(0, state.max_calls - len(state.calls))
                                log_event(
                                    dec_name, "ALLOWED", func.__name__,
                                    f"[PROCEED] Used: {len(state.calls)}/{state.max_calls}, Remaining: {remaining}/{state.max_calls}"
                                )
                                allowed_to_proceed = True
                        else:
                            if on_limit is not None:
                                log_event(
                                    dec_name, "LIMITED", func.__name__,
                                    f"[REJECTED] Calling on_limit callback",
                                    level=logging.WARNING
                                )
                                if is_async_func(on_limit):
                                    return await on_limit(*args, **kwargs)
                                else:
                                    return on_limit(*args, **kwargs)
                            
                            log_event(
                                dec_name, "LIMITED", func.__name__,
                                f"[REJECTED] Exceeded {state.max_calls}/{state.time_window}s - Raising RateLimitExceededError",
                                level=logging.WARNING
                            )
                            raise RateLimitExceededError(
                                f"Function '{func.__name__}' exceeded rate limit: "
                                f"{state.max_calls} calls per {state.time_window} seconds"
                            )
                    else:
                        state.calls.append(current_time)
                        remaining = max(0, state.max_calls - len(state.calls))
                        log_event(
                            dec_name, "ALLOWED", func.__name__,
                            f"[PROCEED] Used: {len(state.calls)}/{state.max_calls}, Remaining: {remaining}/{state.max_calls}"
                        )
                        allowed_to_proceed = True
                
                if allowed_to_proceed:
                    with with_nesting_level():
                        return await func(*args, **kwargs)
                else:
                    raise RateLimitExceededError(
                        f"Function '{func.__name__}' exceeded rate limit"
                    )
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                current_time = time.time()
                allowed_to_proceed = False
                
                with lock:
                    state.calls = [t for t in state.calls if current_time - t < state.time_window]
                    current_count = len(state.calls)
                    
                    log_event(
                        dec_name, "CHECK", func.__name__,
                        f"[CURRENT={current_count}/{state.max_calls} WINDOW={state.time_window}s MODE={mode_str}]"
                    )
                    
                    if current_count >= state.max_calls:
                        if wait:
                            oldest_call = state.calls[0]
                            wait_time = state.time_window - (current_time - oldest_call)
                            
                            if wait_time > 0:
                                log_event(
                                    dec_name, "LIMITED", func.__name__,
                                    f"[THROTTLED] Need to wait {wait_time:.3f}s for next slot...",
                                    level=logging.WARNING
                                )
                                log_event(
                                    dec_name, "WAITING", func.__name__,
                                    f"[SLEEP_START] wait_time={wait_time:.3f}s",
                                    level=logging.WARNING
                                )
                                
                                time.sleep(wait_time)
                                
                                current_time = time.time()
                                state.calls = [t for t in state.calls if current_time - t < state.time_window]
                                
                                log_event(
                                    dec_name, "RELEASED", func.__name__,
                                    f"[SLEEP_END] Waited {wait_time:.3f}s, now allowed to proceed",
                                    level=logging.INFO
                                )
                                
                                state.calls.append(current_time)
                                remaining = max(0, state.max_calls - len(state.calls))
                                log_event(
                                    dec_name, "ALLOWED", func.__name__,
                                    f"[PROCEED] Used: {len(state.calls)}/{state.max_calls}, Remaining: {remaining}/{state.max_calls}"
                                )
                                allowed_to_proceed = True
                        else:
                            if on_limit is not None:
                                log_event(
                                    dec_name, "LIMITED", func.__name__,
                                    f"[REJECTED] Calling on_limit callback",
                                    level=logging.WARNING
                                )
                                return on_limit(*args, **kwargs)
                            
                            log_event(
                                dec_name, "LIMITED", func.__name__,
                                f"[REJECTED] Exceeded {state.max_calls}/{state.time_window}s - Raising RateLimitExceededError",
                                level=logging.WARNING
                            )
                            raise RateLimitExceededError(
                                f"Function '{func.__name__}' exceeded rate limit: "
                                f"{state.max_calls} calls per {state.time_window} seconds"
                            )
                    else:
                        state.calls.append(current_time)
                        remaining = max(0, state.max_calls - len(state.calls))
                        log_event(
                            dec_name, "ALLOWED", func.__name__,
                            f"[PROCEED] Used: {len(state.calls)}/{state.max_calls}, Remaining: {remaining}/{state.max_calls}"
                        )
                        allowed_to_proceed = True
                
                if allowed_to_proceed:
                    with with_nesting_level():
                        return func(*args, **kwargs)
                else:
                    raise RateLimitExceededError(
                        f"Function '{func.__name__}' exceeded rate limit"
                    )
            
            return wrapper
    
    return decorator


class RateLimitExceededError(Exception):
    pass


def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff: float = 1.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    
    dec_name = "retry"
    
    def decorator(func: Callable) -> Callable:
        
        if is_async_func(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                current_delay = delay
                last_exception = None
                
                log_event(dec_name, "ENTER", func.__name__, f"[MAX_ATTEMPTS={max_attempts}]")
                
                try:
                    for attempt in range(1, max_attempts + 1):
                        log_event(
                            dec_name, "ATTEMPT", func.__name__,
                            f"[{attempt}/{max_attempts}]"
                        )
                        
                        with with_nesting_level():
                            try:
                                result = await func(*args, **kwargs)
                                if attempt > 1:
                                    log_event(
                                        dec_name, "SUCCESS", func.__name__,
                                        f"[SUCCEEDED_ON={attempt}/{max_attempts}]",
                                        level=logging.INFO
                                    )
                                return result
                            except exceptions as e:
                                last_exception = e
                                if attempt < max_attempts:
                                    log_event(
                                        dec_name, "FAILED", func.__name__,
                                        f"[ATTEMPT={attempt}/{max_attempts}] {type(e).__name__}: {e} -> RETRY_AFTER={current_delay:.2f}s",
                                        level=logging.WARNING
                                    )
                                    await asyncio.sleep(current_delay)
                                    current_delay *= backoff
                                else:
                                    log_event(
                                        dec_name, "GAVE_UP", func.__name__,
                                        f"[ALL_{max_attempts}_ATTEMPTS_FAILED] Last: {type(e).__name__}: {e}",
                                        level=logging.ERROR
                                    )
                    
                    raise last_exception
                finally:
                    log_event(dec_name, "EXIT", func.__name__)
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not global_chain_id.get():
                    global_chain_id.set(generate_chain_id())
                
                current_delay = delay
                last_exception = None
                
                log_event(dec_name, "ENTER", func.__name__, f"[MAX_ATTEMPTS={max_attempts}]")
                
                try:
                    for attempt in range(1, max_attempts + 1):
                        log_event(
                            dec_name, "ATTEMPT", func.__name__,
                            f"[{attempt}/{max_attempts}]"
                        )
                        
                        with with_nesting_level():
                            try:
                                result = func(*args, **kwargs)
                                if attempt > 1:
                                    log_event(
                                        dec_name, "SUCCESS", func.__name__,
                                        f"[SUCCEEDED_ON={attempt}/{max_attempts}]",
                                        level=logging.INFO
                                    )
                                return result
                            except exceptions as e:
                                last_exception = e
                                if attempt < max_attempts:
                                    log_event(
                                        dec_name, "FAILED", func.__name__,
                                        f"[ATTEMPT={attempt}/{max_attempts}] {type(e).__name__}: {e} -> RETRY_AFTER={current_delay:.2f}s",
                                        level=logging.WARNING
                                    )
                                    time.sleep(current_delay)
                                    current_delay *= backoff
                                else:
                                    log_event(
                                        dec_name, "GAVE_UP", func.__name__,
                                        f"[ALL_{max_attempts}_ATTEMPTS_FAILED] Last: {type(e).__name__}: {e}",
                                        level=logging.ERROR
                                    )
                    
                    raise last_exception
                finally:
                    log_event(dec_name, "EXIT", func.__name__)
            
            return wrapper
    
    return decorator


def reset_chain_context():
    global_chain_id.set("")
    decorator_nesting_level.set(0)
