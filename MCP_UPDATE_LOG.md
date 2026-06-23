# MCP 功能更新说明

## 更新时间
2026-06-23

## 更新内容

### 新增文件

1. **fund_advisor_mcp.py** - MCP 服务器封装
   - 提供 11 个 MCP 工具接口
   - 支持 `--mcp` 参数启动服务器模式
   - 不带参数时等同于原始脚本

2. **MCP_USAGE.md** - MCP 使用详细文档
   - 两种模式对比说明
   - 11 个工具的详细说明
   - 配置和故障排查指南

3. **mcp_config.json** - MCP 配置示例
   - Claude Code 等客户端的配置模板

4. **test_mcp.py** - MCP 功能测试脚本
   - 验证所有组合生成函数
   - 测试搜索和查询功能
   - 验证 JSON 序列化

5. **examples.py** - Python API 使用示例
   - 8 个实用示例
   - 展示如何在代码中直接调用
   - MCP 和独立脚本的桥梁

### 修改文件

1. **README.md** - 更新项目说明
   - 新增 MCP 模式介绍
   - 更新项目结构
   - 新增工具列表

2. **requirements.txt** - 更新依赖
   - 新增 `mcp>=1.0.0` 依赖

## 设计原则

### 零破坏性
- `fund_advisor.py` **完全不变**，保留原有功能
- 可以继续独立运行，输出结果完全一致
- 所有历史调用方式保持兼容

### 双模式支持
```
独立脚本模式          MCP 服务器模式
     ↓                      ↓
fund_advisor.py ←─── fund_advisor_mcp.py
     ↑                      ↑
  直接运行              MCP 客户端调用
```

### 架构分层
```
┌─────────────────────────────────────┐
│  MCP 客户端 (Claude Code 等)         │
└────────────┬────────────────────────┘
             │ MCP 协议
┌────────────▼────────────────────────┐
│  fund_advisor_mcp.py (适配层)        │
│  - 11 个 MCP 工具                    │
│  - JSON 序列化                       │
│  - 错误处理                          │
└────────────┬────────────────────────┘
             │ Python 函数调用
┌────────────▼────────────────────────┐
│  fund_advisor.py (核心逻辑层)        │
│  - 数据获取                          │
│  - 评分算法                          │
│  - 组合生成                          │
└─────────────────────────────────────┘
```

## MCP 工具清单

### 基金组合推荐 (5个)
- `get_portfolio_v1_defensive` - V1 稳健版
- `get_portfolio_v2_balanced` - V2 均衡版
- `get_portfolio_v3_growth` - V3 成长版
- `get_portfolio_v4_rotation` - V4 行业轮动版
- `get_portfolio_v5_index` - V5 指数版

### 综合查询 (1个)
- `get_all_portfolios` - 获取所有版本

### 基金查询 (3个)
- `search_fund` - 搜索基金
- `get_fund_holdings` - 获取持仓
- `get_fund_ranking` - 获取排名

### 板块分析 (2个)
- `find_sector_etf` - 查找板块ETF
- `get_sector_top_funds` - 获取板块头部基金

## 使用方式

### 方式 1: 独立脚本（保持不变）
```bash
python3 fund_advisor.py
```

### 方式 2: MCP 服务器
```bash
# 启动服务器
python3 fund_advisor_mcp.py --mcp

# 或配置到 Claude Code
# 见 mcp_config.json
```

### 方式 3: Python API
```python
from fund_advisor import v3_growth
portfolio = v3_growth()
```

## 测试验证

```bash
# 测试 MCP 功能
python3 test_mcp.py

# 查看使用示例
python3 examples.py
```

## 兼容性

- ✅ 原有脚本功能完全保留
- ✅ 原有调用方式不受影响
- ✅ 可选择性使用 MCP 功能
- ✅ 不安装 mcp 依赖也能正常运行原脚本

## 后续扩展

MCP 架构使得系统可以轻松扩展：

1. **新增工具**: 在 `fund_advisor_mcp.py` 添加新的工具定义
2. **集成其他客户端**: 支持所有 MCP 协议客户端
3. **远程调用**: 可以部署为 HTTP 服务
4. **多语言支持**: MCP 协议支持多语言客户端

## 技术栈

- **核心**: Python 3.12+, requests
- **MCP 框架**: mcp>=1.0.0
- **协议**: MCP (Model Context Protocol)
- **通信**: stdio (标准输入输出)

## 注意事项

1. MCP 模式需要安装 `mcp` 包
2. 独立脚本模式无需额外依赖
3. 两种模式共享相同的数据源和算法
4. API 调用日志在两种模式下都会生成

## 免责声明

本系统仅供学习研究使用，不构成投资建议。
