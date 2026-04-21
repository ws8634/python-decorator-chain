from typing import Any, Callable, List, Optional, Union, Dict, Tuple
import functools
import inspect


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
        dec_names = [dec.__name__ for dec, _, _ in self._decorators]
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
    
    @staticmethod
    def from_config(config: Any) -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit, retry, monitor
        
        chain = DecoratorChain()
        
        if hasattr(config, 'log') and config.log and config.log.enabled:
            chain.add(
                log,
                level=config.log.level,
                log_args=config.log.log_args,
                log_return=config.log.log_return,
                log_time=config.log.log_time,
                log_context=getattr(config.log, 'log_context', True)
            )
        
        if hasattr(config, 'timer') and config.timer and config.timer.enabled:
            chain.add(
                timer,
                unit=config.timer.unit,
                precision=config.timer.precision,
                log_level=config.timer.log_level
            )
        
        if hasattr(config, 'catch') and config.catch and config.catch.enabled:
            chain.add(
                catch,
                exceptions=config.catch.exceptions,
                default=config.catch.default,
                reraise=config.catch.reraise,
                log_error=config.catch.log_error
            )
        
        if hasattr(config, 'rate_limit') and config.rate_limit and config.rate_limit.enabled:
            chain.add(
                rate_limit,
                max_calls=config.rate_limit.max_calls,
                time_window=config.rate_limit.time_window,
                wait=config.rate_limit.wait,
                thread_safe=getattr(config.rate_limit, 'thread_safe', True),
                process_safe=getattr(config.rate_limit, 'process_safe', False)
            )
        
        if hasattr(config, 'retry') and config.retry and config.retry.enabled:
            chain.add(
                retry,
                max_attempts=config.retry.max_attempts,
                delay=config.retry.delay,
                backoff=config.retry.backoff,
                exceptions=config.retry.exceptions
            )
        
        if hasattr(config, 'monitor') and config.monitor and config.monitor.enabled:
            chain.add(
                monitor,
                name=config.monitor.name,
                track_calls=config.monitor.track_calls,
                track_errors=config.monitor.track_errors,
                track_latency=config.monitor.track_latency,
                track_exceptions=config.monitor.track_exceptions,
                histogram_bins=config.monitor.histogram_bins
            )
        
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
            log(level="INFO", log_args=True, log_return=True, log_time=True, log_context=True)
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
    def api_chain(max_calls: int = 100, 
                  time_window: float = 60.0,
                  thread_safe: bool = True,
                  process_safe: bool = False) -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit
        return DecoratorChain(
            timer(unit="ms", precision=3),
            catch(exceptions=(Exception,), default={"error": "Internal Server Error"}, log_error=True),
            rate_limit(max_calls=max_calls, time_window=time_window, 
                       thread_safe=thread_safe, process_safe=process_safe),
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
    def monitored_chain(monitor_name: Optional[str] = None) -> DecoratorChain:
        from decorators import log, timer, monitor
        chain = DecoratorChain(
            timer(unit="ms", precision=3),
            monitor(name=monitor_name),
            log(level="INFO", log_args=False, log_return=False)
        )
        return chain
    
    @staticmethod
    def full_enterprise_chain(max_calls: int = 100,
                               time_window: float = 60.0,
                               max_attempts: int = 3,
                               monitor_name: Optional[str] = None,
                               thread_safe: bool = True,
                               process_safe: bool = False) -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit, retry, monitor
        
        return DecoratorChain(
            timer(unit="ms", precision=3),
            catch(exceptions=(Exception,), default={"error": "Service Unavailable"}, log_error=True),
            rate_limit(max_calls=max_calls, time_window=time_window,
                       thread_safe=thread_safe, process_safe=process_safe),
            retry(max_attempts=max_attempts, delay=0.5, backoff=1.5),
            monitor(name=monitor_name),
            log(level="INFO", log_args=True, log_return=True, log_context=True)
        )
    
    @staticmethod
    def async_api_chain(max_calls: int = 100,
                        time_window: float = 60.0,
                        thread_safe: bool = True) -> DecoratorChain:
        from decorators import log, timer, catch, rate_limit, monitor
        
        return DecoratorChain(
            timer(unit="ms", precision=3),
            catch(exceptions=(Exception,), default={"error": "Async API Error"}, log_error=True),
            rate_limit(max_calls=max_calls, time_window=time_window, thread_safe=thread_safe),
            monitor(name="async_api"),
            log(level="INFO", log_context=True)
        )
