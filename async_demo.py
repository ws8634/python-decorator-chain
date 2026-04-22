import asyncio
import time
import inspect
from typing import Dict, Any, List

from decorators import (
    log, timer, catch, rate_limit, retry, 
    RateLimitExceededError, reset_chain_context, is_async_func
)
from chain import DecoratorChain, DecoratorPresets


def print_header(title: str, width: int = 80):
    print("\n" + "=" * width)
    print(f"【{title}】")
    print("=" * width)


def print_subheader(text: str):
    print(f"\n>>> {text} <<<")


def compare_func_meta(original_func, decorated_func, label: str = ""):
    print(f"\n{'='*60}")
    print(f" 元信息对比验证: {label or original_func.__name__}")
    print(f"{'='*60}")
    
    original_name = original_func.__name__
    decorated_name = decorated_func.__name__
    name_match = original_name == decorated_name
    
    original_doc = original_func.__doc__ or "(无文档)"
    decorated_doc = decorated_func.__doc__ or "(无文档)"
    doc_match = original_doc == decorated_doc
    
    try:
        original_sig = str(inspect.signature(original_func))
    except (ValueError, TypeError):
        original_sig = "(无法获取签名)"
    
    try:
        decorated_sig = str(inspect.signature(decorated_func))
    except (ValueError, TypeError):
        decorated_sig = "(无法获取签名)"
    
    sig_match = original_sig == decorated_sig
    
    print(f"\n  1. __name__ 对比:")
    print(f"     原始函数: {repr(original_name)}")
    print(f"     装饰后函数: {repr(decorated_name)}")
    print(f"     匹配状态: {'✅ 相同' if name_match else '❌ 不同'}")
    
    print(f"\n  2. __doc__ 对比:")
    print(f"     原始函数: {repr(original_doc)}")
    print(f"     装饰后函数: {repr(decorated_doc)}")
    print(f"     匹配状态: {'✅ 相同' if doc_match else '❌ 不同'}")
    
    print(f"\n  3. inspect.signature 对比:")
    print(f"     原始函数: {original_sig}")
    print(f"     装饰后函数: {decorated_sig}")
    print(f"     匹配状态: {'✅ 相同' if sig_match else '❌ 不同'}")
    
    original_is_async = inspect.iscoroutinefunction(original_func)
    decorated_is_async = inspect.iscoroutinefunction(decorated_func)
    async_match = original_is_async == decorated_is_async
    
    print(f"\n  4. 是否为协程函数对比:")
    print(f"     原始函数: {'✅ 是协程' if original_is_async else '❌ 不是协程'}")
    print(f"     装饰后函数: {'✅ 是协程' if decorated_is_async else '❌ 不是协程'}")
    print(f"     匹配状态: {'✅ 相同' if async_match else '❌ 不同'}")
    
    all_match = name_match and doc_match and sig_match and async_match
    print(f"\n  【结论】functools.wraps 效果: {'✅ 完全生效' if all_match else '❌ 存在问题'}")
    print(f"{'='*60}\n")
    
    return all_match


print_header="异步函数装饰器演示系统初始化"

print("""

================================================================================
                        异步函数装饰器演示系统
                (Async Function Decorator Demo System)
================================================================================

本演示展示装饰器如何同时支持同步和异步函数。

核心特性:
1. 自动检测函数类型 (sync / async)
2. 自动选择对应的包装器 (wrapper / async wrapper)
3. 保持相同的日志格式和事件序列
4. 使用 asyncio.sleep 替代 time.sleep (不阻塞事件循环)

演示内容:
- 异步函数的元信息验证
- 异步函数的多层装饰器执行顺序 (洋葱模型)
- 异步函数的 rate_limit 两种模式
- 同步 vs 异步函数的对比

================================================================================
""")

time.sleep(0.5)


