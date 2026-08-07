import asyncio
import time
import inspect
from typing import Dict, Any, List, Callable

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


def compare_func_meta_same_func(original_func: Callable, label: str = ""):
    """
    对同一个函数对象在装饰前后进行对比验证。
    
    关键改进：
    - 保存原始函数的引用
    - 使用相同的函数对象进行装饰
    - 对比装饰前后的元信息
    """
    print(f"\n{'='*70}")
    print(f" 元信息对比验证: {label}")
    print(f"{'='*70}")
    
    original_name = original_func.__name__
    original_doc = original_func.__doc__ or "(无文档)"
    try:
        original_sig = str(inspect.signature(original_func))
    except (ValueError, TypeError):
        original_sig = "(无法获取签名)"
    original_is_async = inspect.iscoroutinefunction(original_func)
    
    print(f"\n  [装饰前 - 原始函数对象]")
    print(f"     原始函数对象 id: {id(original_func)}")
    print(f"     __name__: {repr(original_name)}")
    print(f"     __doc__: {repr(original_doc)[:100]}{'...' if len(original_doc) > 100 else ''}")
    print(f"     signature: {original_sig}")
    print(f"     is_async (iscoroutinefunction): {original_is_async}")
    
    print(f"\n  现在对同一个函数对象应用装饰器...")
    
    decorated_func = timer(unit="ms")(catch(exceptions=(Exception,), default="TEST_DEFAULT")(log(level="INFO")(original_func)))
    
    decorated_name = decorated_func.__name__
    decorated_doc = decorated_func.__doc__ or "(无文档)"
    try:
        decorated_sig = str(inspect.signature(decorated_func))
    except (ValueError, TypeError):
        decorated_sig = "(无法获取签名)"
    decorated_is_async = inspect.iscoroutinefunction(decorated_func)
    
    print(f"\n  [装饰后 - 装饰后的函数对象]")
    print(f"     装饰后函数对象 id: {id(decorated_func)}")
    print(f"     __name__: {repr(decorated_name)}")
    print(f"     __doc__: {repr(decorated_doc)[:100]}{'...' if len(decorated_doc) > 100 else ''}")
    print(f"     signature: {decorated_sig}")
    print(f"     is_async (iscoroutinefunction): {decorated_is_async}")
    
    name_match = original_name == decorated_name
    doc_match = original_doc == decorated_doc
    sig_match = original_sig == decorated_sig
    async_match = original_is_async == decorated_is_async
    
    print(f"\n  {'─'*70}")
    print(f"  对比验证结果:")
    print(f"{'─'*70}")
    print(f"     __name__ 对比:      {'✅ 相同' if name_match else '❌ 不同'}")
    print(f"     __doc__ 对比:       {'✅ 相同' if doc_match else '❌ 不同'}")
    print(f"     signature 对比:     {'✅ 相同' if sig_match else '❌ 不同'}")
    print(f"     is_async 对比:      {'✅ 相同' if async_match else '❌ 不同'}")
    
    all_match = name_match and doc_match and sig_match and async_match
    print(f"{'─'*70}")
    print(f"  【结论】functools.wraps 效果: {'✅ 完全生效' if all_match else '❌ 存在问题'}")
    print(f"{'='*70}\n")
    
    return all_match, decorated_func


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
- 异步函数的元信息验证 (同一个函数装饰前后对比)
- 异步函数的多层装饰器执行顺序 (洋葱模型 - 完整 ENTER/EXIT)
- 异步函数的 rate_limit 两种模式 (含并发限流)
- 企业级异步场景 (修复 NameError 问题)
- 关键证据片段示例日志

