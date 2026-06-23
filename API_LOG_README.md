# API调用日志功能说明

## 修复内容

### 1. 代理连接错误修复 ✅

**问题描述：**
```
HTTPSConnectionPool(host='push2.eastmoney.com', port=443): Max retries exceeded
(Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected(...)))
```

**解决方案：**
- 在 `SESSION` 对象上设置 `trust_env = False`，禁用系统代理
- 在 `em_get()` 函数中显式传入 `proxies={}`，确保不使用代理

**代码修改：**
```python
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": random.choice(USER_AGENTS)})
SESSION.trust_env = False  # 禁用系统代理

# 在请求时显式禁用代理
r = SESSION.get(url, params=params, headers=h, timeout=timeout, proxies=)
```

### 2. API调用日志记录功能 ✅

**新增功能：**
- 自动记录所有API调用的详细信息
- 包含请求URL、参数、状态码、耗时、重试次数、错误信息
- 程序退出时自动保存为JSON文件
- 在程序输出末尾显示API调用统计

**日志内容：**
```json
{
  "total_calls": 10,
  "successful_calls": 9,
  "failed_calls": 1,
  "total_duration": 5.234,
  "calls": [
    {
      "timestamp": "2026-06-22T15:52:32.602740",
      "url": "http://fund.eastmoney.com/js/fundcode_search.js",
      "params": null,
      "status": 200,
      "duration": 0.391,
      "error": null,
      "retries": 0
    }
  ]
}
```

### 3. API接口降级方案 ✅

**问题描述：**
东方财富的 `push2.eastmoney.com` 行业排名接口不稳定，经常连接失败。

**解决方案：**
在 `v4_rotation()` 函数中实现多层降级：
1. 首先尝试实时行业排名API
2. 如果失败，使用预定义的热门行业列表作为备用
3. 确保程序不会因单个接口失败而中断

**代码示例：**
```python
try:
    # 尝试实时API
    r = em_get(url, params=params, timeout=20, max_retries=2)
    # 处理数据...
except Exception as e:
    logger.warning(f"push2接口失败: {e}，尝试备用方案...")
    # 使用预定义列表
    industries = fallback_industries
```

## 使用说明

### 1. 运行基金投顾系统

```bash
source .venv/bin/activate
python3 fund_advisor.py
```

程序会在结束时显示API调用统计：

```
================================================================================
  📊 API调用统计
================================================================================
  总调用次数: 15
  成功: 14  失败: 1
  总耗时: 8.45s  平均: 0.563s/次
```

### 2. 查看API调用日志

程序退出时会自动生成日志文件：`api_calls_YYYYMMDD_HHMMSS.json`

**查看最新日志：**
```bash
python3 view_api_logs.py
```

**列出所有日志文件：**
```bash
python3 view_api_logs.py --list
```

**日志输出示例：**
```
================================================================================
📋 API调用日志分析: api_calls_20260622_155236.json
================================================================================

总体统计:
  总调用次数: 2
  成功: 1 (50.0%)
  失败: 1 (50.0%)
  总耗时: 3.89秒
  平均耗时: 1.947秒/次

按接口统计:
接口                                                           调用     成功     失败     平均耗时       重试
----------------------------------------------------------------------------------------------------
http://fund.eastmoney.com/js/fundcode_search.js              1      1      0      0.391      0
https://push2.eastmoney.com/api/qt/clist/get                 1      0      1      3.503      3

失败调用详情:
1. https://push2.eastmoney.com/api/qt/clist/get
   时间: 2026-06-22T15:52:33.207809
   重试次数: 3
   耗时: 3.503秒
   错误: RequestException: (...)
```

### 3. 测试API修复

运行测试脚本验证修复效果：

```bash
python3 test_api_fix.py
```

## 日志文件管理

日志文件命名格式：`api_calls_YYYYMMDD_HHMMSS.json`

**清理旧日志：**
```bash
# 删除7天前的日志
find . -name "api_calls_*.json" -mtime +7 -delete

# 只保留最新5个日志
ls -t api_calls_*.json | tail -n +6 | xargs rm -f
```

## 技术细节

### 日志记录机制

1. **实时记录**：每次API调用完成后立即记录
2. **异常捕获**：即使请求失败也会记录错误信息
3. **性能统计**：包含每次请求的精确耗时
4. **重试跟踪**：记录重试次数，便于分析接口稳定性

### 代理禁用原理

```python
# 方法1: Session级别禁用
SESSION.trust_env = False

# 方法2: 请求级别禁用
requests.get(url, proxies={})
```

两种方法结合使用，确保不受系统代理配置影响。

## 常见问题

### Q1: 为什么某些接口仍然失败？

A: 东方财富的某些API（特别是 `push2.eastmoney.com`）存在不稳定性，可能是：
- 服务端限流
- 网络波动
- 接口维护

已实现降级方案，确保程序不会中断。

### Q2: 日志文件会占用多少空间？

A: 每次运行约生成 2-10KB 的日志文件。建议定期清理超过7天的日志。

### Q3: 如何分析哪个接口最慢？

A: 使用 `view_api_logs.py` 查看"按接口统计"部分，关注"平均耗时"列。

## 更新日志

- **2026-06-22**: 
  - 修复代理连接错误
  - 新增API调用日志记录功能
  - 实现行业排名API降级方案
  - 新增日志查看工具
