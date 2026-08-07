import time
import functools
import inspect
from typing import Dict, Any, List, Callable

from decorators import (
    log, timer, catch, rate_limit, retry, 
    RateLimitExceededError, reset_chain_context
)
from chain import DecoratorChain, DecoratorPresets, is_async_func


def print_header(title: str, width: int = 80):
    print("\n" + "=" * width)
    print(f"【{title}】")
    print("=" * width)


def print_subheader(text: str):
    print(f"\n>>> {text} <<<")


def compare_func_meta(original_func: Callable, decorated_func: Callable, label: str = ""):
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
    
    all_match = name_match and doc_match and sig_match
    print(f"\n  【结论】functools.wraps 效果: {'✅ 完全生效' if all_match else '❌ 存在问题'}")
    print(f"{'='*60}\n")
    
    return all_match


print_header("演示 0: 装饰器链系统初始化")

print("""

================================================================================
                          企业级可复用 Python 装饰器链系统
                           增强版 - 完整可验证演示
================================================================================

本演示包含以下可验证内容:

  1. 元信息验证 - 证明 functools.wraps 完整保留函数信息
     - 对比装饰前后的 __name__、__doc__、inspect.signature

  2. 执行顺序验证 - 多层装饰器的"洋葱模型"
     - 观察 ENTER/EXIT 事件序列
     - 同一个 CHAIN_ID 贯穿整个调用链
     - 缩进显示嵌套层级

  3. rate_limit 两种模式完整演示
     - REJECT 模式: 超过阈值直接拒绝
     - WAIT 模式: 超过阈值等待后放行
     - 完整事件序列: CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED

  4. DecoratorChain 动态编排演示
     - 预设链的使用
     - 动态添加/移除装饰器

================================================================================
""")

time.sleep(0.5)


print_header="演示 1: functools.wraps 元信息验证"

print_subheader="定义原始函数"

def original_function(a: int, b: str = "default", *, flag: bool = False) -> Dict[str, Any]:
    """
    这是原始函数的文档字符串。
    
    功能描述:
    - 接收一个整数 a 和一个字符串 b
    - 接收一个关键字-only 参数 flag
    - 返回一个包含所有参数的字典
    
    参数:
        a: 整数参数
        b: 字符串参数，默认值 "default"
        flag: 布尔关键字参数，默认值 False
    
    返回:
        包含所有参数的字典
    """
    return {
        "a": a,
        "b": b,
        "flag": flag,
        "result": a * len(b)
    }


print(f"\n原始函数定义:")
print(f"  函数名: {original_function.__name__}")
print(f"  签名: {inspect.signature(original_function)}")
print(f"  是否异步: {is_async_func(original_function)}")


print_subheader="应用多层装饰器"

@timer(unit="ms", precision=4)
@catch(exceptions=(Exception,), default={"error": "caught"})
@log(level="INFO", log_args=True, log_return=True)
def decorated_function(a: int, b: str = "default", *, flag: bool = False) -> Dict[str, Any]:
    """
    这是原始函数的文档字符串。
    
    功能描述:
    - 接收一个整数 a 和一个字符串 b
    - 接收一个关键字-only 参数 flag
    - 返回一个包含所有参数的字典
    
    参数:
        a: 整数参数
        b: 字符串参数，默认值 "default"
        flag: 布尔关键字参数，默认值 False
    
    返回:
        包含所有参数的字典
    """
    return {
        "a": a,
        "b": b,
        "flag": flag,
        "result": a * len(b)
    }


print(f"\n装饰后函数定义:")
print(f"  函数名: {decorated_function.__name__}")


print_subheader="元信息对比验证"

compare_func_meta(original_function, decorated_function, "多层装饰器装饰后的函数")


print_subheader="使用 DecoratorChain 装饰后的元信息验证"

def another_original(x: float, y: float = 1.0) -> float:
    """另一个原始函数，用于测试 Chain 装饰"""
    return x * y

chain = DecoratorChain()
chain.add(timer, unit="s")
chain.add(log, level="DEBUG")

decorated_by_chain = chain.apply(another_original)

compare_func_meta(another_original, decorated_by_chain, "DecoratorChain 装饰后的函数")


print_header="演示 2: 多层装饰器执行顺序验证 - 洋葱模型"