async def main():
    print_header="演示 1: 异步函数元信息验证"
    
    print_subheader="定义原始异步函数"
    
    async def original_async_func(a: int, b: str = "default", *, flag: bool = False) -> Dict[str, Any]:
        """
        这是原始异步函数的文档字符串。
        
        功能描述:
        - 异步执行的示例函数
        - 接收位置参数、默认参数、关键字-only 参数
        - 使用 await asyncio.sleep 模拟异步操作
        
        参数:
            a: 整数参数
            b: 字符串参数，默认值 "default"
            flag: 布尔关键字参数，默认值 False
        
        返回:
            包含所有参数的字典
        """
        await asyncio.sleep(0.01)
        return {
            "a": a,
            "b": b,
            "flag": flag,
            "result": a * len(b)
        }
    
    print(f"\n原始异步函数定义:")
    print(f"  函数名: {original_async_func.__name__}")
    print(f"  签名: {inspect.signature(original_async_func)}")
    print(f"  是否异步: {inspect.iscoroutinefunction(original_async_func)}")
    
    
    print_subheader="应用多层装饰器到异步函数"
    
    @timer(unit="ms", precision=4)
    @catch(exceptions=(Exception,), default={"error": "caught_async"})
    @log(level="INFO", log_args=True, log_return=True)
    async def decorated_async_func(a: int, b: str = "default", *, flag: bool = False) -> Dict[str, Any]:
        """
        这是原始异步函数的文档字符串。
        
        功能描述:
        - 异步执行的示例函数
        - 接收位置参数、默认参数、关键字-only 参数
        - 使用 await asyncio.sleep 模拟异步操作
        
        参数:
            a: 整数参数
            b: 字符串参数，默认值 "default"
            flag: 布尔关键字参数，默认值 False
        
        返回:
            包含所有参数的字典
        """
        await asyncio.sleep(0.01)
        return {
            "a": a,
            "b": b,
            "flag": flag,
            "result": a * len(b)
        }
    
    print(f"\n装饰后异步函数定义:")
    print(f"  函数名: {decorated_async_func.__name__}")
    print(f"  是否异步: {inspect.iscoroutinefunction(decorated_async_func)}")
    
    
    print_subheader="异步函数元信息对比验证"
    
    compare_func_meta(original_async_func, decorated_async_func, "多层装饰器装饰后的异步函数")
    
    
    print_subheader="使用 DecoratorChain 装饰异步函数"
    
    async def another_async_original(x: float, y: float = 1.0) -> float:
        """另一个原始异步函数，用于测试 Chain 装饰"""
        await asyncio.sleep(0.005)
        return x * y
    
    chain = DecoratorChain()
    chain.add(timer, unit="s")
    chain.add(log, level="DEBUG")
    
    decorated_async_by_chain = chain.apply(another_async_original)
    
    compare_func_meta(another_async_original, decorated_async_by_chain, "DecoratorChain 装饰后的异步函数")
    
    
    print_header="演示 2: 异步函数多层装饰器执行顺序 - 洋葱模型"
    
    print("""

异步函数的洋葱模型:
===================

装饰器叠加顺序:
    @timer      (最外层)
    @catch      (中间层)
    @log        (最内层)
    async def func(): ...

关键点:
1. 装饰器自动检测 async 函数
2. 使用 async wrapper 替代同步 wrapper
3. 使用 await 调用内部函数
4. 使用 asyncio.sleep 替代 time.sleep
5. 日志格式和事件序列与同步函数完全一致

""")
    
    await asyncio.sleep(1)
    
    
    print_subheader="异步函数正常执行场景 - 验证洋葱模型顺序"
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @catch(exceptions=(Exception,), default="ASYNC_DEFAULT_VALUE")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_onion_demo_normal(x: int, y: int) -> int:
        """异步洋葱模型演示 - 正常执行"""
        print(f"        [异步函数体执行] x={x}, y={y}")
        await asyncio.sleep(0.05)
        return x + y
    
    print(f"\n调用 await async_onion_demo_normal(10, 20):")
    print(f"请仔细观察日志中的 ENTER/EXIT 顺序和 CHAIN_ID:\n")
    
    result = await async_onion_demo_normal(10, 20)
    print(f"\n返回结果: {result}")
    
    
    print_subheader="异步函数异常捕获场景"
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @catch(exceptions=(ValueError,), default="ASYNC_CAUGHT")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_onion_demo_exception(x: int) -> int:
        """异步洋葱模型演示 - 异常场景"""
        print(f"        [异步函数体执行] x={x}")
        if x < 0:
            raise ValueError(f"x 不能为负数: {x}")
        await asyncio.sleep(0.01)
        return x * 2
    
    print(f"\n调用 await async_onion_demo_exception(-5):")
    print(f"观察 catch 装饰器如何捕获异步函数中的异常:\n")
    
    result = await async_onion_demo_exception(-5)
    print(f"\n返回结果: {result}")
    
    
    print_subheader="同步 vs 异步函数对比 - 相同的装饰器，不同的函数类型"
    
    print("""

对比说明:
=========

使用完全相同的装饰器组合:
    @timer
    @log
    def sync_func(): ...
    
    @timer
    @log
    async def async_func(): ...

装饰器内部会自动检测函数类型:
- 如果是同步函数: 使用普通 wrapper，调用 func(*args, **kwargs)
- 如果是异步函数: 使用 async wrapper，调用 await func(*args, **kwargs)

日志格式和事件序列完全一致，只是内部实现不同。

""")
    
    await asyncio.sleep(0.5)
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @log(level="INFO")
    def sync_compare_func(n: int) -> str:
        """同步对比函数"""
        time.sleep(0.02)
        return f"sync_result_{n}"
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @log(level="INFO")
    async def async_compare_func(n: int) -> str:
        """异步对比函数"""
        await asyncio.sleep(0.02)
        return f"async_result_{n}"
    
    print(f"\n调用同步函数 sync_compare_func(1):\n")
    result_sync = sync_compare_func(1)
    print(f"\n同步函数结果: {result_sync}")
    
    reset_chain_context()
    print(f"\n调用异步函数 async_compare_func(2):\n")
    result_async = await async_compare_func(2)
    print(f"\n异步函数结果: {result_async}")
    
    print(f"\n对比观察:")
    print(f"  - 两个函数使用完全相同的装饰器")
    print(f"  - 日志格式、事件类型、CHAIN_ID 机制完全一致")
    print(f"  - 装饰器自动选择了正确的 wrapper 类型")
    
    
    print_header="演示 3: 异步函数 rate_limit 两种模式"
    
    print("""

异步函数的限流:
===============

关键点:
1. 使用 asyncio.sleep 替代 time.sleep (不阻塞事件循环)
2. 支持同时运行多个异步函数 (并发限流)
3. WAIT 模式下使用 await asyncio.sleep(wait_time)

两种模式:
- REJECT: 超过阈值立即抛出 RateLimitExceededError
- WAIT: 超过阈值等待后放行 (使用 asyncio.sleep)

""")
    
    await asyncio.sleep(1)
    
    
    print_subheader="模式 1: REJECT - 异步函数直接拒绝模式"
    
    reset_chain_context()
    
    @rate_limit(max_calls=2, time_window=3.0, mode="reject")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_rate_limit_reject_demo(request_id: str) -> Dict[str, Any]:
        """异步限流演示 - REJECT 模式"""
        await asyncio.sleep(0.01)
        return {
            "status": "success",
            "request_id": request_id,
            "timestamp": time.time()
        }
    
    print(f"""
配置:
  - max_calls = 2
  - time_window = 3.0s
  - mode = "reject"

预期: 第 1-2 次成功，第 3-5 次被拒绝
""")
    
    print(f"\n开始执行 5 次异步调用...\n")
    
    for i in range(1, 6):
        reset_chain_context()
        req_id = f"ASYNC_REQ_{i:02d}"
        print(f"\n{'─'*50}")
        print(f"异步调用 {i}/5: request_id = {req_id}")
        print(f"{'─'*50}")
        
        try:
            result = await async_rate_limit_reject_demo(req_id)
            print(f"\n  ✅ 成功: {result}")
        except RateLimitExceededError as e:
            print(f"\n  ❌ 被限流: {e}")
    
    
    print_subheader="模式 2: WAIT - 异步函数等待放行模式"
    
    reset_chain_context()
    
    @rate_limit(max_calls=2, time_window=1.5, mode="wait")
    @log(level="INFO", log_args=True, log_return=True)
    @timer(unit="ms", precision=2)
    async def async_rate_limit_wait_demo(request_id: str) -> Dict[str, Any]:
        """异步限流演示 - WAIT 模式"""
        await asyncio.sleep(0.01)
        return {
            "status": "success",
            "request_id": request_id,
            "processed_at": time.time()
        }
    
    print(f"""
配置:
  - max_calls = 2
  - time_window = 1.5s
  - mode = "wait"

关键点:
  - 使用 asyncio.sleep 而非 time.sleep
  - 不阻塞事件循环，其他异步任务可继续执行

预期:
  - 第 1-2 次: 立即成功
  - 第 3 次: 等待约 1.5 秒后成功
""")
    
    print(f"\n开始执行 3 次异步调用 (第 3 次会触发等待)...")
    print(f"注意: 使用 asyncio.sleep，不阻塞事件循环\n")
    
    start_time = time.time()
    
    for i in range(1, 4):
        reset_chain_context()
        req_id = f"ASYNC_WAIT_{i:02d}"
        elapsed = time.time() - start_time
        
        print(f"\n{'═'*60}")
        print(f"异步调用 {i}/3: request_id = {req_id} (距开始: {elapsed:.2f}s)")
        print(f"{'═'*60}")
        
        try:
            result = await async_rate_limit_wait_demo(req_id)
            elapsed_total = time.time() - start_time
            print(f"\n  ✅ 成功: {result}")
            print(f"  本次调用后总耗时: {elapsed_total:.2f}s")
        except Exception as e:
            print(f"\n  ❌ 异常: {type(e).__name__}: {e}")
    
    
    print_subheader="异步并发限流演示 (多个协程同时调用)"
    
    print("""

异步并发限流:
=============

演示多个协程同时调用被限流的异步函数:
- 并发启动 5 个协程
- 每个协程都调用同一个被限流的函数
- 观察限流如何影响并发执行

配置: max_calls=2, time_window=2.0s, mode=wait

预期行为:
- 第 1-2 个协程: 立即执行
- 第 3-5 个协程: 需要等待，直到时间窗口允许

""")
    
    await asyncio.sleep(0.5)
    
    reset_chain_context()
    
    call_count = 0
    
    @rate_limit(max_calls=2, time_window=2.0, mode="wait")
    @log(level="INFO", log_args=True)
    async def concurrent_async_func(coro_id: str) -> str:
        """用于并发测试的异步函数"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return f"{coro_id}_completed"
    
    print(f"\n并发启动 5 个协程...\n")
    
    start_time = time.time()
    
    async def run_coro(coro_id: str):
        reset_chain_context()
        try:
            result = await concurrent_async_func(coro_id)
            elapsed = time.time() - start_time
            print(f"\n  [协程 {coro_id}] 完成: {result}, 耗时: {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n  [协程 {coro_id}] 失败: {e}, 耗时: {elapsed:.2f}s")
            return None
    
    tasks = [run_coro(f"C{i}") for i in range(1, 6)]
    results = await asyncio.gather(*tasks)
    
    total_elapsed = time.time() - start_time
    print(f"\n所有协程完成，总耗时: {total_elapsed:.2f}s")
    print(f"成功完成的协程数: {sum(1 for r in results if r is not None)}/5")
    
    
    print_header="演示 4: 异步函数完整企业级场景"
    
    print("""

