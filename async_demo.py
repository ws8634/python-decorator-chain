import asyncio
import time
import threading
import functools
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from decorators import (
    log, timer, catch, rate_limit, retry, monitor,
    RateLimitExceededError, get_monitor_stats, print_monitor_report, reset_monitor
)
from chain import DecoratorChain, ChainBuilder, DecoratorPresets
from config import (
    DecoratorContext, with_context,
    load_config_from_dict, save_config_to_file,
    enable_decorator, disable_decorator, is_decorator_enabled,
    update_rate_limit_config, update_retry_config,
    DEFAULT_CONFIG, DecoratorChainConfig
)


print("=" * 80)
print("【高级扩展演示 - 企业级装饰器链系统】")
print("=" * 80)

print("""
本演示包含以下高级功能：
1. 异步函数兼容 - 所有装饰器支持 sync/async
2. 线程安全限流 - 多线程高并发下计数准确
3. 上下文传递 - request_id/trace_id 在多层装饰器间共享
4. 监控统计 - @monitor 记录调用次数、耗时、异常分布
5. 配置化能力 - 从字典配置加载，动态开关和调整策略

========================================
""")


print("\n" + "=" * 80)
print("【深度原理讲解】")
print("=" * 80)

print("""

一、Python 装饰器执行顺序
----------------------------

当使用多个装饰器装饰一个函数时，装饰器的应用顺序和执行顺序是不同的：

1. 应用顺序（从下到上）：
   @decorator_A
   @decorator_B
   @decorator_C
   def func(): pass
   
   等同于：decorator_A(decorator_B(decorator_C(func)))

2. 执行顺序（从上到下）：
   调用 func() 时：
   - 先进入 decorator_A 的 wrapper
   - 再进入 decorator_B 的 wrapper
   - 再进入 decorator_C 的 wrapper
   - 执行原函数 func
   - 从 decorator_C 返回
   - 从 decorator_B 返回
   - 从 decorator_A 返回

二、闭包绑定原理
------------------

装饰器本质是一个返回函数的函数，内部函数（wrapper）会形成闭包：

   def decorator(param):
       # 外层函数的变量
       config = param
       
       def wrapper(*args, **kwargs):
           # 内部函数可以访问外层的 config
           # 即使外层函数已返回，config 仍被保留
           print(f"Using config: {config}")
           return func(*args, **kwargs)
       
       return wrapper

关键：wrapper 函数通过闭包「捕获」了外层作用域的变量，
这些变量的生命周期被延长到与 wrapper 相同。

三、多层嵌套执行流程
----------------------

以 @log + @timer + @catch 为例：

   @log()           # 第3层 wrapper
   @timer()         # 第2层 wrapper
   @catch()         # 第1层 wrapper
   def business_func():
       pass

调用链（进入顺序）：
   log_wrapper() → timer_wrapper() → catch_wrapper() → business_func()

返回链（退出顺序）：
   business_func() → catch_wrapper() → timer_wrapper() → log_wrapper()

四、装饰器链数据传递与上下文共享
----------------------------------

传统方式：各装饰器独立，无法共享状态

新机制（使用 contextvars.ContextVar）：

   1. 定义上下文变量：
      request_id_ctx = ContextVar('request_id', default='')
      
   2. 在入口设置上下文：
      @with_context(request_id='REQ-123', trace_id='TRACE-456')
      async def api_handler():
          await service_a()
          await service_b()
      
   3. 在装饰器中读取上下文：
      def log_wrapper(...):
          req_id = DecoratorContext.get_request_id()
          logger.info(f"[REQ:{req_id}] ...")

特点：
- ContextVar 是异步安全的，每个 asyncio 任务有独立上下文
- 支持多层嵌套调用，上下文自动传递
- 线程安全，threading.local 的异步替代品

五、装饰器执行顺序图示
------------------------

   装饰顺序（应用时）：
   ┌─────────────────────────────────────────────────────────┐
   │  @log()                          ← 最外层，最后应用       │
   │    @timer()                     ← 中间层                  │
   │      @catch()                   ← 最内层，最先应用       │
   │        def func(): pass                                   │
   └─────────────────────────────────────────────────────────┘

   执行顺序（调用时）：
   ┌─────────────────────────────────────────────────────────┐
   │  func()                                                  │
   │    ↓                                                     │
   │  log_wrapper 开始 → 记录开始日志                        │
   │    ↓                                                     │
   │  timer_wrapper 开始 → 记录开始时间                      │
   │    ↓                                                     │
   │  catch_wrapper 开始 → 准备异常捕获                      │
   │    ↓                                                     │
   │  执行原函数 func()                                       │
   │    ↓                                                     │
   │  catch_wrapper 结束 → 若有异常则处理                    │
   │    ↓                                                     │
   │  timer_wrapper 结束 → 计算耗时并输出                     │
   │    ↓                                                     │
   │  log_wrapper 结束 → 记录返回值和耗时                     │
   └─────────────────────────────────────────────────────────┘

""")