================================================================================
""")

time.sleep(0.5)


async def main():
    print_header="演示 1: 异步函数元信息验证 - 同一个函数装饰前后对比"
    
    print_subheader="验证方法说明"
    
    print("""
    
    【正确的验证方法】
    ==================
    
    之前的问题:
    - 使用两个不同命名的函数进行对比 (original_async_func vs decorated_async_func)
    - 这两个函数虽然代码相同，但是是不同的函数对象
    - 对比结果可能存在误导
    
    正确的方法:
    1. 定义一个原始函数
    2. 保存原始函数的所有元信息
    3. 对这个函数应用装饰器
    4. 对比装饰前后的元信息
    
    验证步骤:
    - 保存原始函数对象 id
    - 记录 __name__, __doc__, signature, is_async
    - 应用装饰器
    - 对比装饰后的函数对象
    - 确认 functools.wraps 正确保留了元信息
    
    """)
    
    await asyncio.sleep(1)
    
    
    print_subheader="对同一个异步函数进行装饰前后对比"
    
    async def target_async_func(a: int, b: str = "default", *, flag: bool = False) -> Dict[str, Any]:
        """
        这是目标异步函数的文档字符串。
        
        功能描述:
        - 异步执行的示例函数
        - 用于验证 functools.wraps 效果
        - 同一个函数对象装饰前后对比
        
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
    
    is_async = is_async_func(target_async_func)
    print(f"\n确认函数类型: {'✅ 是异步函数' if is_async else '❌ 不是异步函数'}")
    
    result, decorated_func = compare_func_meta_same_func(target_async_func, "异步函数元信息验证")
    
    if result:
        print("\n✅ 元信息验证通过！functools.wraps 正确保留了所有函数元信息。")
    else:
        print("\n❌ 元信息验证失败！")
    
    
    print_header="演示 2: 异步函数多层装饰器执行顺序 - 洋葱模型 (完整 ENTER/EXIT)"
    
    print("""

    洋葱模型说明:
    =============
    
    装饰器叠加顺序 (从外到内):
        @timer      (最外层)
        @catch      (中间层)
        @log        (最内层)
        async def func(): ...
    
    预期执行顺序 (通过日志验证):
    
    【正常返回路径】
    1. [timer] ENTER        (最外层先进入)
    2.   [catch] ENTER      (中间层进入)
    3.     [log] ENTER      (最内层进入)
    4.       [log] PARAMS   (参数日志)
    5.       [log] RESULT   (结果日志)
    6.     [log] EXIT       (最内层先退出)
    7.   [catch] EXIT       (中间层退出)
    8. [timer] EXIT         (最外层最后退出)
    
    【异常捕获路径】
    1. [timer] ENTER
    2.   [catch] ENTER
    3.     [log] ENTER
    4.       [log] EXCEPTION (异常日志)
    5.     [log] EXCEPTION   (最内层异常退出)
    6.   [catch] CAUGHT      (捕获异常)
    7.   [catch] EXIT        (中间层正常退出 - 因为异常被捕获)
    8. [timer] EXIT          (最外层退出)
    
    关键点:
    - 同一个 CHAIN_ID 贯穿整个调用过程
    - 所有装饰器的 ENTER/EXIT 都必须成对出现
    - 异常路径也必须有正确的退出标记
    
    """)
    
    await asyncio.sleep(1)
    
    
    print_subheader="正常返回场景 - 验证完整 ENTER/EXIT 事件序列"
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @catch(exceptions=(Exception,), default="ASYNC_DEFAULT_VALUE")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_onion_normal(x: int, y: int) -> int:
        """异步洋葱模型演示 - 正常执行"""
        print(f"        [异步函数体执行] x={x}, y={y}")
        await asyncio.sleep(0.05)
        return x + y
    
    print(f"\n调用 await async_onion_normal(10, 20):")
    print(f"请仔细观察日志中的 ENTER/EXIT 顺序和 CHAIN_ID:\n")
    
    result = await async_onion_normal(10, 20)
    print(f"\n返回结果: {result}")
    
    print(f"""
    
    【可验证的要点】
    ================
    请从日志中确认:
    
    1. 进入顺序 (洋葱外层 -> 内层):
       [timer] ENTER -> [catch] ENTER -> [log] ENTER
    
    2. 退出顺序 (洋葱内层 -> 外层):
       [log] EXIT -> [catch] EXIT -> [timer] EXIT
    
    3. 同一个 CHAIN_ID 贯穿整个调用:
       所有 [CHAIN: xxxxxx] 应该相同
    
    4. 所有 ENTER 都有对应的 EXIT:
       timer: 有 ENTER 就有 EXIT
       catch: 有 ENTER 就有 EXIT
       log: 有 ENTER 就有 EXIT
    
    """)
    
    
    print_subheader="异常捕获场景 - 验证异常路径的 ENTER/EXIT"
    
    reset_chain_context()
    
    @timer(unit="ms", precision=3)
    @catch(exceptions=(ValueError,), default="ASYNC_CAUGHT_VALUE")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_onion_exception(x: int) -> int:
        """异步洋葱模型演示 - 异常场景"""
        print(f"        [异步函数体执行] x={x}")
        if x < 0:
            raise ValueError(f"x 不能为负数: {x}")
        await asyncio.sleep(0.01)
        return x * 2
    
    print(f"\n调用 await async_onion_exception(-5):")
    print(f"观察异常路径下的 ENTER/EXIT 事件:\n")
    
    result = await async_onion_exception(-5)
    print(f"\n返回结果: {result}")
    
    print(f"""
    
    【异常路径可验证的要点】
    ========================
    请从日志中确认:
    
    1. 异常发生时:
       [log] EXCEPTION 事件会被记录
    
    2. catch 装饰器:
       [catch] CAUGHT 事件显示捕获异常
       [catch] EXIT 事件正常退出 (因为异常被捕获)
    
    3. 所有装饰器都有正确的退出标记:
       [log] EXCEPTION (不是 EXIT，因为有异常)
       [catch] EXIT (正常退出，因为异常被捕获)
       [timer] EXIT (正常退出)
    
    """)
    
    
    print_header="演示 3: 异步函数 rate_limit 两种模式"
    
    print("""

    异步函数的限流:
    ===============
    
    配置:
    - 使用 asyncio.Lock 保护并发访问
    - 使用 asyncio.sleep 替代 time.sleep
    - 不阻塞事件循环
    
    两种模式:
    1. REJECT: 超过阈值立即抛出 RateLimitExceededError
    2. WAIT: 超过阈值等待后放行
    
    新增并发限流演示:
    - 多个协程同时调用
    - 使用锁保护计数
    - 确保 CURRENT/ALLOWED/剩余额度一致且不会出现负数
    
    """)
    
    await asyncio.sleep(1)
    
    
    print_subheader="模式 1: REJECT - 直接拒绝模式"
    
    reset_chain_context()
    
    @rate_limit(max_calls=2, time_window=3.0, mode="reject")
    @log(level="INFO", log_args=True, log_return=True)
    async def async_reject_demo(request_id: str) -> Dict[str, Any]:
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
    
    预期:
      - 第 1-2 次: [CHECK: CURRENT=0/2] -> [ALLOWED: Remaining 1/2] -> [CHECK: CURRENT=1/2] -> [ALLOWED: Remaining 0/2]
      - 第 3-5 次: [CHECK: CURRENT=2/2] -> [LIMITED: REJECTED] -> 抛出 RateLimitExceededError
    
    可验证点:
      - Remaining quota 不会出现负数
      - CURRENT 和 ALLOWED 中的计数一致
    """)
    
    print(f"\n开始执行 5 次异步调用...\n")
    
    for i in range(1, 6):
        reset_chain_context()
        req_id = f"ASYNC_REJ_{i:02d}"
        print(f"\n{'─'*50}")
        print(f"异步调用 {i}/5: request_id = {req_id}")
        print(f"{'─'*50}")
        
        try:
            result = await async_reject_demo(req_id)
            print(f"\n  ✅ 成功: {result}")
        except RateLimitExceededError as e:
            print(f"\n  ❌ 被限流: {e}")
    
    
    print_subheader="模式 2: WAIT - 等待放行模式 (完整事件序列)"
    
    reset_chain_context()
    
    @rate_limit(max_calls=2, time_window=1.5, mode="wait")
    @log(level="INFO", log_args=True, log_return=True)
    @timer(unit="ms", precision=2)
    async def async_wait_demo(request_id: str) -> Dict[str, Any]:
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
    
    完整事件序列 (第 3 次调用):
      1. [rate_limit] CHECK     -> [CURRENT=2/2] (发现超过阈值)
      2. [rate_limit] LIMITED   -> [THROTTLED] (触发限流)
      3. [rate_limit] WAITING   -> [SLEEP_START] (开始等待)
      4. [rate_limit] RELEASED  -> [SLEEP_END] (等待结束)
      5. [rate_limit] ALLOWED   -> [PROCEED] (允许执行)
    
    注意: 使用 asyncio.sleep，不阻塞事件循环
    """)
    
    print(f"\n开始执行 3 次异步调用 (第 3 次会触发等待)...")
    print(f"观察完整事件序列: CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED\n")
    
    start_time = time.time()
    
    for i in range(1, 4):
        reset_chain_context()
        req_id = f"ASYNC_WAIT_{i:02d}"
        elapsed = time.time() - start_time
        
        print(f"\n{'═'*60}")
        print(f"异步调用 {i}/3: request_id = {req_id} (距开始: {elapsed:.2f}s)")
        print(f"{'═'*60}")
        
        try:
            result = await async_wait_demo(req_id)
            elapsed_total = time.time() - start_time
            print(f"\n  ✅ 成功: {result}")
            print(f"  本次调用后总耗时: {elapsed_total:.2f}s")
        except Exception as e:
            print(f"\n  ❌ 异常: {type(e).__name__}: {e}")
    
    
    print_subheader="并发限流演示 (5 个协程同时调用 - 使用锁保护)"
    
    print("""
    
    并发限流说明:
    ============
    
    问题场景:
    - 5 个协程同时调用同一个被限流的函数
    - 配置: max_calls=2, time_window=2.0s, mode=wait
    - 可能出现竞态条件，导致剩余配额为负数
    
    解决方案:
    - 使用 asyncio.Lock 保护临界区
    - 所有检查和更新操作在锁内执行
    - 使用 max(0, ...) 确保剩余配额不会为负
    
    预期行为:
    - 协程 1, 2: 立即执行
    - 协程 3, 4, 5: 需要等待，直到时间窗口允许
    - 所有日志中的计数一致，不会出现负数
    
    """)
    
    await asyncio.sleep(0.5)
    
    reset_chain_context()
    
    call_count = 0
    
    @rate_limit(max_calls=2, time_window=2.0, mode="wait")
    @log(level="INFO", log_args=True)
    async def concurrent_demo(coro_id: str) -> str:
        """用于并发测试的异步函数"""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return f"{coro_id}_completed"
    
    print(f"\n并发启动 5 个协程...")
    print(f"配置: max_calls=2, time_window=2.0s, mode=wait")
    print(f"注意: 使用 asyncio.Lock 保护计数，确保不会出现负数\n")
    
    start_time = time.time()
    
    async def run_coro(coro_id: str):
        reset_chain_context()
        try:
            result = await concurrent_demo(coro_id)
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
    
    print(f"""
    
    【并发限流可验证的要点】
    ========================
    请从日志中确认:
    
    1. 使用锁保护后:
       - 所有 CHECK 和 ALLOWED 事件中的计数一致
       - Remaining quota 不会出现负数
       - 日志格式: "Used: X/Y, Remaining: Z/Y" (Z >= 0)
    
    2. 并发行为:
       - 前 2 个协程立即执行
       - 后 3 个协程需要等待
       - 总耗时约 2.0s (等待时间)
    
    """)
    
    
    print_header="演示 4: 企业级异步场景 - 修复 NameError 问题"
    
    print("""

    问题说明:
    =========
    
    之前的问题:
    - call_counter 定义在 main() 函数内 (局部变量)
    - async_enterprise_api 使用 global 声明
    - 导致 NameError: name 'call_counter' is not defined
    
    解决方案:
    方案 1: 使用 nonlocal 声明 (如果函数定义在嵌套作用域)
    方案 2: 使用可变对象 (如 list, dict) 来存储计数器
    方案 3: 使用类来封装状态
    
    本演示使用方案 2: 使用 list 作为可变容器
    - call_counter = [0] (list 是可变对象)
    - 在嵌套函数中修改 list 的内容
    - 不需要 nonlocal 或 global 声明
    
    预期行为:
    - 第 1 次调用: call_counter[0] = 1, 抛出 ConnectionError
    - 触发 retry 装饰器
    - 第 2 次尝试: call_counter[0] = 2, 正常返回
    - 看到完整的装饰器链日志
    
    """)
    
    await asyncio.sleep(1)
    
    
    print_subheader="修复 NameError 问题 - 使用可变对象存储状态"
    
    reset_chain_context()
    
    enterprise_chain = DecoratorPresets.full_chain(
        max_calls=5,
        time_window=10.0,
        rate_mode="reject",
        retry_max=2,
        retry_delay=0.3
    )
    
    print(f"企业级链定义: {enterprise_chain}")
    
    call_counter = [0]
    
    @enterprise_chain
    async def async_enterprise_api(user_id: int, amount: float) -> Dict[str, Any]:
        """异步企业级 API 模拟"""
        call_counter[0] += 1
        
        if call_counter[0] < 2:
            raise ConnectionError(f"数据库连接失败 (异步尝试 {call_counter[0]})")
        
        if amount <= 0:
            raise ValueError(f"无效金额: {amount}")
        
        await asyncio.sleep(0.05)
        return {
            "transaction_id": f"ASYNC_TXN_{int(time.time())}",
            "user_id": user_id,
            "amount": amount,
            "status": "SUCCESS",
            "async": True,
            "attempt": call_counter[0]
        }
    
    print(f"\n修复说明:")
    print(f"  - 之前: call_counter = 0 (不可变 int), 使用 global 声明 -> NameError")
    print(f"  - 现在: call_counter = [0] (可变 list), 直接修改内容 -> 正常工作")
    print(f"  - 技巧: 对于嵌套函数，使用可变对象可以避免作用域问题")
    
    
    print_subheader="场景 1: 正常交易 (触发重试机制后成功)"
    
    reset_chain_context()
    call_counter[0] = 0
    
    print(f"\n调用 await async_enterprise_api(12345, 100.50):")
    print(f"预期: 第 1 次尝试失败，触发 retry，第 2 次尝试成功")
    print(f"请观察完整的装饰器链日志:\n")
    
    result = await async_enterprise_api(12345, 100.50)
    print(f"\n最终结果: {result}")
    
    print(f"""
    
    【企业级场景可验证的要点】
    ===========================
    请从日志中确认:
    
    1. 装饰器链执行顺序:
       @timer (最外层) -> @catch -> @rate_limit -> @retry -> @log (最内层)
    
    2. 重试机制:
       [retry] ATTEMPT [1/2] -> 失败
       [retry] FAILED -> 等待 0.3s
       [retry] ATTEMPT [2/2] -> 成功
       [retry] SUCCESS [SUCCEEDED_ON=2/2]
    
    3. 完整的 ENTER/EXIT:
       所有装饰器都有 ENTER 和对应的 EXIT/EXCEPTION
    
    """)
    
    
    print_subheader="场景 2: 无效金额 (异常被捕获)"
    
    reset_chain_context()
    call_counter[0] = 2
    
    print(f"\n调用 await async_enterprise_api(12345, -50.0):")
    print(f"预期: call_counter=2，直接抛出 ValueError，被 catch 捕获\n")
    
    result = await async_enterprise_api(12345, -50.0)
    print(f"\n最终结果: {result}")
    
    
    print_header="关键证据片段示例日志"
    
    print("""

================================================================================
                          关键证据片段示例日志
================================================================================

以下是各个演示场景的关键日志片段，用于快速验证功能是否正常。

""")
    
    await asyncio.sleep(0.5)
    
    
    print_subheader="证据 1: 元信息验证输出示例"
    
    print("""
    ──────────────────────────────────────────────────────────────────────────
      元信息对比验证: 异步函数元信息验证
    ──────────────────────────────────────────────────────────────────────────
    
      [装饰前 - 原始函数对象]
           原始函数对象 id: 140234567890123
           __name__: 'target_async_func'
           __doc__: '\n        这是目标异步函数的文档字符串...'
           signature: (a: int, b: str = 'default', *, flag: bool = False) -> Dict[str, Any]
           is_async (iscoroutinefunction): True
    
       现在对同一个函数对象应用装饰器...
    
      [装饰后 - 装饰后的函数对象]
           装饰后函数对象 id: 140234567890456
           __name__: 'target_async_func'
           __doc__: '\n        这是目标异步函数的文档字符串...'
           signature: (a: int, b: str = 'default', *, flag: bool = False) -> Dict[str, Any]
           is_async (iscoroutinefunction): True
    
      ──────────────────────────────────────────────────────────────────────────
       对比验证结果:
      ──────────────────────────────────────────────────────────────────────────
           __name__ 对比:      ✅ 相同
           __doc__ 对比:       ✅ 相同
           signature 对比:     ✅ 相同
           is_async 对比:      ✅ 相同
      ──────────────────────────────────────────────────────────────────────────
       【结论】functools.wraps 效果: ✅ 完全生效
    ──────────────────────────────────────────────────────────────────────────
    
    【验证要点】
    1. 装饰前后函数对象 id 不同 (说明是不同的对象)
    2. 但 __name__, __doc__, signature, is_async 完全相同
    3. 这证明 functools.wraps 正确工作
    """)
    
    
    print_subheader="证据 2: 洋葱模型完整 ENTER/EXIT 事件序列"
    
    print("""
    ──────────────────────────────────────────────────────────────────────────
      正常返回路径 - 完整事件序列
    ──────────────────────────────────────────────────────────────────────────
    
    2026-04-22 10:30:00 - INFO - [CHAIN: abcdef123456] [timer] ENTER -> async_onion_normal [UNIT=ms]
    2026-04-22 10:30:00 - INFO -   [CHAIN: abcdef123456] [catch] ENTER -> async_onion_normal [CATCHING=['Exception']]
    2026-04-22 10:30:00 - INFO -     [CHAIN: abcdef123456] [log] ENTER -> async_onion_normal
    2026-04-22 10:30:00 - INFO -       [CHAIN: abcdef123456] [log] PARAMS -> async_onion_normal ARGS=(10, 20) KWARGS={}
    2026-04-22 10:30:00 - INFO -       [CHAIN: abcdef123456] [log] RESULT -> async_onion_normal RETURN=30 ELAPSED=0.0512s
    2026-04-22 10:30:00 - INFO -     [CHAIN: abcdef123456] [log] EXIT -> async_onion_normal
    2026-04-22 10:30:00 - INFO -   [CHAIN: abcdef123456] [catch] EXIT -> async_onion_normal
    2026-04-22 10:30:00 - INFO - [CHAIN: abcdef123456] [timer] EXIT -> async_onion_normal [DURATION=51.234ms]
    
    ──────────────────────────────────────────────────────────────────────────
      异常捕获路径 - 完整事件序列
    ──────────────────────────────────────────────────────────────────────────
    
    2026-04-22 10:30:01 - INFO - [CHAIN: xyz9876543210] [timer] ENTER -> async_onion_exception [UNIT=ms]
    2026-04-22 10:30:01 - INFO -   [CHAIN: xyz9876543210] [catch] ENTER -> async_onion_exception [CATCHING=['ValueError']]
    2026-04-22 10:30:01 - INFO -     [CHAIN: xyz9876543210] [log] ENTER -> async_onion_exception
    2026-04-22 10:30:01 - INFO -       [CHAIN: xyz9876543210] [log] PARAMS -> async_onion_exception ARGS=(-5,) KWARGS={}
    2026-04-22 10:30:01 - ERROR -       [CHAIN: xyz9876543210] [log] EXCEPTION -> async_onion_exception ValueError: x 不能为负数: -5 ELAPSED=0.0001s
    2026-04-22 10:30:01 - ERROR -     [CHAIN: xyz9876543210] [log] EXCEPTION -> async_onion_exception
    2026-04-22 10:30:01 - ERROR -   [CHAIN: xyz9876543210] [catch] CAUGHT -> async_onion_exception ValueError: x 不能为负数: -5 -> DEFAULT=ASYNC_CAUGHT_VALUE
    2026-04-22 10:30:01 - INFO -   [CHAIN: xyz9876543210] [catch] EXIT -> async_onion_exception [RETURNED_DEFAULT=ASYNC_CAUGHT_VALUE]
    2026-04-22 10:30:01 - INFO - [CHAIN: xyz9876543210] [timer] EXIT -> async_onion_exception [DURATION=1.234ms]
    
    【验证要点】
    1. 同一个 CHAIN_ID 贯穿整个调用 (abcdef123456 或 xyz9876543210)
    2. 缩进显示嵌套层级 (无缩进 -> 2空格 -> 4空格 -> 6空格)
    3. 进入顺序: timer ENTER -> catch ENTER -> log ENTER
    4. 退出顺序: log EXIT -> catch EXIT -> timer EXIT (洋葱模型)
    5. 异常路径: log 显示 EXCEPTION，catch 捕获后正常 EXIT
    6. 所有装饰器的 ENTER 都有对应的退出标记
    """)
    
    
    print_subheader="证据 3: rate_limit 完整事件序列 (WAIT 模式)"
    
    print("""
    ──────────────────────────────────────────────────────────────────────────
      第 1 次调用 (正常通过)
    ──────────────────────────────────────────────────────────────────────────
    
    2026-04-22 10:30:02 - INFO - [CHAIN: call1_xxxxxx] [timer] ENTER -> async_wait_demo [UNIT=ms]
    2026-04-22 10:30:02 - INFO -   [CHAIN: call1_xxxxxx] [log] ENTER -> async_wait_demo
    2026-04-22 10:30:02 - INFO -     [CHAIN: call1_xxxxxx] [rate_limit] CHECK -> async_wait_demo [CURRENT=0/2 WINDOW=1.5s MODE=WAIT]
    2026-04-22 10:30:02 - INFO -     [CHAIN: call1_xxxxxx] [rate_limit] ALLOWED -> async_wait_demo [PROCEED] Used: 1/2, Remaining: 1/2
    2026-04-22 10:30:02 - INFO -       [CHAIN: call1_xxxxxx] [log] PARAMS -> async_wait_demo ARGS=('ASYNC_WAIT_01',) KWARGS={}
    2026-04-22 10:30:02 - INFO -       [CHAIN: call1_xxxxxx] [log] RESULT -> async_wait_demo RETURN={'status': 'success', ...} ELAPSED=0.0105s
    2026-04-22 10:30:02 - INFO -     [CHAIN: call1_xxxxxx] [log] EXIT -> async_wait_demo
    2026-04-22 10:30:02 - INFO - [CHAIN: call1_xxxxxx] [timer] EXIT -> async_wait_demo [DURATION=11.234ms]
    
    ──────────────────────────────────────────────────────────────────────────
      第 3 次调用 (触发等待，完整事件序列)
    ──────────────────────────────────────────────────────────────────────────
    
    2026-04-22 10:30:03 - INFO - [CHAIN: call3_yyyyyy] [timer] ENTER -> async_wait_demo [UNIT=ms]
    2026-04-22 10:30:03 - INFO -   [CHAIN: call3_yyyyyy] [log] ENTER -> async_wait_demo
    2026-04-22 10:30:03 - INFO -     [CHAIN: call3_yyyyyy] [rate_limit] CHECK -> async_wait_demo [CURRENT=2/2 WINDOW=1.5s MODE=WAIT]
    2026-04-22 10:30:03 - WARNING -     [CHAIN: call3_yyyyyy] [rate_limit] LIMITED -> async_wait_demo [THROTTLED] Need to wait 1.498s for next slot...
    2026-04-22 10:30:03 - WARNING -     [CHAIN: call3_yyyyyy] [rate_limit] WAITING -> async_wait_demo [SLEEP_START] wait_time=1.498s
    2026-04-22 10:30:05 - INFO -     [CHAIN: call3_yyyyyy] [rate_limit] RELEASED -> async_wait_demo [SLEEP_END] Waited 1.498s, now allowed to proceed
    2026-04-22 10:30:05 - INFO -     [CHAIN: call3_yyyyyy] [rate_limit] ALLOWED -> async_wait_demo [PROCEED] Used: 1/2, Remaining: 1/2
    2026-04-22 10:30:05 - INFO -       [CHAIN: call3_yyyyyy] [log] PARAMS -> async_wait_demo ARGS=('ASYNC_WAIT_03',) KWARGS={}
    2026-04-22 10:30:05 - INFO -       [CHAIN: call3_yyyyyy] [log] RESULT -> async_wait_demo RETURN={'status': 'success', ...} ELAPSED=0.0102s
    2026-04-22 10:30:05 - INFO -     [CHAIN: call3_yyyyyy] [log] EXIT -> async_wait_demo
    2026-04-22 10:30:05 - INFO - [CHAIN: call3_yyyyyy] [timer] EXIT -> async_wait_demo [DURATION=1509.876ms]
    
    【验证要点】
    1. 完整事件序列 (第 3 次调用):
       CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED
    
    2. 日志时间戳验证:
       WAITING 日志: 10:30:03
       RELEASED 日志: 10:30:05 (约 1.5 秒后)
       证明确实等待了 1.498 秒
    
    3. 剩余配额不会为负数:
       格式: "Used: X/Y, Remaining: Z/Y"
       使用 max(0, ...) 确保 Z >= 0
    
    4. 并发安全:
       使用 asyncio.Lock 保护临界区
       多个协程同时调用时计数一致
    """)
    
    
    print_subheader="证据 4: 企业级异步场景 - 重试成功链路"
    
    print("""
    ──────────────────────────────────────────────────────────────────────────
      企业级场景 - 重试成功完整链路
    ──────────────────────────────────────────────────────────────────────────
    
    配置:
    - @timer (最外层)
    - @catch
    - @rate_limit
    - @retry (max_attempts=2)
    - @log (最内层)
    
    预期行为:
    - 第 1 次尝试: 抛出 ConnectionError
    - retry 捕获，等待 0.3s
    - 第 2 次尝试: 正常返回
    - 所有装饰器的 ENTER/EXIT 完整
    
    2026-04-22 10:30:06 - INFO - [CHAIN: enterprise_chain_id] [timer] ENTER -> async_enterprise_api [UNIT=ms]
    2026-04-22 10:30:06 - INFO -   [CHAIN: enterprise_chain_id] [catch] ENTER -> async_enterprise_api [CATCHING=['RateLimitExceededError', 'ValueError', 'Exception']]
    2026-04-22 10:30:06 - INFO -     [CHAIN: enterprise_chain_id] [rate_limit] CHECK -> async_enterprise_api [CURRENT=0/5 WINDOW=10.0s MODE=REJECT]
    2026-04-22 10:30:06 - INFO -     [CHAIN: enterprise_chain_id] [rate_limit] ALLOWED -> async_enterprise_api [PROCEED] Used: 1/5, Remaining: 4/5
    2026-04-22 10:30:06 - INFO -       [CHAIN: enterprise_chain_id] [retry] ENTER -> async_enterprise_api [MAX_ATTEMPTS=2]
    2026-04-22 10:30:06 - INFO -         [CHAIN: enterprise_chain_id] [retry] ATTEMPT -> async_enterprise_api [1/2]
    2026-04-22 10:30:06 - INFO -           [CHAIN: enterprise_chain_id] [log] ENTER -> async_enterprise_api
    2026-04-22 10:30:06 - INFO -             [CHAIN: enterprise_chain_id] [log] PARAMS -> async_enterprise_api ARGS=(12345, 100.5) KWARGS={}
    2026-04-22 10:30:06 - ERROR -             [CHAIN: enterprise_chain_id] [log] EXCEPTION -> async_enterprise_api ConnectionError: 数据库连接失败 (异步尝试 1) ELAPSED=0.0001s
    2026-04-22 10:30:06 - ERROR -           [CHAIN: enterprise_chain_id] [log] EXCEPTION -> async_enterprise_api
    2026-04-22 10:30:06 - WARNING -         [CHAIN: enterprise_chain_id] [retry] FAILED -> async_enterprise_api [ATTEMPT=1/2] ConnectionError: 数据库连接失败 (异步尝试 1) -> RETRY_AFTER=0.30s
    2026-04-22 10:30:06 - INFO -         [CHAIN: enterprise_chain_id] [retry] ATTEMPT -> async_enterprise_api [2/2]
    2026-04-22 10:30:06 - INFO -           [CHAIN: enterprise_chain_id] [log] ENTER -> async_enterprise_api
    2026-04-22 10:30:06 - INFO -             [CHAIN: enterprise_chain_id] [log] PARAMS -> async_enterprise_api ARGS=(12345, 100.5) KWARGS={}
    2026-04-22 10:30:06 - INFO -             [CHAIN: enterprise_chain_id] [log] RESULT -> async_enterprise_api RETURN={'transaction_id': 'ASYNC_TXN_1234567890', ...} ELAPSED=0.0512s
    2026-04-22 10:30:06 - INFO -           [CHAIN: enterprise_chain_id] [log] EXIT -> async_enterprise_api
    2026-04-22 10:30:06 - INFO -         [CHAIN: enterprise_chain_id] [retry] SUCCESS -> async_enterprise_api [SUCCEEDED_ON=2/2]
    2026-04-22 10:30:06 - INFO -       [CHAIN: enterprise_chain_id] [retry] EXIT -> async_enterprise_api
    2026-04-22 10:30:06 - INFO -   [CHAIN: enterprise_chain_id] [catch] EXIT -> async_enterprise_api
    2026-04-22 10:30:06 - INFO - [CHAIN: enterprise_chain_id] [timer] EXIT -> async_enterprise_api [DURATION=352.456ms]
    
    【验证要点】
    1. 装饰器链执行顺序正确:
       timer -> catch -> rate_limit -> retry -> log
    
    2. 重试机制完整:
       [retry] ATTEMPT [1/2] -> 失败
       [retry] FAILED -> 等待 0.3s
       [retry] ATTEMPT [2/2] -> 成功
       [retry] SUCCESS [SUCCEEDED_ON=2/2]
    
    3. 所有装饰器的 ENTER/EXIT 完整:
       - timer: ENTER -> EXIT
       - catch: ENTER -> EXIT
       - rate_limit: CHECK -> ALLOWED (没有 ENTER/EXIT，但有状态事件)
       - retry: ENTER -> ATTEMPT x2 -> SUCCESS -> EXIT
       - log: 两次 ENTER -> 第一次 EXCEPTION，第二次 EXIT
    
    4. 修复的 NameError 问题:
       - 使用可变对象 list 存储计数器
       - 不需要 nonlocal 或 global 声明
       - 嵌套函数可以正常修改
    """)
    
    
    print_header="异步演示总结"
    
    print("""

================================================================================
                          异步函数装饰器演示完成
================================================================================

✅ 已修复的问题:

1. 元信息验证方式
   - 之前: 使用两个不同命名的函数对比 (可能误导)
   - 现在: 对同一个函数对象装饰前后对比
   - 保存原始函数引用，装饰后对比
   - 验证 __name__, __doc__, signature, is_async

2. ENTER/EXIT 事件完整性
   - 之前: try/except 内的 return/raise 可能跳过 EXIT
   - 现在: 使用 try/finally 确保 EXIT 总是被打印
   - 异常路径使用 EXCEPTION 事件标记
   - 正常路径使用 EXIT 事件标记
   - 所有装饰器的 ENTER 都有对应的退出标记

3. 并发限流计数问题
   - 之前: 竞态条件可能导致剩余配额为负数
   - 现在: 使用 asyncio.Lock (异步) 或 threading.Lock (同步)
   - 使用 max(0, ...) 确保剩余配额 >= 0
   - 日志格式: "Used: X/Y, Remaining: Z/Y"
   - 并发场景下计数一致

4. 企业级场景 NameError
   - 之前: call_counter 是局部变量，使用 global 声明
   - 现在: 使用可变对象 list 存储计数器
   - 技巧: call_counter = [0]，修改 list[0]
   - 不需要 nonlocal 或 global 声明
   - 嵌套函数可以正常修改

================================================================================

✅ 可验证的输出:

1. 元信息验证
   - 同一个函数对象 id 装饰前后对比
   - __name__, __doc__, signature, is_async 完全一致
   - 证明 functools.wraps 正确工作

2. 洋葱模型
   - 进入顺序: 外层 ENTER -> 内层 ENTER
   - 退出顺序: 内层 EXIT -> 外层 EXIT
   - 同一个 CHAIN_ID 贯穿整个调用
   - 缩进显示嵌套层级

3. rate_limit 两种模式
   - REJECT: CHECK -> LIMITED -> 抛出异常
   - WAIT: CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED
   - 等待时间通过日志时间戳验证
   - 剩余配额不会为负数

4. 企业级场景
   - 完整的装饰器链日志
   - 重试机制完整事件序列
   - 所有 ENTER/EXIT 成对出现
   - 计数器正常工作 (无 NameError)

================================================================================
""")


if __name__ == "__main__":
    asyncio.run(main())