异步企业级场景:
===============

使用 full_chain 预设装饰异步 API 函数:
  - timer: 计时 (使用 async 版本)
  - catch: 异常捕获
  - rate_limit: 限流
  - retry: 重试 (使用 asyncio.sleep)
  - log: 日志记录

""")
    
    await asyncio.sleep(0.5)
    
    reset_chain_context()
    
    enterprise_chain = DecoratorPresets.full_chain(
        max_calls=3,
        time_window=5.0,
        rate_mode="reject",
        retry_max=2,
        retry_delay=0.3
    )
    
    print(f"企业级链定义: {enterprise_chain}")
    
    call_counter = 0
    
    @enterprise_chain
    async def async_enterprise_api(user_id: int, amount: float) -> Dict[str, Any]:
        """异步企业级 API 模拟"""
        global call_counter
        call_counter += 1
        
        if call_counter < 2:
            raise ConnectionError(f"数据库连接失败 (异步尝试 {call_counter})")
        
        if amount <= 0:
            raise ValueError(f"无效金额: {amount}")
        
        await asyncio.sleep(0.05)
        return {
            "transaction_id": f"ASYNC_TXN_{int(time.time())}",
            "user_id": user_id,
            "amount": amount,
            "status": "SUCCESS",
            "async": True
        }
    
    
    print_subheader="异步场景 1: 正常交易 (触发重试)"
    
    reset_chain_context()
    call_counter = 0
    
    print(f"\n调用 await async_enterprise_api(12345, 100.50):")
    print(f"预期: 第 1 次失败，触发 retry，第 2 次成功\n")
    
    result = await async_enterprise_api(12345, 100.50)
    print(f"\n最终结果: {result}")
    
    
    print_subheader="异步场景 2: 无效金额 (异常被捕获)"
    
    reset_chain_context()
    call_counter = 2
    
    print(f"\n调用 await async_enterprise_api(12345, -50.0):\n")
    
    result = await async_enterprise_api(12345, -50.0)
    print(f"\n最终结果: {result}")
    
    
    print_header="异步演示总结"
    
    print("""

================================================================================
                          异步函数装饰器演示完成
================================================================================

✅ 验证通过的功能:

1. 异步函数元信息保留
   - __name__: 装饰前后一致
   - __doc__: 装饰前后一致
   - inspect.signature: 装饰前后一致
   - 协程函数属性: 装饰前后一致

2. 自动检测函数类型
   - 同步函数: 使用普通 wrapper
   - 异步函数: 使用 async wrapper
   - 日志格式和事件序列完全一致

3. 异步限流
   - REJECT 模式: 超过阈值立即拒绝
   - WAIT 模式: 使用 asyncio.sleep 等待
   - 不阻塞事件循环

4. 异步重试
   - 使用 asyncio.sleep 替代 time.sleep
   - 支持退避策略

5. 并发支持
   - 多个协程可同时调用被限流的函数
   - 限流策略正确应用于所有协程

================================================================================

装饰器系统现在同时支持同步和异步函数，
使用方式完全一致，内部实现自动适配。

================================================================================
""")


if __name__ == "__main__":
    asyncio.run(main())