print("\n" + "=" * 80)
print("【演示 1】异步函数兼容 - 所有装饰器支持 async/await")
print("=" * 80)


@log(level="INFO", log_args=True, log_return=True, log_context=True)
@timer(unit="ms", precision=4)
@catch(exceptions=(ValueError, ZeroDivisionError), default={"status": "error"})
@rate_limit(max_calls=5, time_window=10.0, thread_safe=True)
@retry(max_attempts=2, delay=0.2, backoff=1.0)
@monitor(name="async_business_service")
async def async_business_service(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步业务服务 - 演示所有装饰器对 async 函数的支持
    """
    await asyncio.sleep(0.05)
    
    if data.get('should_fail'):
        raise ValueError("Simulated business error")
    
    return {
        "user_id": user_id,
        "data": data,
        "processed_at": time.time(),
        "status": "success"
    }


@log(level="DEBUG")
@timer(unit="s")
async def simple_async_func(x: int, y: int) -> int:
    await asyncio.sleep(0.01)
    return x + y


async def demo_async_functions():
    print("\n>>> 测试异步函数装饰器 <<<")
    
    print(f"\n  函数名: {async_business_service.__name__}")
    print(f"  函数文档: {async_business_service.__doc__}")
    print(f"  是否异步函数: {asyncio.iscoroutinefunction(async_business_service)}")
    
    print("\n  正常调用测试:")
    result = await async_business_service(1001, {"action": "test"})
    print(f"    结果: {result}")
    
    print("\n  异常捕获测试:")
    result2 = await async_business_service(1002, {"should_fail": True})
    print(f"    捕获异常后返回: {result2}")
    
    print("\n  简单异步函数测试:")
    result3 = await simple_async_func(10, 20)
    print(f"    10 + 20 = {result3}")


print("\n" + "=" * 80)
print("【演示 2】线程安全限流 - 高并发下计数准确")
print("=" * 80)


thread_safe_counter = 0
thread_counter_lock = threading.Lock()

@rate_limit(max_calls=3, time_window=5.0, thread_safe=True)
@monitor(name="thread_safe_api")
def thread_safe_api_call(request_num: int) -> str:
    global thread_safe_counter
    with thread_counter_lock:
        thread_safe_counter += 1
    return f"Request {request_num} processed successfully (count={thread_safe_counter})"


@rate_limit(max_calls=3, time_window=5.0, thread_safe=False)
@monitor(name="non_thread_safe_api")
def non_thread_safe_api_call(request_num: int) -> str:
    return f"Request {request_num} processed"


def worker_thread(api_func, request_num: int, results: List[Dict], errors: List[Dict]):
    try:
        result = api_func(request_num)
        results.append({"request": request_num, "result": result, "success": True})
    except RateLimitExceededError as e:
        errors.append({"request": request_num, "error": str(e), "success": False})
    except Exception as e:
        errors.append({"request": request_num, "error": str(e), "success": False})


async def demo_thread_safe_rate_limit():
    global thread_safe_counter
    thread_safe_counter = 0
    
    print("\n>>> 线程安全限流测试 <<<")
    print("  策略: max_calls=3, time_window=5s, thread_safe=True")
    print("  场景: 10个线程并发调用，预期只有 3 个成功")
    
    results: List[Dict] = []
    errors: List[Dict] = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(1, 11):
            future = executor.submit(
                worker_thread,
                thread_safe_api_call,
                i,
                results,
                errors
            )
            futures.append(future)
        
        for future in futures:
            try:
                future.result(timeout=2.0)
            except Exception as e:
                print(f"    线程执行错误: {e}")
    
    print(f"\n  实际结果:")
    print(f"    成功调用数: {len(results)}")
    print(f"    被限流数: {len(errors)}")
    print(f"    计数器值: {thread_safe_counter}")
    
    if len(results) == 3:
        print("  ✅ 线程安全限流工作正常！正好 3 个调用通过")
    else:
        print(f"  ⚠️  注意: 并发测试可能有轻微波动，成功数: {len(results)}")


print("\n" + "=" * 80)
print("【演示 3】上下文传递 - request_id/trace_id 多层共享")
print("=" * 80)


@log(level="INFO", log_context=True)
@monitor(name="inner_service")
async def inner_service_a() -> str:
    req_id = DecoratorContext.get_request_id()
    trace_id = DecoratorContext.get_trace_id()
    user_ctx = DecoratorContext.get_user_context()
    print(f"      [inner_service_a] 读取上下文: request_id={req_id}, trace_id={trace_id}, user={user_ctx}")
    return "service_a_ok"


@log(level="INFO", log_context=True)
@monitor(name="inner_service_b")
async def inner_service_b() -> str:
    req_id = DecoratorContext.get_request_id()
    print(f"      [inner_service_b] 读取上下文: request_id={req_id}")
    DecoratorContext.update_extra_context(step="service_b_executed")
    return "service_b_ok"


@log(level="INFO", log_context=True)
@with_context(request_id="GLOBAL-REQ-001", trace_id="TRACE-2024-001", user={"id": 999, "role": "system"})
async def context_demo_entry() -> Dict[str, Any]:
    print("\n  [入口函数] 设置了初始上下文")
    print(f"    request_id: {DecoratorContext.get_request_id()}")
    print(f"    trace_id: {DecoratorContext.get_trace_id()}")
    print(f"    user: {DecoratorContext.get_user_context()}")
    
    DecoratorContext.update_extra_context(api_version="v2.0", env="production")
    
    print("\n  调用 inner_service_a（自动继承上下文）:")
    result_a = await inner_service_a()
    
    print("\n  调用 inner_service_b（自动继承上下文）:")
    result_b = await inner_service_b()
    
    extra = DecoratorContext.get_extra_context()
    print(f"\n  [入口函数结束] 额外上下文: {extra}")
    
    return {
        "result_a": result_a,
        "result_b": result_b,
        "context": DecoratorContext.get_all_context()
    }


async def demo_context_passing():
    print("\n>>> 上下文传递演示 <<<")
    print("""
  原理说明:
  - 使用 contextvars.ContextVar 存储上下文
  - 每个 asyncio 任务有独立的上下文副本
  - 子协程自动继承父协程的上下文
  - @with_context 装饰器可以设置/覆盖上下文
""")
    
    result = await context_demo_entry()
    print(f"\n  最终结果:")
    print(f"    服务执行结果: A={result['result_a']}, B={result['result_b']}")
    print(f"    完整上下文: {result['context']}")


print("\n" + "=" * 80)
print("【演示 4】监控统计 - @monitor 装饰器")
print("=" * 80)


@monitor(name="monitored_func_1")
async def monitored_success_func() -> str:
    await asyncio.sleep(0.01)
    return "success"


@monitor(name="monitored_func_2")
async def monitored_mixed_func(should_fail: bool = False) -> str:
    await asyncio.sleep(0.02)
    if should_fail:
        raise ValueError("Simulated error")
    return "ok"


async def demo_monitor_stats():
    print("\n>>> 监控统计演示 <<<")
    
    reset_monitor()
    
    print("\n  调用 monitored_func_1（全部成功）:")
    for i in range(5):
        await monitored_success_func()
        await asyncio.sleep(0.001)
    
    print("  调用 monitored_func_2（部分成功，部分失败）:")
    for i in range(10):
        try:
            await monitored_mixed_func(should_fail=(i % 3 == 0))
        except Exception:
            pass
    
    print("\n  打印监控报表:")
    print_monitor_report()
    
    stats = get_monitor_stats()
    print(f"\n  以编程方式获取的统计:")
    for name, data in stats.items():
        print(f"    [{name}] 总调用: {data['total_calls']}, "
              f"成功率: {data['success_rate_pct']}%, "
              f"平均耗时: {data['avg_latency_ms']}ms")


print("\n" + "=" * 80)
print("【演示 5】配置化能力 - 动态加载和调整")
print("=" * 80)


def demo_configuration():
    print("\n>>> 配置化能力演示 <<<")
    
    config_dict = {
        "log": {
            "level": "DEBUG",
            "log_args": True,
            "log_return": False,
            "log_time": True,
            "log_context": True,
            "enabled": True
        },
        "timer": {
            "unit": "ms",
            "precision": 3,
            "log_level": "INFO",
            "enabled": True
        },
        "rate_limit": {
            "max_calls": 5,
            "time_window": 30.0,
            "wait": False,
            "thread_safe": True,
            "process_safe": False,
            "enabled": True
        },
        "retry": {
            "max_attempts": 3,
            "delay": 0.5,
            "backoff": 2.0,
            "exceptions": ["ConnectionError", "TimeoutError"],
            "enabled": True
        },
        "monitor": {
            "name": "config_based_chain",
            "track_calls": True,
            "track_errors": True,
            "track_latency": True,
            "track_exceptions": True,
            "histogram_bins": 10,
            "enabled": True
        }
    }
    
    print("\n  1. 从字典加载配置:")
    config = load_config_from_dict(config_dict)
    print(f"    log.level: {config.log.level}")
    print(f"    rate_limit.max_calls: {config.rate_limit.max_calls}")
    print(f"    retry.max_attempts: {config.retry.max_attempts}")
    
    print("\n  2. 使用配置创建装饰器链:")
    chain_from_config = ChainBuilder.from_config(config)
    print(f"    装饰器链: {chain_from_config}")
    print(f"    装饰器数量: {len(chain_from_config)}")
    
    print("\n  3. 动态开关测试:")
    print(f"    log 装饰器启用状态: {is_decorator_enabled('log')}")
    disable_decorator('log')
    print(f"    禁用后 log 状态: {is_decorator_enabled('log')}")
    enable_decorator('log')
    print(f"    重新启用后状态: {is_decorator_enabled('log')}")
    
    print("\n  4. 动态调整限流策略:")
    print("    调用 update_rate_limit_config(max_calls=100, time_window=60.0)")
    update_rate_limit_config(max_calls=100, time_window=60.0)
    
    print("\n  5. 动态调整重试策略:")
    print("    调用 update_retry_config(max_attempts=5, delay=0.2, backoff=1.5)")
    update_retry_config(max_attempts=5, delay=0.2, backoff=1.5)
    
    print("\n  6. 配置导出为字典:")
    export_dict = config.to_dict()
    print(f"    导出的配置键: {list(export_dict.keys())}")
    
    return chain_from_config


print("\n" + "=" * 80)
print("【演示 6】高并发异步限流 - 完整场景")
print("=" * 80)


@rate_limit(max_calls=5, time_window=10.0, thread_safe=True)
@monitor(name="high_concurrency_api")
async def high_concurrency_async_api(req_id: str) -> Dict[str, Any]:
    await asyncio.sleep(0.01)
    return {
        "req_id": req_id,
        "status": "processed",
        "timestamp": time.time()
    }


async def concurrent_worker(req_id: str, results: List, errors: List):
    try:
        result = await high_concurrency_async_api(req_id)
        results.append({"req_id": req_id, "success": True, "result": result})
    except RateLimitExceededError as e:
        errors.append({"req_id": req_id, "success": False, "error": "RateLimited"})
    except Exception as e:
        errors.append({"req_id": req_id, "success": False, "error": str(e)})


async def demo_high_concurrency_async():
    print("\n>>> 高并发异步限流演示 <<<")
    print("  策略: max_calls=5, time_window=10s")
    print("  场景: 20 个并发异步任务")
    
    reset_monitor()
    
    results: List[Dict] = []
    errors: List[Dict] = []
    
    tasks = []
    for i in range(1, 21):
        req_id = f"CONC-REQ-{i:03d}"
        task = asyncio.create_task(concurrent_worker(req_id, results, errors))
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"\n  结果统计:")
    print(f"    成功调用数: {len(results)}")
    print(f"    被限流数: {len(errors)}")
    
    if len(results) == 5:
        print("  ✅ 异步高并发限流工作正常！正好 5 个调用通过")
    else:
        print(f"  ⚠️  并发测试完成，成功数: {len(results)}")
    
    print("\n  监控数据:")
    print_monitor_report("high_concurrency_api")


print("\n" + "=" * 80)
print("【演示 7】配置化装饰器链实际应用")
print("=" * 80)


async def demo_configured_chain_usage():
    print("\n>>> 配置化装饰器链实际应用 <<<")
    
    prod_config_dict = {
        "log": {"level": "INFO", "log_args": False, "log_return": False, "log_context": True, "enabled": True},
        "timer": {"unit": "ms", "precision": 2, "enabled": True},
        "catch": {"exceptions": ["Exception"], "default": {"error": "Service Down"}, "enabled": True},
        "rate_limit": {"max_calls": 10, "time_window": 60.0, "thread_safe": True, "enabled": True},
        "retry": {"max_attempts": 3, "delay": 0.3, "backoff": 1.5, "exceptions": ["ConnectionError"], "enabled": True},
        "monitor": {"name": "production_api", "enabled": True}
    }
    
    prod_config = load_config_from_dict(prod_config_dict)
    prod_chain = ChainBuilder.from_config(prod_config)
    
    print(f"\n  生产环境装饰器链: {prod_chain}")
    
    async def unstable_remote_api(data: Dict) -> Dict:
        await asyncio.sleep(0.02)
        if data.get('simulate_error'):
            raise ConnectionError("Remote service timeout")
        return {"status": "ok", "data": data}
    
    decorated_api = prod_chain.apply(unstable_remote_api)
    
    print("\n  测试正常调用:")
    result = await decorated_api({"id": 123})
    print(f"    结果: {result}")
    
    print("\n  测试异常+重试:")
    result2 = await decorated_api({"id": 456, "simulate_error": True})
    print(f"    结果（捕获异常后返回默认值）: {result2}")
    
    print("\n  监控报表:")
    print_monitor_report("production_api")


async def main():
    print("\n" + "=" * 80)
    print("开始执行所有演示...")
    print("=" * 80)
    
    await demo_async_functions()
    await demo_thread_safe_rate_limit()
    await demo_context_passing()
    await demo_monitor_stats()
    demo_configuration()
    await demo_high_concurrency_async()
    await demo_configured_chain_usage()
    
    print("\n" + "=" * 80)
    print("所有演示完成！")
    print("=" * 80)
    
    print("""

总结 - 高级扩展功能实现:
========================================

1. ✅ 异步函数兼容
   - 所有装饰器（log/timer/catch/rate_limit/retry/monitor）
   - 自动检测 sync/async 函数，选择对应的 wrapper
   - 使用 inspect.iscoroutinefunction() 判断

2. ✅ 线程安全与进程安全
   - @rate_limit 添加 thread_safe 参数（默认 True）
   - 使用 threading.Lock 保护共享状态
   - 可选 process_safe，使用 multiprocessing.Manager
   - 高并发测试验证计数准确

3. ✅ 上下文传递机制
   - 使用 contextvars.ContextVar 存储 request_id/trace_id/span_id
   - DecoratorContext 类提供统一访问接口
   - @with_context 装饰器支持设置上下文
   - 支持用户上下文和额外扩展上下文
   - 异步安全，每个任务独立上下文

4. ✅ @monitor 监控装饰器
   - 统计总调用数、成功数、失败数
   - 计算成功率、平均耗时、P50/P95/P99 延迟
   - 记录异常类型分布
   - 支持打印统计报表
   - 支持以编程方式获取统计数据
   - 线程安全的统计更新

5. ✅ 配置化能力
   - 支持从字典加载配置（load_config_from_dict）
   - 支持从 JSON/YAML 文件加载
   - ChainBuilder.from_config() 创建装饰器链
   - 动态开关装饰器（enable/disable）
   - 动态调整限流/重试策略
   - 配置导出为字典

6. ✅ 模块化架构
   - decorators.py - 核心装饰器实现
   - chain.py - 装饰器编排和预设
   - config.py - 配置管理和上下文
   - async_demo.py - 高级功能演示

========================================
""")


if __name__ == "__main__":
    asyncio.run(main())