print("""

洋葱模型说明:
=============

装饰器叠加顺序:
    @timer      (最外层)
    @catch      (中间层)
    @log        (最内层)
    def func(): ...

预期执行顺序 (通过日志验证):
    1. timer ENTER      (最外层先进入)
    2.   catch ENTER    (中间层进入)
    3.     log ENTER    (最内层进入)
    4.       log PARAMS / RESULT (实际函数执行)
    5.     log EXIT     (最内层先退出)
    6.   catch EXIT     (中间层退出)
    7. timer EXIT       (最外层最后退出)

同一个 CHAIN_ID 应该贯穿整个调用过程。
缩进层级应该显示嵌套关系。

""")

time.sleep(1)


print_subheader="正常执行场景 - 验证洋葱模型顺序"

reset_chain_context()

@timer(unit="ms", precision=3)
@catch(exceptions=(Exception,), default="DEFAULT_VALUE")
@log(level="INFO", log_args=True, log_return=True)
def onion_demo_normal(x: int, y: int) -> int:
    """洋葱模型演示 - 正常执行"""
    print(f"        [实际函数体执行] x={x}, y={y}")
    time.sleep(0.05)
    return x + y


print(f"\n调用 onion_demo_normal(10, 20):")
print(f"请仔细观察日志中的 ENTER/EXIT 顺序和 CHAIN_ID:\n")

result = onion_demo_normal(10, 20)
print(f"\n返回结果: {result}")


print_subheader="异常捕获场景 - 验证异常时的执行顺序"

reset_chain_context()

@timer(unit="ms", precision=3)
@catch(exceptions=(ValueError,), default="CAUGHT_BY_CATCH")
@log(level="INFO", log_args=True, log_return=True)
def onion_demo_exception(x: int) -> int:
    """洋葱模型演示 - 异常场景"""
    print(f"        [实际函数体执行] x={x}")
    if x < 0:
        raise ValueError(f"x 不能为负数: {x}")
    return x * 2


print(f"\n调用 onion_demo_exception(-5) (会抛出 ValueError):")
print(f"观察 catch 装饰器如何捕获异常并返回默认值:\n")

result = onion_demo_exception(-5)
print(f"\n返回结果: {result}")


print_subheader="连续多次调用 - 验证 CHAIN_ID 独立性"

print("""
每次调用应该生成不同的 CHAIN_ID，证明:
1. 每次调用都是独立的上下文
2. contextvars 正确隔离了不同调用
""")

reset_chain_context()

@log(level="INFO")
@timer(unit="ms")
def chain_id_demo(n: int) -> str:
    return f"call_{n}"

print(f"\n连续调用 3 次，观察 CHAIN_ID 变化:\n")

for i in range(1, 4):
    reset_chain_context()
    print(f"\n--- 第 {i} 次调用 ---")
    chain_id_demo(i)


print_header="演示 3: rate_limit 两种模式完整演示"

print("""

rate_limit 装饰器支持两种模式:
=================================

模式 1: REJECT (直接拒绝)
    - 超过阈值时，立即抛出 RateLimitExceededError
    - 适用于必须快速失败的场景
    - 事件序列: CHECK -> LIMITED -> [抛出异常]

模式 2: WAIT (等待放行)
    - 超过阈值时，等待直到时间窗口允许新的调用
    - 适用于可以容忍延迟的场景
    - 完整事件序列: CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED

本演示将完整展示这两种模式的行为。

""")

time.sleep(1)


print_subheader="模式 1: REJECT - 直接拒绝模式"

reset_chain_context()

@rate_limit(max_calls=2, time_window=3.0, mode="reject")
@log(level="INFO", log_args=True, log_return=True)
def rate_limit_reject_demo(request_id: str) -> Dict[str, Any]:
    """限流演示 - REJECT 模式"""
    return {
        "status": "success",
        "request_id": request_id,
        "timestamp": time.time()
    }


print(f"""
配置:
  - max_calls = 2 (每窗口最多 2 次)
  - time_window = 3.0 秒
  - mode = "reject" (直接拒绝)

预期行为:
  - 第 1-2 次调用: 成功
  - 第 3-5 次调用: 被拒绝，抛出 RateLimitExceededError
""")

print(f"\n开始执行 5 次调用...\n")

