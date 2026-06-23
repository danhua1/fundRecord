# fundRecord — 基金投顾研究系统

基于东方财富 & 天天基金公开 API，结合 A 股全栈数据工具包，构建「板块→基金」体系化投资研究工具。

## 项目目标

- 用数据驱动的方式判断当前应该投资哪个行业板块
- 按板块筛选优质基金，给出多版本组合推荐
- 提供实时行业轮动信号，辅助调仓决策

## 项目结构

```
fundRecord/
├── fund_advisor.py                 # 核心脚本：基金推荐引擎（独立运行）
├── fund_advisor_mcp.py             # MCP 服务器封装（支持 MCP 客户端调用）🆕
├── test_mcp.py                     # MCP 功能测试脚本 🆕
├── mcp_config.json                 # MCP 配置文件示例 🆕
├── MCP_USAGE.md                    # MCP 使用详细说明 🆕
├── .claude/skills/a-stock-data/    # A股数据工具包（行情/研报/龙虎榜/资金流）
└── README.md                       # 本文件
```

## 核心能力

### fund_advisor.py — 五维基金组合推荐

| 版本 | 风格 | 配置逻辑 | 适合人群 | 特色功能 |
|------|------|----------|----------|----------|
| V1 稳健版 | 债券为主 | 长债+中短债+偏债混合+货币 | 保守型 | - |
| V2 均衡版 | 股债平衡 | 宽基指数+偏股混合+纯债 | 稳健增长型 | - |
| V3 成长版 | 权益为主 | 行业ETF+主动权益精选 | 进取型 | ⭐ 含板块头部主动基金 |
| V4 行业轮动版 | 动态捕捉 | 实时行业排名→动量最强板块ETF | 交易型 | ⭐ 含强势行业头部主动基金 |
| V5 指数版 | 被动投资 | 核心宽基+行业卫星配置 | 长期定投型 | - |

**✨ V2.0 新特性**：
- V3/V4 版本新增"💎 各板块头部主动管理基金"板块
- 为每个推荐板块提供 3-5 只头部主动管理基金
- 通过名称关键词匹配 + 多维度评分自动筛选
- 提供 ETF + 主动基金双维度选择

### a-stock-data skill — A 股全栈数据

七层数据覆盖：行情(mootdx+腾讯+百度)、研报(东财+同花顺)、信号(热点+北向+龙虎榜)、资金面(融资融券+大宗交易)、新闻、基础数据、公告

## 数据来源

- **东方财富** — 基金列表、排名、净值历史、重仓持仓、实时估值
- **天天基金** — 基金持仓明细、基金详情
- **mootdx（通达信）** — K 线、盘口、F10 财务
- **腾讯财经** — PE/PB/市值/ETF 行情
- **同花顺** — 热点题材归因、北向资金

## 快速开始

### 模式 1: 独立脚本执行（传统模式）

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行基金推荐引擎
python3 fund_advisor.py
```

### 模式 2: MCP 服务器模式（新增 🆕）

**适用场景**: 与 Claude Code 等 MCP 客户端集成，智能对话式查询

```bash
# 安装 MCP 依赖
pip install mcp

# 测试 MCP 功能
python3 test_mcp.py

# 启动 MCP 服务器
python3 fund_advisor_mcp.py --mcp
```

**MCP 工具列表** (11个):
- `get_portfolio_v1_defensive` - 获取V1稳健版组合
- `get_portfolio_v2_balanced` - 获取V2均衡版组合
- `get_portfolio_v3_growth` - 获取V3成长版组合
- `get_portfolio_v4_rotation` - 获取V4行业轮动版组合
- `get_portfolio_v5_index` - 获取V5指数版组合
- `get_all_portfolios` - 一次性获取全部5个版本
- `search_fund` - 搜索基金（代码/名称）
- `get_fund_holdings` - 查询基金持仓
- `get_fund_ranking` - 获取基金排名列表
- `find_sector_etf` - 查找板块ETF
- `get_sector_top_funds` - 获取板块头部主动基金

详细说明请查看 [MCP_USAGE.md](./MCP_USAGE.md)

## 免责声明

本项目仅供学习研究使用，所有数据来自公开 API，不构成任何投资建议。投资有风险，入市需谨慎。
