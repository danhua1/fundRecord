# Cherry Studio MCP 配置指南

## 问题修复说明

已修复 MCP 服务器兼容性问题：
- ✅ 使用正确的 MCP SDK API
- ✅ 修复了工具列表返回格式
- ✅ 添加了 stderr 日志输出（不干扰 stdio 通信）
- ✅ 添加了更严格的 inputSchema 验证
- ✅ 兼容 Cherry Studio 和其他 MCP 客户端

---

## Cherry Studio 配置步骤

### 1. 找到 Cherry Studio 的 MCP 配置文件

Cherry Studio 的配置文件通常位于：
- **macOS**: `~/Library/Application Support/cherry-studio/mcp_config.json`
- **Windows**: `%APPDATA%\cherry-studio\mcp_config.json`
- **Linux**: `~/.config/cherry-studio/mcp_config.json`

### 2. 添加配置

打开配置文件，添加以下内容：

```json
{
  "mcpServers": {
    "fund-advisor": {
      "command": "python3",
      "args": [
        "/Users/dusiyuan/Documents/fundRecord/fund_advisor_mcp.py",
        "--mcp"
      ],
      "env": {
        "PYTHONPATH": "/Users/dusiyuan/Documents/fundRecord",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**⚠️ 重要**: 将路径 `/Users/dusiyuan/Documents/fundRecord` 替换为你的实际项目路径！

### 3. 确保虚拟环境中有依赖

```bash
cd /Users/dusiyuan/Documents/fundRecord
source .venv/bin/activate
pip install mcp requests
```

### 4. 测试 MCP 服务器

在添加到 Cherry Studio 之前，先手动测试：

```bash
cd /Users/dusiyuan/Documents/fundRecord
source .venv/bin/activate
python3 fund_advisor_mcp.py --mcp
```

如果服务器正常启动，你会看到类似输出：
```
启动 Fund Advisor MCP 服务器...
模式: stdio
工具数量: 11
```

按 `Ctrl+C` 停止测试。

### 5. 重启 Cherry Studio

配置完成后，完全退出并重新启动 Cherry Studio。

### 6. 验证工具是否加载

在 Cherry Studio 中：
1. 打开设置或工具面板
2. 查看是否显示 "fund-advisor" 服务器
3. 应该能看到 11 个可用工具

---

## 可用的 11 个工具

### 基金组合推荐（5个）
1. **get_portfolio_v1_defensive** - V1稳健版（低风险⭐）
2. **get_portfolio_v2_balanced** - V2均衡版（中低风险⭐⭐）
3. **get_portfolio_v3_growth** - V3成长版（中高风险⭐⭐⭐）
4. **get_portfolio_v4_rotation** - V4行业轮动版（高风险⭐⭐⭐⭐）
5. **get_portfolio_v5_index** - V5指数版（中风险⭐⭐）

### 综合查询（1个）
6. **get_all_portfolios** - 一次性获取所有版本

### 基金查询（3个）
7. **search_fund** - 搜索基金（需要参数：keyword）
8. **get_fund_holdings** - 查询持仓（需要参数：code）
9. **get_fund_ranking** - 获取排名（可选参数：fund_type, sort_by, page_size）

### 板块分析（2个）
10. **find_sector_etf** - 查找板块ETF（需要参数：keyword）
11. **get_sector_top_funds** - 获取板块头部基金（需要参数：sector）

---

## 使用示例

在 Cherry Studio 的对话中：

```
请帮我获取 V3 成长版的基金组合推荐
```

```
搜索一下"消费"相关的基金
```

```
查找芯片板块的 ETF
```

```
获取科技板块的头部主动管理基金
```

---

## 故障排查

### 问题 1: Cherry Studio 找不到工具

**解决方案**:
1. 检查配置文件路径是否正确
2. 确保 Python 路径正确：`which python3`
3. 确保项目路径是绝对路径
4. 重启 Cherry Studio

### 问题 2: 工具调用失败

**解决方案**:
1. 手动测试服务器：`python3 fund_advisor_mcp.py --mcp`
2. 检查依赖是否安装：`pip list | grep mcp`
3. 查看日志：Cherry Studio 通常有错误日志面板

### 问题 3: Python 虚拟环境问题

**解决方案**:

如果使用虚拟环境，修改配置为：

```json
{
  "mcpServers": {
    "fund-advisor": {
      "command": "/Users/dusiyuan/Documents/fundRecord/.venv/bin/python3",
      "args": [
        "/Users/dusiyuan/Documents/fundRecord/fund_advisor_mcp.py",
        "--mcp"
      ],
      "env": {
        "PYTHONPATH": "/Users/dusiyuan/Documents/fundRecord"
      }
    }
  }
}
```

**注意**: 使用虚拟环境中的 python3 完整路径。

### 问题 4: 网络超时

**症状**: 工具调用很慢或超时

**原因**: 数据源 API 调用较慢

**解决**: 正常现象，首次调用需要 15-30 秒获取数据，后续会使用缓存。

---

## 调试模式

如果需要查看详细日志，可以手动启动服务器：

```bash
cd /Users/dusiyuan/Documents/fundRecord
source .venv/bin/activate
python3 fund_advisor_mcp.py --mcp 2>&1 | tee mcp_debug.log
```

日志会保存到 `mcp_debug.log` 文件。

---

## 修复内容总结

### 修复前的问题
- ❌ 使用了错误的 `types.Tool` 导入
- ❌ 装饰器使用不当
- ❌ 返回格式不符合规范

### 修复后的改进
- ✅ 使用正确的 `Tool` 和 `TextContent` 类型
- ✅ 日志输出到 stderr，避免干扰 stdio
- ✅ 完善的 inputSchema 定义（包含 enum, minimum, maximum）
- ✅ 统一的错误处理
- ✅ 更好的日志记录

---

## 配置文件模板

完整的配置文件已保存在项目根目录：
- `mcp_config.json` - 配置模板

直接复制该文件内容到 Cherry Studio 的配置文件中，并修改路径即可。

---

## 技术细节

### MCP 协议版本
- MCP SDK: 1.28.0
- 协议: stdio (标准输入输出)
- 通信格式: JSON-RPC

### 关键修复点
1. **Tool 定义**: 使用 `Tool` 而不是 `types.Tool`
2. **内容返回**: 使用 `TextContent` 包装结果
3. **异步处理**: 正确使用 `async/await`
4. **错误隔离**: 日志输出到 stderr

---

**现在可以在 Cherry Studio 中正常使用了！** 🎉
