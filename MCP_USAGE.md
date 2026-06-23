# 基金投顾系统 MCP 使用说明

## 概述

本系统现在支持两种使用模式：

1. **独立脚本模式**（保留原有功能）
2. **MCP 服务器模式**（新增，支持 Claude Code 等 MCP 客户端调用）

---

## 模式 1: 独立脚本执行（原有模式）

### 使用方法

```bash
# 激活虚拟环境
source .venv/bin/activate

# 直接运行脚本
python3 fund_advisor.py

# 或运行 MCP 版本（不带参数时等同于原脚本）
python3 fund_advisor_mcp.py
```

### 输出结果

- 在终端直接输出5个版本的基金组合推荐
- 生成 API 调用日志文件（`api_calls_*.json`）

---

## 模式 2: MCP 服务器模式（新增）

### 安装依赖

```bash
# 确保已安装 mcp 包
pip install mcp

# 或更新 requirements.txt
echo "mcp>=1.0.0" >> requirements.txt
pip install -r requirements.txt
```

### 配置 MCP 服务器

#### 方式 1: 在 Claude Code 中配置

将以下配置添加到 Claude Code 的 MCP 配置文件中：

**位置**: `~/.claude/mcp_config.json` 或项目根目录

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
        "PYTHONPATH": "/Users/dusiyuan/Documents/fundRecord"
      }
    }
  }
}
```

#### 方式 2: 直接启动 MCP 服务器

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动 MCP 服务器（通过 stdio 通信）
python3 fund_advisor_mcp.py --mcp
```

### 可用的 MCP 工具

MCP 模式下提供以下 11 个工具：

#### 1. 基金组合推荐工具（5个版本）

| 工具名称 | 说明 | 风险等级 |
|---------|------|---------|
| `get_portfolio_v1_defensive` | V1 稳健版（债券为主） | 低风险 ⭐ |
| `get_portfolio_v2_balanced` | V2 均衡版（股债平衡） | 中低风险 ⭐⭐ |
| `get_portfolio_v3_growth` | V3 成长版（权益为主） | 中高风险 ⭐⭐⭐ |
| `get_portfolio_v4_rotation` | V4 行业轮动版（动量驱动） | 高风险 ⭐⭐⭐⭐ |
| `get_portfolio_v5_index` | V5 指数版（纯被动） | 中风险 ⭐⭐ |

#### 2. 综合工具

- **`get_all_portfolios`**: 一次性获取所有5个版本的组合推荐

#### 3. 基金查询工具

- **`search_fund`**: 搜索基金（支持代码、名称关键词）
  - 参数: `keyword` (必填), `limit` (可选，默认10)

- **`get_fund_holdings`**: 获取基金持仓和板块分析
  - 参数: `code` (必填), `year` (可选), `quarter` (可选)

- **`get_fund_ranking`**: 获取基金排名列表
  - 参数: `fund_type` (可选), `sort_by` (可选), `page_size` (可选)

#### 4. 板块分析工具

- **`find_sector_etf`**: 查找板块 ETF
  - 参数: `keyword` (必填，如: 芯片、新能源、消费)

- **`get_sector_top_funds`**: 获取板块头部主动管理基金
  - 参数: `sector` (必填), `top_n` (可选，默认10)

### 使用示例

#### 在 Claude Code 中调用

配置完成后，可以在 Claude Code 对话中直接使用：

```
请帮我获取V3成长版的基金组合推荐
```

Claude Code 会自动调用 `get_portfolio_v3_growth` 工具。

```
帮我搜索"消费"相关的基金
```

Claude Code 会调用 `search_fund` 工具，参数为 `{"keyword": "消费"}`。

```
查看基金 000001 的持仓情况
```

Claude Code 会调用 `get_fund_holdings` 工具，参数为 `{"code": "000001"}`。

#### 返回格式

所有工具返回 JSON 格式数据，包含：

- **基金组合**: 完整的资产配置方案、基金列表、业绩数据
- **基金信息**: 代码、名称、类型、收益率、规模、费率等
- **错误信息**: 如果调用失败，返回错误详情

---

## 对比两种模式

| 特性 | 独立脚本模式 | MCP 服务器模式 |
|-----|------------|--------------|
| 使用场景 | 终端直接运行，查看完整报告 | Claude Code 集成，智能对话 |
| 输出格式 | 格式化文本表格 | JSON 结构化数据 |
| 交互方式 | 一次性输出全部 | 按需调用单个功能 |
| 扩展性 | 需要修改代码 | 通过工具调用灵活组合 |
| 原有逻辑 | 完全保留 | 复用原有函数 |

---

## 依赖关系

```
fund_advisor.py          # 原始脚本（核心逻辑）
    ↓
fund_advisor_mcp.py      # MCP 封装层
    ↓
MCP 客户端（Claude Code） # 调用方
```

**设计原则**: 
- `fund_advisor.py` 保持不变，可独立运行
- `fund_advisor_mcp.py` 作为适配层，导入并封装原有功能
- 两种模式互不干扰，各自独立

---

## 故障排查

### 问题 1: MCP 服务器启动失败

**解决方案**:
```bash
# 检查 Python 路径
which python3

# 检查依赖
pip list | grep mcp

# 手动测试导入
python3 -c "from fund_advisor import v1_defensive; print('OK')"
```

### 问题 2: Claude Code 找不到工具

**解决方案**:
1. 检查 `mcp_config.json` 路径是否正确
2. 重启 Claude Code
3. 查看 Claude Code 日志: `~/.claude/logs/`

### 问题 3: 数据获取失败

**原因**: 网络问题或 API 限流

**解决方案**:
- 检查网络连接
- 等待几秒后重试
- 查看 `api_calls_*.json` 日志

---

## 更新日志

### v1.0.0 (2026-06-23)
- ✅ 新增 MCP 服务器模式
- ✅ 提供 11 个 MCP 工具
- ✅ 保留原有独立脚本模式
- ✅ 零依赖外部文件，自包含设计

---

## 技术栈

- **核心逻辑**: Python 3.12+, requests
- **MCP 框架**: mcp>=1.0.0
- **数据源**: 东方财富、天天基金 API

---

## 许可证

本项目仅供学习研究使用，不构成投资建议。
