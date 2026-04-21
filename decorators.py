import functools
import time
import logging
import uuid
from typing import Any, Callable, Optional, Type, Tuple, List, Dict
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DecoratorSystem")


@dataclass
class RateLimitState:
    calls: List[float] = field(default_factory=list)
    max_calls: int = 10
    time_window: float = 60.0


def log(level: str = "INFO", log_args: bool = True, log_return: bool = True, 
        log_time: bool = True) -> Callable:
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            call_id = str(uuid.uuid4())[:8]
            start_time = time.time()
            
            log_parts = [f"[CALL_ID: {call_id}] [FUNCTION: {func.__name__}]"]
            
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
                    f"[EXCEPTION: {type(e).__name__}: {e}] [ELAPSED: {elapsed:.4f}s]"
                )
                raise
        
        return wrapper
    return decorator


def timer(unit: str = "ms", precision: int = 4, log_level: str = "INFO") -> Callable:
    
    valid_units = {"s": 1.0, "ms": 1000.0, "us": 1000000.0}
    multiplier = valid_units.get(unit.lower(), 1000.0)
    unit_name = unit.lower()
    
    log_level_val = getattr(logging, log_level.upper(), logging.INFO)
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
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
        
        return wrapper
    return decorator


def catch(exceptions: Tuple[Type[Exception], ...] = (Exception,), 
          default: Any = None, 
          reraise: bool = False,
          log_error: bool = True) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
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
        
        return wrapper
    return decorator


def rate_limit(max_calls: int = 10, 
               time_window: float = 60.0,
               wait: bool = False,
               on_limit: Optional[Callable] = None) -> Callable:
    
    rate_limit_states: Dict[int, RateLimitState] = {}
    
    def decorator(func: Callable) -> Callable:
        func_id = id(func)
        
        if func_id not in rate_limit_states:
            rate_limit_states[func_id] = RateLimitState(
                max_calls=max_calls,
                time_window=time_window
            )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            state = rate_limit_states[func_id]
            current_time = time.time()
            
            state.calls = [t for t in state.calls if current_time - t < state.time_window]
            
            if len(state.calls) >= state.max_calls:
                if wait:
                    oldest_call = state.calls[0]
                    wait_time = state.time_window - (current_time - oldest_call)
                    if wait_time > 0:
                        logger.warning(
                            f"[RATE_LIMIT] [FUNCTION: {func.__name__}] "
                            f"Rate limit exceeded ({state.max_calls}/{state.time_window}s). "
                            f"Waiting {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        current_time = time.time()
                        state.calls = [t for t in state.calls if current_time - t < state.time_window]
                else:
                    if on_limit is not None:
                        return on_limit(*args, **kwargs)
                    
                    logger.warning(
                        f"[RATE_LIMIT] [FUNCTION: {func.__name__}] "
                        f"Rate limit exceeded ({state.max_calls}/{state.time_window}s). "
                        f"Call rejected."
                    )
                    raise RateLimitExceededError(
                        f"Function '{func.__name__}' exceeded rate limit: "
                        f"{state.max_calls} calls per {state.time_window} seconds"
                    )
            
            state.calls.append(current_time)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class RateLimitExceededError(Exception):
    pass


def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff: float = 1.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
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
        
        return wrapper
    return decorator