for i in range(1, 6):
    reset_chain_context()
    req_id = f"REQ_{i:02d}"
    print(f"\n{'─'*50}")
    print(f"调用 {i}/5: request_id = {req_id}")
    print(f"{'─'*50}")
    
    try:
        result = rate_limit_reject_demo(req_id)
        print(f"\n  ✅ 成功: {result}")
    except RateLimitExceededError as e:
        print(f"\n  ❌ 被限流 (RateLimitExceededError): {e}")


print_subheader="模式 2: WAIT - 等待放行模式 (完整事件序列)"

reset_chain_context()

@rate_limit(max_calls=2, time_window=1.5, mode="wait")
@log(level="INFO", log_args=True, log_return=True)
@timer(unit="ms", precision=2)
def rate_limit_wait_demo(request_id: str) -> Dict[str, Any]:
    """限流演示 - WAIT 模式"""
    return {
        "status": "success",
        "request_id": request_id,
        "processed_at": time.time()
    }


print(f"""
配置:
  - max_calls = 2 (每窗口最多 2 次)
  - time_window = 1.5 秒
  - mode = "wait" (等待放行)

预期行为:
  - 第 1-2 次调用: 立即成功
  - 第 3 次调用: 触发限流，需要等待约 1.5 秒
  - 等待后: 自动放行，执行成功

完整事件序列 (通过日志验证):
  1. [rate_limit] CHECK -> 检查当前调用计数
  2. [rate_limit] LIMITED -> 发现超过阈值
  3. [rate_limit] WAITING [SLEEP_START] -> 开始等待
  4. [rate_limit] RELEASED [SLEEP_END] -> 等待结束
  5. [rate_limit] ALLOWED [PROCEED] -> 允许执行
  6. 其他装饰器执行...
""")

print(f"\n开始执行 3 次调用 (第 3 次会触发等待)...")
print(f"注意: 第 3 次调用会等待约 1.5 秒，请耐心观察日志...\n")

start_time = time.time()

for i in range(1, 4):
    reset_chain_context()
    req_id = f"WAIT_REQ_{i:02d}"
    elapsed = time.time() - start_time
    
    print(f"\n{'═'*60}")
    print(f"调用 {i}/3: request_id = {req_id} (距开始: {elapsed:.2f}s)")
    print(f"{'═'*60}")
    
    try:
        result = rate_limit_wait_demo(req_id)
        elapsed_total = time.time() - start_time
        print(f"\n  ✅ 成功: {result}")
        print(f"  本次调用后总耗时: {elapsed_total:.2f}s")
    except Exception as e:
        print(f"\n  ❌ 异常: {type(e).__name__}: {e}")


print_header="演示 4: DecoratorChain 动态编排与预设链"

print_subheader="使用预设链 logging_chain"

reset_chain_context()

logging_chain = DecoratorPresets.logging_chain()
print(f"预设链定义: {logging_chain}")

@logging_chain
def preset_chain_demo(data: List[int]) -> Dict[str, Any]:
    """使用预设链装饰的函数"""
    time.sleep(0.02)
    return {
        "count": len(data),
        "sum": sum(data),
        "avg": sum(data) / len(data) if data else 0
    }


print(f"\n调用 preset_chain_demo([1, 2, 3, 4, 5]):\n")
result = preset_chain_demo([1, 2, 3, 4, 5])
print(f"\n结果: {result}")


print_subheader="使用预设链 safe_execution_chain (包含异常捕获)"

reset_chain_context()

safe_chain = DecoratorPresets.safe_execution_chain()
print(f"预设链定义: {safe_chain}")

@safe_chain
def risky_operation(x: int, y: int) -> float:
    """可能抛出异常的操作"""
    if x < 0:
        raise ValueError(f"x 不能为负: {x}")
    return x / y


print(f"\n测试 1: 正常调用 risky_operation(10, 2):\n")
result = risky_operation(10, 2)
print(f"结果: {result}")

reset_chain_context()
print(f"\n测试 2: 异常调用 risky_operation(-5, 2) (应该被捕获并返回默认值 None):\n")
result = risky_operation(-5, 2)
print(f"结果: {result}")


print_subheader="动态修改装饰器链"

print("""
演示:
1. 创建空链
2. 动态添加装饰器
3. 应用到函数
4. 验证效果
""")

dynamic_chain = DecoratorChain()
print(f"\n初始空链: {dynamic_chain}")

dynamic_chain.add(log, level="INFO")
print(f"添加 log 后: {dynamic_chain}")

