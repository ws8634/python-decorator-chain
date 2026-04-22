from typing import Any, Callable, List, Optional, Union, Dict, Tuple
import functools
import inspect


def is_async_func(func: Callable) -> bool:
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


class DecoratorChain:
    def __init__(self, *decorators: Callable):
        self._decorators: List[Tuple[Callable, Tuple, Dict]] = []
        for dec in decorators:
            self._decorators.append((dec, (), {}))
    
    def add(self, decorator: Callable, *args, **kwargs) -> 'DecoratorChain':
        self._decorators.append((decorator, args, kwargs))
        return self
    
    def add_before(self, decorator: Callable, *args, **kwargs) -> 'DecoratorChain':
        self._decorators.insert(0, (decorator, args, kwargs))
        return self
    
    def add_after(self, decorator: Callable, *args, **kwargs) -> 'DecoratorChain':
        self._decorators.append((decorator, args, kwargs))
        return self
    
    def insert_at(self, index: int, decorator: Callable, *args, **kwargs) -> 'DecoratorChain':
        if index < 0:
            index = max(0, len(self._decorators) + index + 1)
        else:
            index = min(index, len(self._decorators))
        self._decorators.insert(index, (decorator, args, kwargs))
        return self
    
    def remove(self, index: int) -> 'DecoratorChain':
        if 0 <= index < len(self._decorators):
            self._decorators.pop(index)
        return self
    
    def clear(self) -> 'DecoratorChain':
        self._decorators.clear()
        return self
    
    def copy(self) -> 'DecoratorChain':
        new_chain = DecoratorChain()
        new_chain._decorators = list(self._decorators)
        return new_chain
    
    def apply(self, func: Callable) -> Callable:
        result = func
        for decorator, args, kwargs in reversed(self._decorators):
            if args or kwargs:
                result = decorator(*args, **kwargs)(result)
            else:
                result = decorator(result)
        return result
    
    def __call__(self, func: Callable) -> Callable:
        return self.apply(func)
    
    def apply_batch(self, *funcs: Callable) -> List[Callable]:
        return [self.apply(func) for func in funcs]
    
    def decorate_module(self, module: Any, 
                        predicate: Optional[Callable[[Callable], bool]] = None,
                        exclude_names: Optional[List[str]] = None) -> Dict[str, Callable]:
        decorated = {}
        exclude_names = exclude_names or []
        
        for name, obj in inspect.getmembers(module):
            if name.startswith('_'):
                continue
            if name in exclude_names:
                continue
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                if predicate is None or predicate(obj):
                    decorated[name] = self.apply(obj)
        
        return decorated
    
    def __len__(self) -> int:
        return len(self._decorators)
    
    def __repr__(self) -> str:
        dec_names = []
        for dec, args, kwargs in self._decorators:
            name = getattr(dec, '__name__', str(dec))
            if args or kwargs:
                params = []
                if args:
                    params.extend(str(a) for a in args)
                if kwargs:
                    params.extend(f"{k}={v}" for k, v in kwargs.items())
                name = f"{name}({', '.join(params)})"
            dec_names.append(name)
        return f"DecoratorChain({', '.join(dec_names)})"


class ChainBuilder:
    @staticmethod
    def create() -> DecoratorChain:
        return DecoratorChain()
    
    @staticmethod
    def from_list(decorators: List[Tuple[Callable, Tuple, Dict]]) -> DecoratorChain:
        chain = DecoratorChain()
        for decorator, args, kwargs in decorators:
            chain.add(decorator, *args, **kwargs)
        return chain


def combine(*decorators: Callable) -> Callable:
    def decorator(func: Callable) -> Callable:
        result = func
        for dec in reversed(decorators):
            result = dec(result)
        return result
    return decorator


class DecoratorPresets:
    @staticmethod
    def logging_chain() -> DecoratorChain:
        from decorators import log, timer
        return DecoratorChain(
            timer(unit="ms", precision=4),
            log(level="INFO", log_args=True, log_return=True, log_time=True)
        )
    
    @staticmethod
    def safe_execution_chain() -> DecoratorChain:
        from decorators import log, catch, timer
        return DecoratorChain(
            timer(unit="ms"),
            catch(exceptions=(Exception,), default=None, log_error=True),
            log(level="INFO")
        )
    
    @staticmethod
    def api_chain(max_calls: int = 100, time_window: float = 60.0, mode: str = "reject") -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit
        return DecoratorChain(
            timer(unit="ms", precision=3),
            catch(exceptions=(Exception,), default={"error": "Internal Server Error"}, log_error=True),
            rate_limit(max_calls=max_calls, time_window=time_window, mode=mode),
            log(level="INFO", log_args=True, log_return=True)
        )
    
    @staticmethod
    def resilient_chain(max_attempts: int = 3, 
                         delay: float = 1.0,
                         backoff: float = 2.0) -> DecoratorChain:
        from decorators import log, timer, catch, retry
        return DecoratorChain(
            timer(unit="ms"),
            catch(exceptions=(Exception,), default=None),
            retry(max_attempts=max_attempts, delay=delay, backoff=backoff),
            log(level="INFO")
        )
    
    @staticmethod
    def full_chain(max_calls: int = 10, 
                   time_window: float = 60.0,
                   rate_mode: str = "reject",
                   retry_max: int = 3,
                   retry_delay: float = 0.5) -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit, retry
        return DecoratorChain(
            timer(unit="ms", precision=3),
            catch(exceptions=(Exception,), default=None, log_error=True),
            rate_limit(max_calls=max_calls, time_window=time_window, mode=rate_mode),
            retry(max_attempts=retry_max, delay=retry_delay, backoff=1.5),
            log(level="INFO", log_args=True, log_return=True, log_time=True)
        )