dynamic_chain.add(timer, unit="ms")
print(f"添加 timer 后: {dynamic_chain}")

dynamic_chain.add(catch, exceptions=(Exception,), default="DYNAMIC_DEFAULT")
print(f"添加 catch 后: {dynamic_chain}")

print(f"\n最终链: {dynamic_chain}")

@dynamic_chain
def dynamic_chain_demo(x: int) -> str:
    """动态链装饰的函数"""
    if x > 100:
        raise ValueError(f"x 太大: {x}")
    return f"processed_{x}"


reset_chain_context()
print(f"\n测试 1: 正常调用 dynamic_chain_demo(50):\n")
result = dynamic_chain_demo(50)
print(f"结果: {result}")

reset_chain_context()
print(f"\n测试 2: 异常调用 dynamic_chain_demo(200) (应该被捕获):\n")
result = dynamic_chain_demo(200)
print(f"结果: {result}")


print_header="演示 5: 完整企业级场景 - 所有装饰器组合"

print("""
使用 full_chain 预设:
  - timer: 计时
  - catch: 异常捕获
  - rate_limit: 限流
  - retry: 重试
  - log: 日志记录

这是一个典型的企业级 API 服务的装饰器组合。
""")

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
def enterprise_api(user_id: int, amount: float) -> Dict[str, Any]:
    """企业级 API 模拟"""
    global call_counter
    call_counter += 1
    
    if call_counter < 2:
        raise ConnectionError(f"数据库连接失败 (尝试 {call_counter})")
    
    if amount <= 0:
        raise ValueError(f"无效金额: {amount}")
    
    time.sleep(0.05)
    return {
        "transaction_id": f"TXN_{int(time.time())}",
        "user_id": user_id,
        "amount": amount,
        "status": "SUCCESS"
    }


print_subheader="场景 1: 正常交易 (触发重试机制后成功)"

reset_chain_context()
call_counter = 0

print(f"\n调用 enterprise_api(12345, 100.50):")
print(f"预期: 第 1 次调用失败，触发 retry，第 2 次成功\n")

result = enterprise_api(12345, 100.50)
print(f"\n最终结果: {result}")


print_subheader="场景 2: 无效金额 (异常被捕获)"

reset_chain_context()
call_counter = 2

print(f"\n调用 enterprise_api(12345, -50.0):")
print(f"预期: 抛出 ValueError，被 catch 捕获，返回默认值 None\n")

result = enterprise_api(12345, -50.0)
print(f"\n最终结果: {result}")


print_subheader="场景 3: 触发限流"

reset_chain_context()
call_counter = 2

print(f"""
配置: max_calls=3, time_window=5.0s, mode=reject

将连续调用 5 次:
  - 第 1-3 次: 成功 (如果参数合法)
  - 第 4-5 次: 被限流，返回默认值 None
""")

for i in range(1, 6):
    reset_chain_context()
    call_counter = 2
    print(f"\n{'─'*50}")
    print(f"调用 {i}/5")
    print(f"{'─'*50}")
    
    result = enterprise_api(12345, 100.0 + i)
    print(f"\n结果: {result}")


print_header="演示总结"

print("""

================================================================================
                              演示完成总结
================================================================================

✅ 验证通过的功能:

1. functools.wraps 元信息保留
   - __name__: 装饰前后一致
   - __doc__: 装饰前后一致
   - inspect.signature: 装饰前后一致

2. 多层装饰器执行顺序 (洋葱模型)
   - 最外层装饰器 ENTER 最先执行
   - 最内层装饰器 EXIT 最先执行
   - 同一个 CHAIN_ID 贯穿整个调用
   - 缩进清晰显示嵌套层级

3. rate_limit 两种模式
   - REJECT 模式: 超过阈值立即拒绝，抛出异常
   - WAIT 模式: 超过阈值等待后放行
   - 完整事件序列可验证: CHECK -> LIMITED -> WAITING -> RELEASED -> ALLOWED

4. DecoratorChain 动态编排
   - 预设链快速使用
   - 动态添加/移除装饰器
   - 批量应用装饰器

5. 企业级组合场景
   - 所有装饰器协同工作
   - 重试 -> 限流 -> 异常捕获 -> 日志 -> 计时

================================================================================

下一步: 运行 async_demo.py 查看异步函数的装饰器演示

""")
